import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    Enum as SQLEnum,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


def get_utc_now() -> datetime:
    """Helper to return current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    """Helper to generate a random UUID string."""
    return str(uuid.uuid4())


# ==========================================
# 1. Status Enums
# ==========================================

class JobStatus(str, enum.Enum):
    """Lifecycle statuses for a bulk generation job."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    PARTIALLY_COMPLETED = "COMPLETED_WITH_ERRORS"
    FAILED = "FAILED"


class CertificateStatus(str, enum.Enum):
    """Lifecycle statuses for an individual certificate."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ==========================================
# 2. Database Models
# ==========================================

class GenerationJob(Base):
    """
    Represents a bulk certificate generation batch job.
    Tracks overall progress, totals, and completion metrics.
    """
    __tablename__ = "generation_jobs"

    id = Column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        index=True,
        doc="Unique identifier for the job (UUID string)",
    )
    event_name = Column(
        String(255),
        nullable=False,
        default="Certificate Event",
        doc="Name of the course, training, or event",
    )
    certificate_title = Column(
        String(255),
        nullable=False,
        default="Certificate of Completion",
        doc="Certificate title text displayed on the PDF",
    )
    status = Column(
        SQLEnum(JobStatus),
        default=JobStatus.PENDING,
        nullable=False,
        index=True,
        doc="Current overall execution status of the job",
    )
    total = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Total number of certificates to generate in this batch",
    )
    successful = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of certificates generated successfully",
    )
    failed = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of certificates that failed generation",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=get_utc_now,
        nullable=False,
        doc="Timestamp when the job was submitted",
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when the job finished processing (success or partial/failure)",
    )

    # Relationship: 1 GenerationJob -> Many Certificates
    certificates = relationship(
        "Certificate",
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Certificate.created_at",
    )

    __table_args__ = (
        CheckConstraint("total >= 0", name="chk_generation_jobs_total_non_negative"),
        CheckConstraint("successful >= 0", name="chk_generation_jobs_successful_non_negative"),
        CheckConstraint("failed >= 0", name="chk_generation_jobs_failed_non_negative"),
        Index("ix_generation_jobs_status_created_at", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<GenerationJob(id='{self.id}', status='{self.status}', "
            f"total={self.total}, successful={self.successful}, failed={self.failed})>"
        )


class Certificate(Base):
    """
    Represents an individual certificate item generated as part of a GenerationJob.
    Maintains independent success/failure status and isolated error message.
    """
    __tablename__ = "certificates"

    id = Column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        index=True,
        doc="Unique identifier for the certificate (UUID string)",
    )
    job_id = Column(
        String(36),
        ForeignKey("generation_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key reference to the parent GenerationJob",
    )
    recipient_name = Column(
        String(255),
        nullable=False,
        doc="Full name of the certificate recipient",
    )
    recipient_email = Column(
        String(255),
        nullable=False,
        index=True,
        doc="Email address of the certificate recipient",
    )
    status = Column(
        SQLEnum(CertificateStatus),
        default=CertificateStatus.PENDING,
        nullable=False,
        index=True,
        doc="Status of this individual certificate generation",
    )
    file_path = Column(
        String(500),
        nullable=True,
        doc="Relative or absolute file path to the generated PDF",
    )
    error_message = Column(
        Text,
        nullable=True,
        doc="Error traceback or failure explanation if status is FAILED",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=get_utc_now,
        nullable=False,
        doc="Timestamp when the certificate record was created",
    )

    # Relationship: Many Certificates -> 1 GenerationJob
    job = relationship(
        "GenerationJob",
        back_populates="certificates",
    )

    __table_args__ = (
        Index("ix_certificates_job_id_status", "job_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Certificate(id='{self.id}', job_id='{self.job_id}', "
            f"recipient_name='{self.recipient_name}', status='{self.status}')>"
        )
