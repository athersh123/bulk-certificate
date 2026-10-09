from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logger import logger
from app.api.v1.api import api_router
from app.db.database import engine, Base
import app.models  # Ensure models are imported for metadata registration


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    logger.info("Starting up %s...", settings.APP_NAME)
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    # Initialize database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
    yield
    # Shutdown tasks
    logger.info("Shutting down %s...", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    description="High-performance asynchronous bulk certificate generation and alerting system.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================================
# Global Exception Handlers (Security, Sanitization & Structured Errors)
# =========================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Transforms Pydantic validation errors into clean, client-friendly error structures.
    """
    errors = []
    for err in exc.errors():
        field_path = " -> ".join(str(loc) for loc in err.get("loc", []) if loc != "body")
        errors.append({
            "field": field_path or "body",
            "message": err.get("msg", "Invalid input value"),
            "type": err.get("type", "value_error"),
        })

    logger.warning(
        "Validation error on %s %s: %d issues found",
        request.method,
        request.url.path,
        len(errors),
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status_code": 422,
            "error_type": "ValidationError",
            "message": "Input validation failed. Please check the provided payload.",
            "errors": errors,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Ensures standard structure across all explicitly raised HTTP exceptions.
    """
    logger.info(
        "HTTP %d error on %s %s: %s",
        exc.status_code,
        request.method,
        request.url.path,
        exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "error_type": "HTTPException",
            "detail": exc.detail,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Catches all unexpected internal errors.
    Logs full stack trace to internal logs, but shields internal details from client.
    """
    logger.critical(
        "Unhandled 500 Internal Server Error on %s %s: %s",
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status_code": 500,
            "error_type": "InternalServerError",
            "message": "An unexpected server error occurred. Our team has been notified.",
        },
    )


# Mount API routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(api_router)  # Direct /jobs, /certificates and /health endpoints


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
        "api_v1": settings.API_V1_PREFIX,
    }
