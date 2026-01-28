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

    # CORS - Allow all origins by default for simplicity
    # In production, Railway can override via CORS_ORIGINS_STR env variable
    cors_origins_str: str = "*"

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from string."""
        # Allow all origins - simplest solution to avoid CORS issues
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


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
