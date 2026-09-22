"""
RECRUIT.AI — Rate Limiting

A fixed-window limiter used as a FastAPI dependency on the endpoints worth
protecting: sign-in (brute force), password reset (mail spam to a known
address), registration and public application submission.

Two backends:

  - Redis when REDIS_URL is reachable, which makes the limit exact and shared
    across every worker and survives a restart
  - process memory otherwise, which is approximate (with N workers the
    effective limit is roughly N times configured) but needs no infrastructure

The backend is chosen once at startup. If Redis is configured but unreachable
the limiter falls back to memory rather than failing closed: a rate limiter
that cannot reach its store should degrade, not take sign-in down with it.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

from app.config import get_settings

settings = get_settings()

# key -> (window_started_at, count)
_buckets: dict[str, tuple[float, int]] = defaultdict(lambda: (0.0, 0))
_lock = threading.Lock()

# Lazily resolved Redis client; False means "checked and unavailable", so the
# probe runs once rather than on every request.
_redis_client = None


def _redis():
    """Return a working Redis client, or None."""
    global _redis_client

    if _redis_client is False:
        return None
    if _redis_client is not None:
        return _redis_client

    if not settings.REDIS_URL:
        _redis_client = False
        return None

    try:
        import redis  # imported lazily: optional dependency

        client = redis.Redis.from_url(
            settings.REDIS_URL, socket_connect_timeout=1, socket_timeout=1
        )
        client.ping()
        _redis_client = client
        logging.getLogger("recruit.ratelimit").info("rate limiting backed by Redis")
        return client
    except Exception as exc:
        # Degrade to memory rather than failing closed. A limiter that cannot
        # reach its store must not take authentication down with it.
        logging.getLogger("recruit.ratelimit").warning(
            "Redis unavailable, rate limiting falls back to process memory",
            extra={"error": type(exc).__name__},
        )
        _redis_client = False
        return None


def _check_redis(client, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
    """
    Fixed window via INCR plus an expiry set on first use.

    INCR and EXPIRE go in one pipeline so a crash between them cannot leave a
    key without a TTL, which would otherwise block that caller forever.
    """
    redis_key = f"ratelimit:{key}"
    pipeline = client.pipeline()
    pipeline.incr(redis_key)
    pipeline.ttl(redis_key)
    count, ttl = pipeline.execute()

    if ttl is None or ttl < 0:
        client.expire(redis_key, window_seconds)
        ttl = window_seconds

    return (count <= limit), int(ttl)


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
    global _redis_client
    with _lock:
        _buckets.clear()
    _redis_client = None


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

        client = _redis()
        if client is not None:
            try:
                allowed, retry_after = _check_redis(
                    client, key, self.limit, self.window_seconds
                )
            except Exception:
                # A Redis blip must not block a legitimate sign-in.
                allowed, retry_after = _check(key, self.limit, self.window_seconds)
        else:
            allowed, retry_after = _check(key, self.limit, self.window_seconds)

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please wait and try again.",
                headers={"Retry-After": str(retry_after)},
            )
