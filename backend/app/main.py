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

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from sqlalchemy import text

from app.config import settings
from app.database import init_db, close_db, engine
from app.rate_limit import limiter
from app.api import (
    auth,
    activities,
    periods,
    reports,
    reference,
    organization,
    import_data,
    admin,
    cbam,
    emission_factors,
    billing,
    audit,
    decarbonization,
)

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

# CORS Middleware - Uses CORS_ORIGINS_STR from environment
# In production: set to specific domains (e.g., "https://climatrix.io,https://app.climatrix.io")
# In development: defaults to "*" for convenience
_origins = settings.cors_origins
_use_wildcard = _origins == ["*"]

_cors_kwargs: dict = dict(
    allow_methods=["*"],
    allow_headers=["*"],
)

if _use_wildcard:
    _cors_kwargs["allow_origins"] = ["*"]
    _cors_kwargs["allow_credentials"] = False
else:
    _cors_kwargs["allow_origins"] = _origins
    _cors_kwargs["allow_credentials"] = True
    # Allow Vercel preview deploys (*.vercel.app)
    if settings.cors_allow_vercel_previews:
        _cors_kwargs["allow_origin_regex"] = r"https://.*\.vercel\.app"

app.add_middleware(CORSMiddleware, **_cors_kwargs)

# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


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
app.include_router(
    decarbonization.router, prefix="/api", tags=["Decarbonization Pathways"]
)


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
    """Readiness probe: verifies the database is reachable.

    Returns 503 (not 200) when the DB check fails so a load balancer / Railway
    takes an unhealthy instance out of rotation instead of routing traffic to it.
    """
    db_ok = True
    db_error: str | None = None
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - report any DB failure as not-ready
        db_ok = False
        db_error = str(exc)

    body = {
        "status": "healthy" if db_ok else "unhealthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "checks": {"database": "ok" if db_ok else f"error: {db_error}"},
    }
    return JSONResponse(status_code=200 if db_ok else 503, content=body)
