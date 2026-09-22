"""
Tests for the platform hardening work: Redis-backed rate limits, optional
error tracking, and the duplicate-application race.
"""

import pytest

from app.config import get_settings
from app.error_tracking import _scrub, configure_error_tracking
from app.models.database import Applicant
from app.services import rate_limit

settings = get_settings()


@pytest.fixture(autouse=True)
def _reset():
    rate_limit.reset()
    yield
    rate_limit.reset()


# ──────────────────────────────────────────────
# Rate limiting: Redis with a safe fallback
# ──────────────────────────────────────────────
def test_falls_back_to_memory_when_redis_is_unreachable(monkeypatch):
    """
    A limiter that cannot reach its store must degrade, not fail closed — it
    sits in front of sign-in, so failing closed would lock everyone out.
    """
    monkeypatch.setattr(settings, "REDIS_URL", "redis://127.0.0.1:1/0")
    rate_limit.reset()

    assert rate_limit._redis() is None
    allowed, _ = rate_limit._check("probe:1.1.1.1", limit=2, window_seconds=60)
    assert allowed is True


def test_redis_probe_is_not_repeated_per_request(monkeypatch):
    """
    An unreachable Redis must be probed once, not on every request — a
    one-second connect timeout on each call would be worse than no limiter.
    """
    monkeypatch.setattr(settings, "REDIS_URL", "redis://127.0.0.1:1/0")
    rate_limit.reset()

    rate_limit._redis()
    assert rate_limit._redis_client is False, "failure must be cached"


def test_no_redis_url_means_no_probe(monkeypatch):
    monkeypatch.setattr(settings, "REDIS_URL", "")
    rate_limit.reset()
    assert rate_limit._redis() is None


class _FakePipeline:
    def __init__(self, store, key):
        self.store, self.key, self.ops = store, key, []

    def incr(self, key):
        self.ops.append(("incr", key))

    def ttl(self, key):
        self.ops.append(("ttl", key))

    def execute(self):
        self.store[self.key] = self.store.get(self.key, 0) + 1
        return [self.store[self.key], self.store.get(f"{self.key}:ttl", -1)]


class _FakeRedis:
    def __init__(self):
        self.store = {}

    def pipeline(self):
        return _FakePipeline(self.store, "ratelimit:k")

    def expire(self, key, seconds):
        self.store[f"{key}:ttl"] = seconds


def test_redis_backend_counts_and_blocks():
    client = _FakeRedis()
    results = [
        rate_limit._check_redis(client, "k", limit=3, window_seconds=60)[0]
        for _ in range(5)
    ]
    assert results[:3] == [True, True, True]
    assert results[3:] == [False, False]


def test_redis_backend_sets_a_ttl_on_first_use():
    """
    Without an expiry the key would never reset and that caller would be
    blocked permanently.
    """
    client = _FakeRedis()
    rate_limit._check_redis(client, "k", limit=1, window_seconds=45)
    assert client.store.get("ratelimit:k:ttl") == 45


# ──────────────────────────────────────────────
# Error tracking
# ──────────────────────────────────────────────
def test_error_tracking_is_off_without_a_dsn(monkeypatch):
    """Local development and CI must need no account and no network."""
    monkeypatch.setattr(settings, "SENTRY_DSN", "")
    assert configure_error_tracking() is False


def test_scrub_redacts_credential_headers():
    event = _scrub(
        {"request": {"headers": {"Authorization": "Bearer abc", "Accept": "*/*"}}}, None
    )
    assert event["request"]["headers"]["Authorization"] == "[redacted]"
    assert event["request"]["headers"]["Accept"] == "*/*", "harmless headers stay"


def test_scrub_drops_the_request_body_entirely():
    """Bodies carry passwords and reset tokens; none of it should leave."""
    event = _scrub({"request": {"data": {"password": "hunter2"}}}, None)
    assert "data" not in event["request"]


def test_scrub_redacts_sensitive_extra_context():
    event = _scrub({"extra": {"reset_token": "abc", "applicant_id": "123"}}, None)
    assert event["extra"]["reset_token"] == "[redacted]"
    assert event["extra"]["applicant_id"] == "123", "non-sensitive context is kept"


def test_scrub_tolerates_a_bare_event():
    _scrub({}, None)


# ──────────────────────────────────────────────
# Duplicate applications
# ──────────────────────────────────────────────
def test_applicant_has_a_uniqueness_constraint():
    """
    The handler's pre-check is a read before a write, so two concurrent
    requests could both pass it. Only the database closes that window.
    """
    constraints = {
        c.name for c in Applicant.__table__.constraints if hasattr(c, "columns")
    }
    assert "uq_applicant_drive_email" in constraints


def test_uniqueness_is_scoped_per_drive():
    """The same person must still be able to apply to a different drive."""
    constraint = next(
        c for c in Applicant.__table__.constraints
        if getattr(c, "name", None) == "uq_applicant_drive_email"
    )
    assert {c.name for c in constraint.columns} == {"drive_id", "email"}


def test_apply_handles_the_integrity_error():
    """
    Losing the race must read the same to the caller as applying twice, so a
    double-click is not reported as a server error.
    """
    import inspect
    from app.routers import applicants

    source = inspect.getsource(applicants.submit_application)
    assert "IntegrityError" in source
    assert "db.rollback()" in source
