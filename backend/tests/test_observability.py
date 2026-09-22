"""
Tests for logging configuration and the health check.

The health endpoint pings the database, so these patch db.ping directly
rather than standing up a connection: what is being tested is how the endpoint
reports success and failure, not the driver.
"""

import json
import logging

import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.config import get_settings
from app.logging_config import JsonFormatter, configure_logging

client = TestClient(main.app)
settings = get_settings()


# ──────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────
def test_health_reports_healthy_when_the_database_answers(monkeypatch):
    async def _ok():
        return True

    monkeypatch.setattr(main.db, "ping", _ok)
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["checks"]["database"] == "ok"


def test_health_reports_503_when_the_database_is_unreachable(monkeypatch):
    """
    This previously returned {"status": "healthy"} unconditionally, so it
    stayed green while the database was down — exactly when an orchestrator
    most needs to know.
    """
    async def _fail():
        raise OSError("connection refused")

    monkeypatch.setattr(main.db, "ping", _fail)
    response = client.get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"] == "unavailable"


def test_health_does_not_leak_connection_details(monkeypatch):
    """
    /health is unauthenticated, so the failure reason must not come back in
    the response body where a prober could read hostnames or credentials.
    """
    async def _leaky():
        raise OSError(
            "could not connect to mongodb://admin:hunter2@db.internal:27017"
        )

    monkeypatch.setattr(main.db, "ping", _leaky)
    body = client.get("/health").text

    assert "hunter2" not in body
    assert "db.internal" not in body


# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
def test_json_formatter_emits_one_parseable_object():
    record = logging.LogRecord(
        name="recruit.test", level=logging.INFO, pathname=__file__, lineno=1,
        msg="something happened", args=(), exc_info=None,
    )
    parsed = json.loads(JsonFormatter().format(record))

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "recruit.test"
    assert parsed["message"] == "something happened"
    assert parsed["ts"]


def test_extra_fields_are_included():
    """`extra=` is how callers attach context; it must survive into the output."""
    record = logging.LogRecord(
        name="recruit.test", level=logging.ERROR, pathname=__file__, lineno=1,
        msg="upload failed", args=(), exc_info=None,
    )
    record.applicant_id = "abc-123"
    parsed = json.loads(JsonFormatter().format(record))

    assert parsed["applicant_id"] == "abc-123"


def test_unserialisable_extra_does_not_raise():
    """
    A stray object in `extra` must not blow up inside the logger and take down
    the request it was describing.
    """
    class Opaque:
        pass

    record = logging.LogRecord(
        name="recruit.test", level=logging.INFO, pathname=__file__, lineno=1,
        msg="m", args=(), exc_info=None,
    )
    record.thing = Opaque()
    json.loads(JsonFormatter().format(record))


def test_configure_logging_is_idempotent():
    """Reload and repeated test setup must not duplicate every log line."""
    configure_logging()
    first = len(logging.getLogger().handlers)
    configure_logging()

    assert len(logging.getLogger().handlers) == first == 1


def test_no_bare_prints_remain_in_application_code():
    """
    print() has no level, no timestamp and nothing a log aggregator can parse.

    Parsed with ast rather than matched as text, so a docstring that merely
    mentions print() is not flagged.
    """
    import ast
    import pathlib

    app_dir = pathlib.Path(main.__file__).parent
    offenders = []
    for path in app_dir.rglob("*.py"):
        if "__pycache__" in str(path):
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "print"
            ):
                offenders.append(f"{path.name}:{node.lineno}")

    assert not offenders, f"bare print() calls remain: {offenders}"
