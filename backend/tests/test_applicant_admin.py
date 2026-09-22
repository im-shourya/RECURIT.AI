"""
Tests for the organisation-scoped applicant endpoints.

These run without a database. A Postgres server is not available in every
development environment, and the models use PostgreSQL-specific column types
(UUID, ARRAY, JSONB) that SQLite cannot host, so DB-backed integration tests
are deliberately out of scope here.

What is covered without a database:
  - the authentication boundary (auth is resolved before any DB work)
  - the authorization filter, asserted against the compiled SQL
  - request validation rules

What is NOT covered: end-to-end behaviour against a real database.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.models.schemas import ApplicantDecisionRequest, PasswordChangeRequest

client = TestClient(app)

APPLICANT_ID = "3f7c1a52-1d44-4a5e-9c3b-9f2a7e6d5c41"


# ──────────────────────────────────────────────
# Authentication boundary
# ──────────────────────────────────────────────
@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/applicants"),
        ("get", f"/api/applicants/{APPLICANT_ID}"),
        ("post", f"/api/applicants/{APPLICANT_ID}/decision"),
        ("post", "/api/auth/change-password"),
    ],
)
def test_endpoint_requires_authentication(method, path):
    """Every new endpoint must reject an unauthenticated caller."""
    kwargs = {"json": {}} if method == "post" else {}
    response = getattr(client, method)(path, **kwargs)
    assert response.status_code == 401, (
        f"{method.upper()} {path} returned {response.status_code}, expected 401"
    )


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/applicants"),
        ("get", f"/api/applicants/{APPLICANT_ID}"),
        ("post", f"/api/applicants/{APPLICANT_ID}/decision"),
    ],
)
def test_endpoint_rejects_garbage_token(method, path):
    """A malformed bearer token must be rejected, not merely ignored."""
    kwargs = {"json": {"decision": "selected"}} if method == "post" else {}
    response = getattr(client, method)(
        path,
        headers={"Authorization": "Bearer not-a-real-jwt"},
        **kwargs,
    )
    assert response.status_code == 401


# ──────────────────────────────────────────────
# Authorization filter
#
# Previously asserted by compiling the SQL and reading the WHERE clause,
# because no database was reachable. It now runs the query.
# ──────────────────────────────────────────────
async def test_applicant_lookup_is_scoped_to_the_organisation(applicant, other_org):
    """
    The org scoping is the authorization boundary for these endpoints. A
    dropped filter here would expose every organisation's candidates to every
    other organisation.
    """
    from app.models.documents import Applicant

    found = await Applicant.find_one(
        Applicant.id == applicant.id, Applicant.org_id == other_org.id
    )
    assert found is None, "another organisation must not resolve this applicant"

    mine = await Applicant.find_one(
        Applicant.id == applicant.id, Applicant.org_id == applicant.org_id
    )
    assert mine is not None


# ──────────────────────────────────────────────
# Request validation
# ──────────────────────────────────────────────
@pytest.mark.parametrize("decision", ["selected", "rejected"])
def test_decision_accepts_valid_values(decision):
    assert ApplicantDecisionRequest(decision=decision).decision == decision


@pytest.mark.parametrize(
    "decision",
    ["", "SELECTED", "hired", "applied", "selected; drop table applicants", "null"],
)
def test_decision_rejects_invalid_values(decision):
    """Only the two terminal states may be set through this endpoint."""
    with pytest.raises(ValidationError):
        ApplicantDecisionRequest(decision=decision)


def test_password_change_enforces_minimum_length():
    with pytest.raises(ValidationError):
        PasswordChangeRequest(current_password="old", new_password="short")

    # 8 characters is the documented minimum and must be accepted.
    assert PasswordChangeRequest(current_password="old", new_password="12345678")


def test_password_change_requires_current_password():
    with pytest.raises(ValidationError):
        PasswordChangeRequest(current_password="", new_password="a-long-enough-password")


# ──────────────────────────────────────────────
# Contract
# ──────────────────────────────────────────────
def test_openapi_schema_builds():
    """Catches malformed response models across the whole app."""
    schema = app.openapi()
    paths = schema["paths"]
    assert "/api/applicants" in paths
    assert "/api/applicants/{applicant_id}" in paths
    assert "/api/applicants/{applicant_id}/decision" in paths
    assert "/api/auth/change-password" in paths
