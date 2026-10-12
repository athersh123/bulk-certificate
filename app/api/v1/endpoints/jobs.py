from typing import List
from fastapi import APIRouter, Depends, BackgroundTasks, status, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import GenerationJob, Certificate, JobStatus, CertificateStatus
from app.schemas.schemas import (
    CertificateGenerationRequest,
    JobCreationResponse,
    JobStatusResponse,
)
from app.services.job_processor import process_bulk_job
from app.core.logger import logger

router = APIRouter()


@router.get(
    "/jobs",
    response_model=List[JobStatusResponse],
    summary="List Recent Bulk Generation Jobs",
    description="Retrieves a list of recent bulk certificate generation jobs with real-time status and progress.",
)
def list_jobs(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> List[JobStatusResponse]:
    """
    Returns recent jobs ordered by creation date descending for dashboard tracking.
    """
    jobs = (
        db.query(GenerationJob)
        .order_by(GenerationJob.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    result = []
    for job in jobs:
        processed = job.successful + job.failed
        pending = max(0, job.total - processed)
        if job.total > 0:
            raw_progress = (processed / job.total) * 100.0
            progress = round(min(100.0, max(0.0, raw_progress)), 2)
        else:
            progress = 0.0

        result.append(
            JobStatusResponse(
                job_id=job.id,
                event_name=job.event_name,
                certificate_title=job.certificate_title,
                status=job.status,
                total=job.total,
                successful=job.successful,
                failed=job.failed,
                pending=pending,
                progress=progress,
                created_at=job.created_at,
                completed_at=job.completed_at,
            )
        )
    return result


@router.post(
    "/jobs",
    response_model=JobCreationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create & Enqueue Bulk Certificate Generation Job",
    description="Validates recipient batch data, creates database records in PENDING status, and dispatches background PDF processing.",
)
def create_generation_job(
    payload: CertificateGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> JobCreationResponse:
    """
    Creates a new GenerationJob and dispatches background worker without blocking HTTP response.
    """
    try:
        total_recipients = len(payload.recipients)
        logger.info(
            "Received GenerationJob request for event '%s' with %d recipients",
            payload.event_name,
            total_recipients,
        )

        # 1. Create the parent GenerationJob record
        job = GenerationJob(
            event_name=payload.event_name,
            certificate_title=payload.certificate_title,
            status=JobStatus.PENDING,
            total=total_recipients,
            successful=0,
            failed=0,
        )
        db.add(job)
        db.flush()  # Populates job.id before creating child certificates

        # 2. Create child Certificate records for every recipient
        certificates = [
            Certificate(
                job_id=job.id,
                recipient_name=recipient.name,
                recipient_email=recipient.email,
                status=CertificateStatus.PENDING,
            )
            for recipient in payload.recipients
        ]
        db.add_all(certificates)

        # 3. Atomically commit the transaction to DB
        db.commit()
        db.refresh(job)

        logger.info("Persisted GenerationJob ID: %s. Enqueuing background worker task...", job.id)

        # 4. Schedule background bulk processor task
        background_tasks.add_task(process_bulk_job, job.id)

        # 5. Immediately return 202 Accepted response
        return JobCreationResponse(
            job_id=job.id,
            event_name=job.event_name,
            certificate_title=job.certificate_title,
            status=job.status,
            total=job.total,
            message="Certificate generation job accepted and background processing started.",
            status_url=f"/api/v1/jobs/{job.id}",
            created_at=job.created_at,
        )

    except Exception as exc:
        db.rollback()
        logger.error("Failed to create generation job: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the generation job: {str(exc)}",
        )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get Bulk Job Status & Progress",
    description="Retrieves the current lifecycle status, progress percentage, and success/failure counters of a bulk job.",
)
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
) -> JobStatusResponse:
    """
    Returns the real-time progress and summary counters for a given Job ID.
    """
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        logger.warning("Job status query failed: Job ID '%s' not found", job_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation job with ID '{job_id}' was not found.",
        )

    # Calculate safe progress metrics
    processed = job.successful + job.failed
    pending = max(0, job.total - processed)

    # Safe division: guarantee no ZeroDivisionError and clamp between 0.0% and 100.0%
    if job.total > 0:
        raw_progress = (processed / job.total) * 100.0
        progress = round(min(100.0, max(0.0, raw_progress)), 2)
    else:
        progress = 0.0

    return JobStatusResponse(
        job_id=job.id,
        event_name=job.event_name,
        certificate_title=job.certificate_title,
        status=job.status,
        total=job.total,
        successful=job.successful,
        failed=job.failed,
        pending=pending,
        progress=progress,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )
