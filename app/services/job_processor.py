from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.models import (
    GenerationJob,
    Certificate,
    JobStatus,
    CertificateStatus,
    get_utc_now,
)
from app.services.certificate_generator import generate_certificate_pdf, CertificateGenerationError
from app.core.logger import logger


def process_bulk_job(job_id: str) -> None:
    """
    Background worker task to process all certificates for a GenerationJob.
    Executes in FastAPI BackgroundTasks with complete per-item fault isolation.
    """
    # 1. Create a dedicated database session for this background execution
    db: Session = SessionLocal()

    try:
        logger.info("Starting background processing for Job ID: %s", job_id)

        # 2. Fetch the job record
        job: Optional[GenerationJob] = (
            db.query(GenerationJob)
            .filter(GenerationJob.id == job_id)
            .first()
        )

        if not job:
            logger.error("Background job processor could not find Job ID: %s", job_id)
            return

        # 3. Transition job status to PROCESSING
        job.status = JobStatus.PROCESSING
        db.commit()

        # 4. Fetch all queued certificates for this job
        certificates = (
            db.query(Certificate)
            .filter(Certificate.job_id == job_id)
            .order_by(Certificate.created_at)
            .all()
        )

        # Reset counters to reflect actual processed counts
        successful_count = 0
        failed_count = 0

        # 5. Process each certificate independently with fault isolation
        for cert in certificates:
            try:
                cert.status = CertificateStatus.PROCESSING
                db.commit()

                logger.debug(
                    "Generating certificate [%s] for recipient: %s (%s)",
                    cert.id,
                    cert.recipient_name,
                    cert.recipient_email,
                )

                # Generate the physical PDF file
                file_path = generate_certificate_pdf(
                    certificate_id=cert.id,
                    recipient_name=cert.recipient_name,
                    event_name=job.event_name,
                    certificate_title=job.certificate_title,
                    job_id=job.id,
                )

                # Mark certificate as COMPLETED
                cert.file_path = file_path
                cert.status = CertificateStatus.COMPLETED
                cert.error_message = None
                successful_count += 1
                logger.info("Certificate [%s] generated successfully", cert.id)

            except Exception as cert_exc:
                # ISOLATION: Error in single certificate does NOT stop remaining batch
                logger.error(
                    "Certificate [%s] failed for recipient '%s': %s",
                    cert.id,
                    cert.recipient_name,
                    cert_exc,
                    exc_info=True,
                )
                cert.status = CertificateStatus.FAILED
                cert.error_message = str(cert_exc)
                failed_count += 1

            finally:
                # Update parent job counters dynamically after each item
                job.successful = successful_count
                job.failed = failed_count
                db.commit()

        # 6. Finalize Job Status & Completion Timestamp
        job.completed_at = get_utc_now()

        if failed_count == 0:
            job.status = JobStatus.COMPLETED
        elif successful_count > 0 and failed_count > 0:
            job.status = JobStatus.COMPLETED_WITH_ERRORS
        else:
            job.status = JobStatus.FAILED

        db.commit()
        logger.info(
            "Finished Job ID: %s | Final Status: %s | Success: %d | Failed: %d | Total: %d",
            job.id,
            job.status,
            job.successful,
            job.failed,
            job.total,
        )

    except Exception as job_exc:
        # Catch unexpected job-level crash (e.g., database connection dropped)
        logger.critical(
            "Fatal unexpected error in background processor for Job ID %s: %s",
            job_id,
            job_exc,
            exc_info=True,
        )
        try:
            if "job" in locals() and job:
                job.status = JobStatus.FAILED
                job.completed_at = get_utc_now()
                db.commit()
        except Exception:
            db.rollback()

    finally:
        # Guarantee session closure to prevent connection leaks
        db.close()
