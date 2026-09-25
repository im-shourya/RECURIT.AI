"""
RECRUIT.AI — Logging

The app previously used bare print() calls, which meant no levels, no
timestamps, no request correlation, and nothing a log aggregator could parse.

Two formats:
  - text in development, for readability
  - single-line JSON in every other environment, because hosted log viewers
    (Render, CloudWatch, Datadog) index structured fields and cannot do much
    with free-form text

Configured once at import of app.main, before any logger is used.
"""

import json
import logging
import sys
from datetime import datetime, timezone

from app.config import get_settings

settings = get_settings()

# Attributes LogRecord always carries; anything else was attached by the
# caller via `extra=` and belongs in the structured output.
_STANDARD_FIELDS = set(
    logging.LogRecord("", 0, "", 0, "", None, None).__dict__
) | {"message", "asctime", "taskName"}


class JsonFormatter(logging.Formatter):
    """One JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in _STANDARD_FIELDS and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # default=str so a stray UUID or datetime in `extra` cannot raise
        # inside the logger and take down the request that was being logged.
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL.upper())

    # Replace handlers rather than adding, so repeated calls (tests, reload)
    # do not duplicate every line.
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if settings.ENVIRONMENT == "development":
        handler.setFormatter(
            logging.Formatter("%(asctime)s  %(levelname)-8s %(name)s  %(message)s")
        )
    else:
        handler.setFormatter(JsonFormatter())

    root.addHandler(handler)

    # Uvicorn installs its own handlers; let them flow through ours instead so
    # access logs share the format.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
