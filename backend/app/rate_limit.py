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

    # Use Redis if available (already configured for task queue)
    if settings.redis_url and settings.environment != "development":
        storage_uri = settings.redis_url

    return Limiter(
        key_func=get_remote_address,
        default_limits=[settings.rate_limit_default],
        storage_uri=storage_uri,
        enabled=settings.rate_limit_enabled,
    )


limiter = _get_limiter()
