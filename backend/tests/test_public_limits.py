"""
Tests for the limits on candidate-facing endpoints, outbox retention,
account deletion and drive pagination.

Every public route is unauthenticated by necessity — candidates have no
account — so a rate limit is the only thing bounding them.
"""

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute

from app.config import get_settings
from app.main import app
from app.models.documents import EmailOutbox
from app.services import rate_limit

settings = get_settings()


@pytest.fixture(autouse=True)
def _reset():
    rate_limit.reset()
    yield
    rate_limit.reset()


def _dependency_names(dependant) -> set[str]:
    out = set()
    for d in dependant.dependencies:
        call = getattr(d, "call", None)
        if call is not None:
            out.add(getattr(call, "__name__", type(call).__name__))
        out |= _dependency_names(d)
    return out


def _public_routes():
    for route in app.routes:
        if not isinstance(route, APIRoute) or not route.path.startswith("/api"):
            continue
        deps = _dependency_names(route.dependant)
        authed = any(n.startswith("get_current") or n == "_guard" for n in deps)
        if not authed:
            yield route, deps


# ──────────────────────────────────────────────
# Every public endpoint is bounded
# ──────────────────────────────────────────────
def test_every_public_endpoint_is_rate_limited():
    """
    These cannot require authentication — a candidate has no account — so the
    limiter is the only thing standing between a leaked token and unbounded
    writes.
    """
    unbounded = [
        route.path for route, deps in _public_routes() if "RateLimit" not in deps
    ]
    assert not unbounded, f"public endpoints with no limit: {unbounded}"


def test_upload_endpoints_have_the_tightest_limits():
    """
    Each accepted upload is object storage that gets paid for, so these are
    spend limits as much as abuse limits.
    """
    limits = {}
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for dep in route.dependant.dependencies:
            call = getattr(dep, "call", None)
            if isinstance(call, rate_limit.RateLimit):
                limits[call.name] = call.limit

    assert limits["interview_recording"] <= 5, "200MB per call needs a tight cap"
    assert limits["submit_upload"] <= 10


# ──────────────────────────────────────────────
# Keyed on the token, not the address
# ──────────────────────────────────────────────
class _Req:
    def __init__(self, path_params=None, host="1.2.3.4"):
        self.path_params = path_params or {}
        self.headers = {}
        self.client = type("c", (), {"host": host})()


def test_limits_are_keyed_on_the_capability_token():
    """
    One candidate's token must not be able to hammer an endpoint no matter how
    many addresses it comes from.
    """
    limiter = rate_limit.RateLimit("probe", limit=1, window_seconds=60, key_param="token")

    limiter(_Req({"token": "tok-a"}, host="1.1.1.1"))
    with pytest.raises(HTTPException) as exc:
        # Same token, different address — must still be blocked.
        limiter(_Req({"token": "tok-a"}, host="9.9.9.9"))
    assert exc.value.status_code == 429


def test_different_tokens_do_not_share_a_bucket():
    """
    Several candidates behind one NAT must not lock each other out, which is
    exactly what address-keyed limiting would do.
    """
    limiter = rate_limit.RateLimit("probe", limit=1, window_seconds=60, key_param="token")
    limiter(_Req({"token": "tok-a"}, host="1.1.1.1"))
    limiter(_Req({"token": "tok-b"}, host="1.1.1.1"))  # must not raise


def test_falls_back_to_the_address_when_the_token_is_absent():
    """An unknown or missing token still has to be limited by something."""
    limiter = rate_limit.RateLimit("probe", limit=1, window_seconds=60, key_param="token")
    limiter(_Req({}, host="5.5.5.5"))
    with pytest.raises(HTTPException):
        limiter(_Req({}, host="5.5.5.5"))


