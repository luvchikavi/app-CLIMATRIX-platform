"""
CLIMATRIX - GHG Emissions Accounting Platform

FastAPI application entry point.
"""
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sentry_sdk

from app.config import settings
from app.database import init_db, close_db
from app.api import auth, activities, periods, reports, reference, organization, import_data, admin, cbam, emission_factors, billing, audit, decarbonization

# Initialize Sentry for error tracking (only if DSN is configured)
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=f"climatrix@{settings.app_version}",
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        profiles_sample_rate=0.1,  # 10% for profiling
        send_default_pii=False,  # Don't send personally identifiable information
    )


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

# CORS Middleware - Permissive configuration to avoid CORS issues
# Allow ALL origins to prevent recurring CORS problems
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_origin_regex=r"https?://.*",  # Backup: match any URL
    allow_credentials=False,  # Must be False when using "*" origins
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
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

    # Capture exception in Sentry
    if settings.sentry_dsn:
        sentry_sdk.capture_exception(exc)

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
app.include_router(cbam.router, prefix="/api/cbam", tags=["CBAM"])
app.include_router(emission_factors.router, prefix="/api", tags=["Emission Factors"])
app.include_router(billing.router, prefix="/api", tags=["Billing"])
app.include_router(audit.router, prefix="/api", tags=["Audit"])
app.include_router(decarbonization.router, prefix="/api", tags=["Decarbonization Pathways"])


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
