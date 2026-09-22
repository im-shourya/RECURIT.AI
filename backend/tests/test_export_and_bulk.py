"""
Tests for CSV export, email resend, and bulk decisions.

The CSV cells are the interesting part: applicant names and skills arrive from
a public form, so an exported sheet is an injection vector unless every cell is
neutralised before a recruiter opens it in Excel or Sheets.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.models.schemas import BulkDecisionRequest, ResendEmailRequest
from app.routers.applicant_admin import _csv_safe

client = TestClient(app)
APPLICANT_ID = uuid.uuid4()


# ──────────────────────────────────────────────
# CSV formula injection
# ──────────────────────────────────────────────
@pytest.mark.parametrize(
    "payload",
    [
        "=1+1",
        '=HYPERLINK("http://evil.test","click")',
        "+1+1",
        "-1+1",
        "@SUM(A1:A9)",
        "=cmd|'/c calc'!A0",
    ],
)
def test_formula_cells_are_neutralised(payload):
    """
    A cell beginning with =, +, - or @ is evaluated by Excel and Sheets. Each
    must be prefixed so it is rendered as text rather than executed.
    """
    result = _csv_safe(payload)
    assert result.startswith("'"), f"{payload!r} was left executable"
    assert result[1:] == payload, "the original value must still be readable"


@pytest.mark.parametrize(
    "payload", ["Alex Developer", "alex@example.com", "React, TypeScript", "10-20 hrs"]
)
def test_ordinary_values_are_untouched(payload):
    """Normal data must not be mangled; only leading formula characters matter."""
    if payload.startswith(("=", "+", "-", "@")):
        pytest.skip("covered by the injection test")
    assert _csv_safe(payload) == payload


def test_none_becomes_empty_string():
    assert _csv_safe(None) == ""


def test_numbers_survive_as_text():
    assert _csv_safe(87) == "87"


# ──────────────────────────────────────────────
# Route ordering
# ──────────────────────────────────────────────
def test_export_route_is_declared_before_the_uuid_route():
    """
    FastAPI matches in definition order. If /{applicant_id} came first it would
    capture /export and reject it as an invalid UUID, so the ordering is
    load-bearing rather than cosmetic.
    """
    paths = [r.path for r in app.routes if hasattr(r, "methods")]
    assert paths.index("/api/applicants/export") < paths.index(
        "/api/applicants/{applicant_id}"
    )


# ──────────────────────────────────────────────
# Request validation
# ──────────────────────────────────────────────
@pytest.mark.parametrize("kind", ["applied", "task", "interview", "result"])
def test_resend_accepts_known_email_types(kind):
    assert ResendEmailRequest(type=kind).type == kind


@pytest.mark.parametrize("kind", ["welcome", "RESULT", "", "spam"])
def test_resend_rejects_unknown_email_types(kind):
    with pytest.raises(ValidationError):
        ResendEmailRequest(type=kind)


def test_bulk_decision_requires_at_least_one_id():
    with pytest.raises(ValidationError):
        BulkDecisionRequest(applicant_ids=[], decision="selected")


def test_bulk_decision_is_capped():
    """
    Each accepted id sends an email, so an unbounded list would be a way to fan
    out a large amount of mail from a single request.
    """
    too_many = [uuid.uuid4() for _ in range(101)]
    with pytest.raises(ValidationError):
        BulkDecisionRequest(applicant_ids=too_many, decision="selected")

    at_limit = [uuid.uuid4() for _ in range(100)]
    assert len(BulkDecisionRequest(applicant_ids=at_limit, decision="selected").applicant_ids) == 100


@pytest.mark.parametrize("decision", ["hired", "SELECTED", "maybe", ""])
def test_bulk_decision_rejects_invalid_decisions(decision):
    with pytest.raises(ValidationError):
        BulkDecisionRequest(applicant_ids=[uuid.uuid4()], decision=decision)


# ──────────────────────────────────────────────
# Authentication boundary
# ──────────────────────────────────────────────
@pytest.mark.parametrize(
    "method,path,payload",
    [
        ("get", "/api/applicants/export", None),
        ("post", f"/api/applicants/{APPLICANT_ID}/resend-email", {"type": "result"}),
        (
            "post",
            "/api/applicants/bulk-decision",
            {"applicant_ids": [str(APPLICANT_ID)], "decision": "selected"},
        ),
    ],
)
def test_requires_authentication(method, path, payload):
    kwargs = {"json": payload} if payload is not None else {}
    assert getattr(client, method)(path, **kwargs).status_code == 401