# ──────────────────────────────────────────────
# Outbox retention
# ──────────────────────────────────────────────
def test_delivered_mail_expires():
    ttl = [
        index.document
        for index in EmailOutbox.Settings.indexes
        if "expireAfterSeconds" in getattr(index, "document", {})
    ]
    assert ttl, "sent mail would accumulate forever without a TTL index"
    assert "sent_at" in ttl[0]["key"]


def test_pending_mail_is_not_expired():
    """
    The TTL is on sent_at, and MongoDB ignores documents where the field is
    null — so pending rows survive for retry and failed ones for inspection.
    """
    assert EmailOutbox.model_fields["sent_at"].default is None


# ──────────────────────────────────────────────
# Account deletion
# ──────────────────────────────────────────────
def test_account_deletion_requires_authentication():
    from fastapi.testclient import TestClient

    # .request() rather than .delete(): the DELETE helper takes no json body.
    response = TestClient(app).request(
        "DELETE", "/api/auth/me", json={"current_password": "x", "confirm": True}
    )
    assert response.status_code == 401


def test_account_deletion_is_owner_only_and_needs_the_password():
    import inspect
    from app.routers import auth

    source = inspect.getsource(auth.delete_account)
    assert "require_role(UserRole.OWNER)" in inspect.getsource(auth)
    assert "verify_password" in source
    assert "cascade.delete_organisation" in source


# ──────────────────────────────────────────────
# Drive pagination
# ──────────────────────────────────────────────
def test_drive_detail_does_not_embed_every_applicant():
    """
    It used to return all of them, so a drive with thousands of candidates
    produced one enormous response.
    """
    import inspect
    from app.routers import drives

    source = inspect.getsource(drives.get_drive)
    assert "DRIVE_DETAIL_APPLICANT_PREVIEW" in source
    assert drives.DRIVE_DETAIL_APPLICANT_PREVIEW <= 50


async def test_drive_applicants_are_paginated_and_scoped(drive, applicant, other_org):
    """The count must be exact even though the page is bounded."""
    from app.models.documents import Applicant

    total = await Applicant.find(Applicant.drive_id == drive.id).count()
    assert total == 1

    # A drive belonging to another organisation must not resolve.
    from app.routers.drives import _owned_drive
    from fastapi import HTTPException as HE

    with pytest.raises(HE) as exc:
        await _owned_drive(drive.id, other_org)
    assert exc.value.status_code == 404


# ──────────────────────────────────────────────
# The candidate's own status link
#
# The emailed link used to be the only copy of the submit token a candidate
# ever received, so a bounced confirmation ended their application silently.
# The apply response now carries it — but only that response.
# ──────────────────────────────────────────────
def test_apply_response_returns_the_submit_token():
    """Without this the client cannot show a status link at all."""
    from app.models.schemas import ApplyAcceptedResponse

    assert "submit_token" in ApplyAcceptedResponse.model_fields


def test_organisation_facing_responses_never_carry_the_submit_token():
    """
    The token is a capability: whoever holds it can submit work as that
    candidate. It belongs to the candidate, not to every team member browsing
    the applicant list.
    """
    from app.models.schemas import ApplicantResponse, ApplicantStatusView

    assert "submit_token" not in ApplicantResponse.model_fields
    assert "submit_token" not in ApplicantStatusView.model_fields


def test_apply_route_uses_the_dedicated_response_model():
    from app.models.schemas import ApplyAcceptedResponse
    from app.routers import applicants

    route = next(
        r for r in app.routes
        if isinstance(r, APIRoute)
        and r.path == "/api/apply/{link_token}"
        and "POST" in r.methods
    )
    assert route.response_model is ApplyAcceptedResponse


def test_status_view_still_withholds_the_recruiters_evidence():
    """
    The status page renders whatever this model exposes, so the exclusion has
    to hold here rather than in the page.
    """
    from app.models.schemas import ApplicantStatusView

    fields = ApplicantStatusView.model_fields
    for leaked in ("total_score", "score_intro", "transcript", "malpractice_flags"):
        assert leaked not in fields, f"{leaked} must not reach the candidate"
