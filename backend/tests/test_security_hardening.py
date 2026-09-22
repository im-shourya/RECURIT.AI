"""
Tests for the security hardening changes.

Each test corresponds to a specific weakness that existed before:
  - the submission endpoint keyed off a bare applicant UUID
  - interview detail was readable by anyone holding a token
  - CORS paired a wildcard origin with credentials
  - interview links never expired
  - nothing was rate limited
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.models.database import Applicant, Interview
from app.services import rate_limit

client = TestClient(app)
settings = get_settings()


@pytest.fixture(autouse=True)
def _clear_rate_limits():
    rate_limit.reset()
    yield
    rate_limit.reset()


# ──────────────────────────────────────────────
# Submission endpoint no longer keys off a UUID
# ──────────────────────────────────────────────
def test_submit_route_takes_a_token_not_an_applicant_id():
    """
    The old route was /submit/{applicant_id}. Anyone holding or guessing an
    applicant id could submit on that candidate's behalf.
    """
    paths = {r.path for r in app.routes if hasattr(r, "methods")}
    assert "/api/submit/{submit_token}" in paths
    assert "/api/submit/{applicant_id}" not in paths
    assert "/api/submit/{submit_token}/upload" in paths


def test_applicant_model_has_a_submit_token():
    column = Applicant.__table__.c.submit_token
    assert column.unique is True
    assert column.index is True


def test_submit_token_column_is_wide_enough_for_the_generated_value():
    """secrets.token_urlsafe(32) renders as 43 characters."""
    assert Applicant.__table__.c.submit_token.type.length >= 43


# ──────────────────────────────────────────────
# Interview detail requires an organisation
# ──────────────────────────────────────────────
def test_interview_detail_requires_authentication():
    """
    This returned the full transcript, scores and malpractice flags to anyone
    holding an interview token — including the candidate themselves and anyone
    they forwarded the link to.
    """
    response = client.get(f"/api/interview/{uuid.uuid4().hex}/detail")
    assert response.status_code == 401


def test_interview_detail_rejects_a_garbage_token_unauthenticated():
    response = client.get(
        f"/api/interview/{uuid.uuid4().hex}/detail",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert response.status_code == 401


def test_candidate_interview_endpoints_stay_public():
    """
    Locking down /detail must not lock out the candidate: they have no account
    and reach their interview by token alone.
    """
    spec = app.openapi()["paths"]
    for path in (
        "/api/interview/{token}",
        "/api/interview/{token}/start",
        "/api/interview/{token}/answer",
        "/api/interview/{token}/end",
    ):
        assert path in spec


# ──────────────────────────────────────────────
# Interview expiry
# ──────────────────────────────────────────────
def test_interview_has_an_expiry_column():
    assert "expires_at" in Interview.__table__.c


def test_expiry_is_nullable_so_existing_links_keep_working():
    """
    A row created before this column existed has NULL, which must read as "no
    expiry set" rather than "expired", or every in-flight interview breaks on
    deploy.
    """
    assert Interview.__table__.c.expires_at.nullable is True


def test_interview_ttl_is_configured():
    assert settings.INTERVIEW_TOKEN_TTL_DAYS > 0


# ──────────────────────────────────────────────
# CORS
# ──────────────────────────────────────────────
def test_cors_origins_are_explicit_not_wildcard():
    """
    allow_origins=["*"] with allow_credentials=True is rejected by browsers:
    the CORS spec forbids a wildcard on a credentialed response. The old
    config paired them, so it was not merely permissive, it did not work.
    """
    origins = [o.strip() for o in settings.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]
    assert origins, "at least one origin must be configured"
    assert "*" not in origins


def test_cors_middleware_is_installed():
    names = [m.cls.__name__ for m in app.user_middleware]
    assert "CORSMiddleware" in names


# ──────────────────────────────────────────────
# Rate limiting
# ──────────────────────────────────────────────
def test_repeated_logins_are_eventually_throttled(monkeypatch):
    """
    /auth/login was unbounded, so credentials could be stuffed at full speed.

    The endpoint needs no database to reach the limiter: the dependency runs
    before the handler body.
    """
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)

    statuses = []
    for _ in range(15):
        response = client.post(
            "/api/auth/login", json={"email": "a@b.test", "password": "x"}
        )
        statuses.append(response.status_code)
        if response.status_code == 429:
            break

    assert 429 in statuses, f"login was never throttled: {statuses}"


def test_throttled_response_tells_the_caller_when_to_retry():
    for _ in range(15):
        response = client.post(
            "/api/auth/login", json={"email": "a@b.test", "password": "x"}
        )
        if response.status_code == 429:
            assert response.headers.get("Retry-After")
            return
    pytest.fail("never reached the limit")


def test_limits_are_tracked_per_caller():
    """One caller hitting the limit must not lock everyone else out."""
    rate_limit.reset()
    allowed_first, _ = rate_limit._check("probe:1.1.1.1", limit=1, window_seconds=60)
    blocked_first, _ = rate_limit._check("probe:1.1.1.1", limit=1, window_seconds=60)
    allowed_other, _ = rate_limit._check("probe:2.2.2.2", limit=1, window_seconds=60)

    assert allowed_first is True
    assert blocked_first is False
    assert allowed_other is True, "a different caller must not inherit the block"


def test_limiter_can_be_disabled(monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", False)
    limiter = rate_limit.RateLimit("probe", limit=1, window_seconds=60)

    class _Req:
        headers: dict = {}
        client = None

    # Well past the limit, but disabled means it must never raise.
    for _ in range(5):
        limiter(_Req())


def test_forwarded_header_is_ignored_unless_proxies_are_trusted(monkeypatch):
    """
    X-Forwarded-For is trivially forged. Honouring it without a proxy in front
    would let one caller bypass every limit by varying the header.
    """
    monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", False)

    class _Req:
        headers = {"x-forwarded-for": "9.9.9.9"}

        class client:
            host = "1.2.3.4"

    assert rate_limit.client_identifier(_Req()) == "1.2.3.4"


def test_forwarded_header_is_used_when_proxies_are_trusted(monkeypatch):
    monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", True)

    class _Req:
        headers = {"x-forwarded-for": "9.9.9.9, 10.0.0.1"}

        class client:
            host = "1.2.3.4"

    assert rate_limit.client_identifier(_Req()) == "9.9.9.9"
