from fastapi import APIRouter
from app.core.config import settings
from datetime import datetime, timezone

router = APIRouter()


@router.get("/health", summary="Service Health Check")
async def health_check():
    """Returns the operational status and metadata of the application."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }
