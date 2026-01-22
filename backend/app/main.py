"""
CLIMATRIX - GHG Emissions Accounting Platform

FastAPI application entry point.
"""
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db, close_db
from app.api import auth, activities, periods, reports, reference, organization, import_data, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="GHG Emissions Accounting Platform - Scope 1, 2, and 3",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler to ensure proper error responses with CORS
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch all unhandled exceptions and return a proper JSON response.
    This ensures CORS headers are properly set even on server errors.
    """
    error_detail = str(exc)
    tb = traceback.format_exc()
    print(f"[ERROR] Unhandled exception: {error_detail}")
    print(f"[ERROR] Traceback: {tb}")

    return JSONResponse(
        status_code=500,
        content={
            "detail": error_detail,
            "type": type(exc).__name__,
        },
    )


# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(periods.router, prefix="/api/periods", tags=["Reporting Periods"])
app.include_router(activities.router, prefix="/api", tags=["Activities"])
app.include_router(reports.router, prefix="/api", tags=["Reports"])
app.include_router(reference.router, prefix="/api/reference", tags=["Reference Data"])
app.include_router(organization.router, prefix="/api", tags=["Organization"])
app.include_router(import_data.router, prefix="/api", tags=["Import"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "healthy",
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
    }
