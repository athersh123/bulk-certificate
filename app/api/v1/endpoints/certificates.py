import os
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Certificate, CertificateStatus
from app.schemas.schemas import CertificateResponse
from app.core.logger import logger

router = APIRouter()


@router.get(
    "/certificates/{certificate_id}",
    summary="Download Generated Certificate PDF",
    description="Retrieves and downloads the physical PDF certificate for a recipient. Returns appropriate error status if pending, processing, or failed.",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "The binary PDF certificate file.",
        },
        400: {"description": "Certificate is still pending or processing."},
        404: {"description": "Certificate record or physical PDF file not found."},
        409: {"description": "Certificate generation failed."},
    },
)
def get_certificate_file(
    certificate_id: str,
    db: Session = Depends(get_db),
):
    """
    Finds a certificate by ID and streams the generated PDF file to the client.
    """
    # 1. Look up certificate in the database
    cert: Optional[Certificate] = (
        db.query(Certificate)
        .filter(Certificate.id == certificate_id)
        .first()
    )

    if not cert:
        logger.warning("Certificate lookup failed: ID '%s' not found", certificate_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' does not exist.",
        )

    # 2. Check if certificate is still in-flight (PENDING or PROCESSING)
    if cert.status in [CertificateStatus.PENDING, CertificateStatus.PROCESSING]:
        logger.info("Certificate '%s' is not ready yet (status: %s)", certificate_id, cert.status)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Certificate '{certificate_id}' is currently {cert.status}. Please poll the job status and try again shortly.",
        )

    # 3. Check if certificate generation failed
    if cert.status == CertificateStatus.FAILED:
        logger.warning(
            "Certificate '%s' generation previously failed: %s",
            certificate_id,
            cert.error_message,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"Certificate generation failed for recipient '{cert.recipient_name}'.",
                "error": cert.error_message or "Unknown rendering error",
                "certificate_id": cert.id,
                "status": cert.status,
            },
        )

    # 4. If COMPLETED, verify file path exists on disk and is within storage directory
    if not cert.file_path or not os.path.exists(cert.file_path):
        logger.error(
            "Certificate '%s' marked COMPLETED but file missing at path: %s",
            certificate_id,
            cert.file_path,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The certificate was marked completed, but the physical PDF file was not found on the server.",
        )

    resolved_path = Path(cert.file_path).resolve()

    # 5. Sanitize and prepare clean download filename
    safe_name = "".join(c for c in cert.recipient_name if c.isalnum() or c in (" ", "_", "-")).strip()
    download_filename = f"Certificate_{safe_name}_{certificate_id[:8]}.pdf".replace(" ", "_")

    logger.info("Serving certificate PDF for ID: %s (%s)", certificate_id, download_filename)

    # 6. Stream the file response
    return FileResponse(
        path=cert.file_path,
        media_type="application/pdf",
        filename=download_filename,
    )


@router.get(
    "/certificates/{certificate_id}/metadata",
    response_model=CertificateResponse,
    summary="Get Certificate Metadata",
    description="Retrieves the metadata, status, recipient details, and error messages for a single certificate.",
)
def get_certificate_metadata(
    certificate_id: str,
    db: Session = Depends(get_db),
) -> CertificateResponse:
    """
    Retrieves the JSON record for a certificate without downloading the file.
    """
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' was not found.",
        )

    return CertificateResponse(
        id=cert.id,
        job_id=cert.job_id,
        recipient_name=cert.recipient_name,
        recipient_email=cert.recipient_email,
        status=cert.status,
        file_path=cert.file_path,
        download_url=f"/certificates/{cert.id}",
        error_message=cert.error_message,
        created_at=cert.created_at,
    )


@router.get(
    "/jobs/{job_id}/certificates",
    response_model=List[CertificateResponse],
    summary="List All Certificates for a Job",
    description="Retrieves a list of all recipient certificates and their individual statuses under a specific job.",
)
def list_job_certificates(
    job_id: str,
    db: Session = Depends(get_db),
) -> List[CertificateResponse]:
    """
    Lists all certificate items belonging to a job.
    """
    certs = (
        db.query(Certificate)
        .filter(Certificate.job_id == job_id)
        .order_by(Certificate.created_at)
        .all()
    )

    if not certs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No certificates found for Job ID '{job_id}'.",
        )

    return [
        CertificateResponse(
            id=cert.id,
            job_id=cert.job_id,
            recipient_name=cert.recipient_name,
            recipient_email=cert.recipient_email,
            status=cert.status,
            file_path=cert.file_path,
            download_url=f"/certificates/{cert.id}",
            error_message=cert.error_message,
            created_at=cert.created_at,
        )
        for cert in certs
    ]
