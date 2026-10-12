from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
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

# Static files and Web Frontend mounting
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
FRONTEND_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/", tags=["Root"])
async def root(request: Request):
    accept = request.headers.get("accept", "")
    index_file = FRONTEND_DIR / "index.html"
    if "text/html" in accept and index_file.exists():
        return FileResponse(index_file)
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
        "api_v1": settings.API_V1_PREFIX,
        "ui": "/ui",
    }


@app.get("/ui", tags=["Root"], include_in_schema=False)
async def serve_ui():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse(status_code=404, content={"message": "Frontend UI file not found"})


@app.get("/style.css", include_in_schema=False)
async def serve_root_css():
    css_file = FRONTEND_DIR / "style.css"
    if css_file.exists():
        return FileResponse(css_file, media_type="text/css")
    return JSONResponse(status_code=404, content={"message": "CSS not found"})


@app.get("/app.js", include_in_schema=False)
async def serve_root_js():
    js_file = FRONTEND_DIR / "app.js"
    if js_file.exists():
        return FileResponse(js_file, media_type="application/javascript")
    return JSONResponse(status_code=404, content={"message": "JS not found"})

# Reload trigger



