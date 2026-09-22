"""
RECRUIT.AI — Rate Limiting

A fixed-window limiter used as a FastAPI dependency on the endpoints worth
protecting: sign-in (brute force), password reset (mail spam to a known
address), registration and public application submission.

Scope, stated plainly: counters live in this process's memory. They are not
shared between workers and they reset on restart, so with N workers the
effective limit is roughly N times the configured one. That is a real
weakening, but it still turns an unbounded credential-stuffing loop into a
throttled one, and it needs no new infrastructure. REDIS_URL is already
configured and unused — moving these counters there is the obvious next step
and would make the limit exact and shared.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

from app.config import get_settings

settings = get_settings()

# key -> (window_started_at, count)
_buckets: dict[str, tuple[float, int]] = defaultdict(lambda: (0.0, 0))
_lock = threading.Lock()


def client_identifier(request: Request) -> str:
    """
    Best-effort caller identity for limiting.

    X-Forwarded-For is only honoured when TRUST_PROXY_HEADERS is on. The header
    is trivially forged, so trusting it unconditionally would let a caller
    bypass every limit by varying it; ignoring it behind a real proxy would
    instead lump all users under the proxy's own address. Which is correct
    depends on the deployment, so it is a setting rather than a guess.
    """
    if settings.TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # Left-most entry is the original client.
            return forwarded.split(",")[0].strip()

    return request.client.host if request.client else "unknown"


def _check(key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
    """Return (allowed, seconds_until_reset)."""
    now = time.monotonic()
    with _lock:
        started, count = _buckets[key]

        if now - started >= window_seconds:
            _buckets[key] = (now, 1)
            return True, window_seconds

        if count >= limit:
            return False, int(window_seconds - (now - started)) + 1

        _buckets[key] = (started, count + 1)
        return True, int(window_seconds - (now - started)) + 1


def reset() -> None:
    """Clear all counters. Used by tests."""
    with _lock:
        _buckets.clear()


class RateLimit:
    """
    FastAPI dependency factory.

        @router.post("/login", dependencies=[Depends(RateLimit("login", 10, 300))])
    """

    def __init__(self, name: str, limit: int, window_seconds: int):
        self.name = name
        self.limit = limit
        self.window_seconds = window_seconds

    def __call__(self, request: Request) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return

        key = f"{self.name}:{client_identifier(request)}"
        allowed, retry_after = _check(key, self.limit, self.window_seconds)

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please wait and try again.",
                headers={"Retry-After": str(retry_after)},
            )
