from fastapi import APIRouter
from app.api.v1.endpoints import health, jobs, certificates

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(jobs.router, tags=["Jobs"])
api_router.include_router(certificates.router, tags=["Certificates"])
