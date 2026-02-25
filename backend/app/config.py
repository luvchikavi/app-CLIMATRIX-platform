"""
Application configuration using Pydantic Settings.
All configuration is loaded from environment variables.
"""
import json
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    # e.g. "https://climatrix.io,https://app.climatrix.io"
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
        if self.cors_origins_str.strip().startswith('['):
            try:
                return json.loads(self.cors_origins_str)
            except json.JSONDecodeError:
                pass
        # Fall back to comma-separated
        return [origin.strip() for origin in self.cors_origins_str.split(',') if origin.strip()]

    # Reference Data
    default_emission_factor_year: int = 2024
    default_region: str = "Global"

    # Feature Flags
    enable_wtt_auto_calculation: bool = True
    enable_market_based_scope2: bool = True

    # Claude AI (Anthropic)
    anthropic_api_key: str = ""  # Set ANTHROPIC_API_KEY in .env
    claude_model: str = "claude-sonnet-4-20250514"  # Default model for AI extraction
    ai_extraction_enabled: bool = True  # Enable/disable AI-powered features

    # Monitoring & Error Tracking
    sentry_dsn: str = ""  # Set SENTRY_DSN in environment for error tracking

    # Email Configuration (for transactional emails)
    smtp_host: str = ""  # e.g., smtp.sendgrid.net, smtp.gmail.com
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@climatrix.io"
    smtp_from_name: str = "CLIMATRIX"
    smtp_use_tls: bool = True

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

    # Stripe Billing
    stripe_secret_key: str = ""  # Set STRIPE_SECRET_KEY in environment
    stripe_publishable_key: str = ""  # Set STRIPE_PUBLISHABLE_KEY
    stripe_webhook_secret: str = ""  # Set STRIPE_WEBHOOK_SECRET for webhook validation
    stripe_price_id_starter: str = ""  # Stripe Price ID for Starter plan
    stripe_price_id_professional: str = ""  # Stripe Price ID for Professional plan
    stripe_price_id_enterprise: str = ""  # Stripe Price ID for Enterprise plan


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
