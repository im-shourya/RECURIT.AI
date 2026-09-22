"""
RECRUIT.AI — Error Tracking

Optional Sentry wiring. Unhandled exceptions previously vanished into stdout,
so a 500 in production was only visible if somebody happened to be reading
logs at the time.

Disabled unless SENTRY_DSN is set: the SDK is not even imported, so local
development and CI need no account and no network.
"""

import logging

from app.config import get_settings

settings = get_settings()
log = logging.getLogger("recruit.errors")


def configure_error_tracking() -> bool:
    """Initialise Sentry if configured. Returns whether it was enabled."""
    if not settings.SENTRY_DSN:
        return False

    try:
        import sentry_sdk
    except ImportError:
        log.warning("SENTRY_DSN is set but sentry-sdk is not installed")
        return False

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        # This service handles candidate names, emails, transcripts and
        # interview scores. Sending request bodies and headers to a third
        # party by default would export exactly that, so it stays off and
        # errors carry only the stack.
        send_default_pii=False,
        before_send=_scrub,
    )
    log.info("error tracking enabled", extra={"environment": settings.ENVIRONMENT})
    return True


_SENSITIVE = ("authorization", "cookie", "password", "token", "secret", "api_key")


def _scrub(event, _hint):
    """
    Last line of defence before an event leaves the process.

    send_default_pii=False already excludes most of this; this removes
    anything that slipped into request data or extra context by another route.
    """
    request = event.get("request") or {}
    headers = request.get("headers")
    if isinstance(headers, dict):
        for name in list(headers):
            if any(marker in name.lower() for marker in _SENSITIVE):
                headers[name] = "[redacted]"

    # Never ship a request body: it can carry passwords and reset tokens.
    request.pop("data", None)

    extra = event.get("extra")
    if isinstance(extra, dict):
        for key in list(extra):
            if any(marker in key.lower() for marker in _SENSITIVE):
                extra[key] = "[redacted]"

    return event
