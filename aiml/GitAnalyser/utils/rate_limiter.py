"""
Rate limiting middleware for FastAPI.
Prevents API abuse and ensures fair resource allocation.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
import os


# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{os.getenv('RATE_LIMIT_PER_MINUTE', '10')}/minute"]
)


def get_limiter():
    """Get the rate limiter instance."""
    return limiter
