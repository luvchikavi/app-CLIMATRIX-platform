"""
Application configuration using Pydantic Settings.
All configuration is loaded from environment variables.
"""

import json
import warnings
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_SECRET_KEY = "CHANGE-THIS-IN-PRODUCTION-use-openssl-rand-hex-32"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "CLIMATRIX"
    app_version: str = "3.1.0"
    debug: bool = False
    environment: str = "development"  # development, staging, production

    # Database
    # For local dev: sqlite+aiosqlite:///./climatrix.db
    # For production: postgresql+asyncpg://...
    # Railway provides DATABASE_URL as postgresql://, we convert to asyncpg
    database_url: str = "sqlite+aiosqlite:///./climatrix.db"
    database_echo: bool = False  # Log SQL queries

    @property
    def async_database_url(self) -> str:
        """Convert DATABASE_URL to async format for SQLAlchemy."""
        url = self.database_url
        # Convert Railway's postgresql:// to postgresql+asyncpg://
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    # Redis (for task queue)
    redis_url: str = "redis://localhost:6379"

    # JWT Authentication
    secret_key: str = "CHANGE-THIS-IN-PRODUCTION-use-openssl-rand-hex-32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS - In production set to specific domains via CORS_ORIGINS_STR
    # e.g. "https://climatrix.co,https://app.climatrix.co"
    cors_origins_str: str = "*"
    cors_allow_vercel_previews: bool = True  # Allow *.vercel.app preview deploys

    # Google OAuth
    google_client_id: str = ""  # Set GOOGLE_CLIENT_ID in environment

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from string."""
        if self.cors_origins_str == "*":
            return ["*"]
        if not self.cors_origins_str:
            return ["*"]
        # Try JSON array first
        if self.cors_origins_str.strip().startswith("["):
            try:
                return json.loads(self.cors_origins_str)
            except json.JSONDecodeError:
                pass
        # Fall back to comma-separated
        return [
            origin.strip()
            for origin in self.cors_origins_str.split(",")
            if origin.strip()
        ]

    # Reference Data
    default_emission_factor_year: int = 2024
    default_region: str = "Global"

    # Feature Flags
    enable_wtt_auto_calculation: bool = True
    enable_market_based_scope2: bool = True

    # Claude AI (Anthropic)
    anthropic_api_key: str = ""  # Set ANTHROPIC_API_KEY in .env
    # Ingestion parser models (owner-approved): Opus for mapping/clarifying
    # questions, Haiku for cheap bulk classification/dedupe. Sonnet = cost-cap fallback.
    claude_model: str = "claude-opus-4-8"  # mapping + clarifying questions
    claude_model_fast: str = "claude-haiku-4-5"  # bulk per-cell classification/dedupe
    claude_model_fallback: str = "claude-sonnet-4-6"  # cost-cap fallback only
    ai_extraction_enabled: bool = True  # Enable/disable AI-powered features

    # Monitoring & Error Tracking
    sentry_dsn: str = ""  # Set SENTRY_DSN in environment for error tracking

    # Email Configuration (for transactional emails)
    smtp_host: str = ""  # e.g., smtp.sendgrid.net, smtp.gmail.com
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@climatrix.co"
    smtp_from_name: str = "CLIMATRIX"
    smtp_use_tls: bool = True

    # Founder inbox notified on every new signup ("" disables)
    signup_notification_email: str = "avi@climatrix.co"

    # Lead follow-up automation
    # Public scheduling link offered in the demo-request acknowledgment
    # ("" omits the button until the founder provides one)
    demo_booking_url: str = ""
    # Remind the founder about leads still uncontacted after this many hours
    # (0 disables the reminder loop entirely)
    lead_reminder_hours: int = 48
    # How often the background sweep looks for overdue leads
    lead_reminder_check_minutes: int = 360

    # Frontend URL (for email links)
    frontend_url: str = "http://localhost:3000"

    # Password Reset
    password_reset_token_expire_minutes: int = 30

    # File Storage (S3-compatible: AWS S3 or Cloudflare R2)
    storage_backend: str = "local"  # "local" or "s3"
    s3_bucket_name: str = ""
    s3_region: str = "auto"  # "auto" for R2
    s3_endpoint_url: str = ""  # e.g., https://<account_id>.r2.cloudflarestorage.com
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""

    # File Upload Limits
    max_upload_size_mb: int = 50  # Maximum file upload size in MB

    # Smart Import: dispatch parsing to the arq worker (async) vs. parse inline in
    # the request. Off by default — no worker is deployed and the parser is fast
    # (~15-20s), so inline is reliable. Flip to True only if a worker is running.
    ingest_use_worker: bool = False

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_login: str = "10/minute"
    rate_limit_register: str = "5/minute"
    rate_limit_password_reset: str = "5/minute"
    rate_limit_import: str = "20/minute"
    rate_limit_default: str = "60/minute"

    # Stripe Billing
    stripe_secret_key: str = ""  # Set STRIPE_SECRET_KEY in environment
    stripe_publishable_key: str = ""  # Set STRIPE_PUBLISHABLE_KEY
    stripe_webhook_secret: str = ""  # Set STRIPE_WEBHOOK_SECRET for webhook validation
    # Price IDs for the 2026-07-20 restructured catalog. Populate from the
    # create_stripe_products.py script output. Empty => that purchase path is
    # unavailable (checkout returns a clear 400/503).
    stripe_price_starter_monthly: str = ""  # Starter $99/mo (recurring)
    stripe_price_starter_annual: str = ""  # Starter $1,010/yr (recurring)
    stripe_price_professional_annual: str = ""  # Professional $3,560/yr (recurring)
    stripe_price_report_pass: str = ""  # Report Pass $1,790 (one-time)
    stripe_price_site_pack: str = ""  # Site pack +5 sites $490/yr (recurring)
    stripe_price_seat: str = ""  # Extra seat $190/yr (recurring)
    # Deprecated single-price fields (pre-restructure). Kept so old env vars
    # don't break boot; no longer used for checkout.
    stripe_price_id_starter: str = ""
    stripe_price_id_professional: str = ""
    stripe_price_id_enterprise: str = ""


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    s = Settings()
    # Fail-fast: refuse to start in production with the default secret key
    if s.secret_key == _DEFAULT_SECRET_KEY:
        if s.environment in ("production", "staging"):
            raise RuntimeError(
                "SECRET_KEY is still the default placeholder. "
                "Set a secure SECRET_KEY via environment variable before running in production. "
                "Generate one with: openssl rand -hex 32"
            )
        else:
            warnings.warn(
                "SECRET_KEY is the default placeholder. "
                "This is fine for development but MUST be changed for production.",
                stacklevel=2,
            )
    return s


settings = get_settings()
