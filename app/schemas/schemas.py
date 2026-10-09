from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.models.models import JobStatus, CertificateStatus


# ==========================================
# 1. Input Schemas (Requests)
# ==========================================

class Recipient(BaseModel):
    """Schema representing an individual certificate recipient."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Full recipient name displayed on certificate",
        examples=["Alice Smith"],
    )
    email: EmailStr = Field(
        ...,
        description="Valid recipient email address",
        examples=["alice.smith@example.com"],
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Recipient name cannot be empty or only whitespace")
        return stripped


class CertificateGenerationRequest(BaseModel):
    """Schema for submitting a bulk certificate generation batch job."""
    event_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Title of the event, workshop, or course",
        examples=["FastAPI Backend Mastery Bootcamp"],
    )
    certificate_title: str = Field(
        default="Certificate of Completion",
        min_length=1,
        max_length=255,
        description="Header title printed on the certificate",
        examples=["Certificate of Completion"],
    )
    recipients: List[Recipient] = Field(
        ...,
        min_length=1,
        description="List of recipients (must contain at least one recipient)",
    )

    @field_validator("event_name", "certificate_title")
    @classmethod
    def validate_strings_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or only whitespace")
        return stripped


# ==========================================
# 2. Output Schemas (Responses)
# ==========================================

class CertificateResponse(BaseModel):
    """Schema representing an individual certificate and its generation status."""
    id: str
    job_id: str
    recipient_name: str
    recipient_email: str
    status: CertificateStatus
    file_path: Optional[str] = None
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobCreationResponse(BaseModel):
    """Schema returned immediately upon submitting a bulk job."""
    job_id: str
    event_name: str
    certificate_title: str
    status: JobStatus
    total: int
    message: str
    status_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobStatusResponse(BaseModel):
    """Detailed schema tracking progress and statistics of a bulk job."""
    job_id: str
    event_name: str
    certificate_title: str
    status: JobStatus
    total: int
    successful: int
    failed: int
    pending: int = 0
    progress: float = 0.0
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
