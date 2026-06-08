"""
Rate limiting configuration using slowapi.

Provides per-endpoint rate limits to protect against brute force,
spam, and resource abuse. Uses in-memory storage by default,
Redis when available.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


def _get_limiter() -> Limiter:
    """Create limiter with appropriate storage backend."""
    storage_uri = None

    # Use Redis only in deployed environments (production/staging). Development
    # and test fall back to in-memory storage so they don't require a running
    # Redis — otherwise rate-limited endpoints raise ConnectionError in CI.
    if settings.redis_url and settings.environment in ("production", "staging"):
        storage_uri = settings.redis_url

    return Limiter(
        key_func=get_remote_address,
        default_limits=[settings.rate_limit_default],
        storage_uri=storage_uri,
        enabled=settings.rate_limit_enabled,
    )


limiter = _get_limiter()
