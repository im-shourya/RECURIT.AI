"""
Tests for the audit trail, candidate data deletion, and candidate
self-service status.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.database import AuditAction, AuditLog
from app.models.schemas import ApplicantStatusView
from app.services import storage_service

client = TestClient(app)
APPLICANT_ID = uuid.uuid4()


# ──────────────────────────────────────────────
# Audit trail
# ──────────────────────────────────────────────
def test_audit_survives_deletion_of_its_subject():
    """
    The table must outlive the rows it describes, or erasing a candidate would
    also erase the record that they were erased. A foreign key to applicants
    would cascade exactly that away.
    """
    fk_targets = {
        fk.column.table.name for fk in AuditLog.__table__.foreign_keys
    }
    assert "applicants" not in fk_targets
    assert "organisations" in fk_targets, "still scoped to an organisation"


def test_audit_captures_a_label_not_just_an_id():
    """
    After the subject is deleted the id resolves to nothing, so the entry
    needs a human-readable label recorded at the time.
    """
    assert "entity_label" in AuditLog.__table__.c


def test_audit_is_indexed_for_the_queries_it_serves():
    for column in ("org_id", "action", "created_at"):
        assert AuditLog.__table__.c[column].index is True, f"{column} not indexed"


def test_audit_endpoint_requires_authentication():
    assert client.get("/api/audit").status_code == 401


def test_audit_has_no_write_endpoints():
    """A trail that can be edited or deleted answers nothing."""
    methods = {
        m
        for r in app.routes
        if hasattr(r, "methods") and r.path.startswith("/api/audit")
        for m in r.methods
    }
    assert methods <= {"GET", "HEAD", "OPTIONS"}, f"audit is writable: {methods}"


def test_decisions_are_audited():
    import inspect
    from app.routers import applicant_admin

    source = inspect.getsource(applicant_admin.decide_applicant)
    assert "audit.record" in source
    assert "APPLICANT_SELECTED" in source and "APPLICANT_REJECTED" in source


def test_bulk_decisions_are_audited_per_applicant():
    """One entry per candidate, not one for the batch — the trail is per person."""
    import inspect
    from app.routers import applicant_admin

    source = inspect.getsource(applicant_admin.bulk_decision)
    assert "audit.record" in source
    assert source.index("for applicant_id in body.applicant_ids") < source.index("audit.record")


@pytest.mark.parametrize(
    "action",
    ["applicant.selected", "applicant.rejected", "applicant.deleted",
     "drive.created", "drive.deleted", "org.password_changed"],
)
def test_expected_actions_exist(action):
    assert action in {a.value for a in AuditAction}


# ──────────────────────────────────────────────
# Candidate data deletion
# ──────────────────────────────────────────────
def test_delete_endpoint_exists_and_requires_authentication():
    response = client.delete(f"/api/applicants/{APPLICANT_ID}")
    assert response.status_code == 401


def test_deletion_also_removes_stored_files():
    """
    Leaving a recording or submission in the bucket would make the deletion
    only partial, which does not satisfy a deletion request.
    """
    import inspect
    from app.routers import applicant_admin

    source = inspect.getsource(applicant_admin.delete_applicant)
    assert "storage_service.delete_object" in source
    assert "recording_url" in source and "file_url" in source


def test_audit_is_recorded_before_the_row_is_deleted():
    import inspect
    from app.routers import applicant_admin

    source = inspect.getsource(applicant_admin.delete_applicant)
    assert source.index("audit.record") < source.index("db.delete(applicant)")


def test_storage_delete_refuses_paths_that_are_not_ours():
    """
    A legacy row can hold a plain URL rather than a key; that must not be
    turned into a delete against an arbitrary path.
    """
    assert storage_service.delete_object("https://example.com/x.pdf") is False
    assert storage_service.delete_object("../../etc/passwd") is False
    assert storage_service.delete_object("") is False


# ──────────────────────────────────────────────
# Candidate self-service
# ──────────────────────────────────────────────
def test_status_route_exists():
    paths = {r.path for r in app.routes if hasattr(r, "methods")}
    assert "/api/status/{submit_token}" in paths


def test_status_view_hides_the_recruiter_evidence():
    """
    Scores, transcript and malpractice flags are the recruiter's evidence.
    Exposing them mid-process would also tell a candidate how they are being
    graded while they are still being graded.
    """
    fields = set(ApplicantStatusView.model_fields)
    for hidden in ("total_score", "score_intro", "transcript", "malpractice_flags"):
        assert hidden not in fields, f"{hidden} must not be visible to the candidate"


def test_status_view_shows_progress():
    fields = set(ApplicantStatusView.model_fields)
    assert {"status", "has_submitted", "interview_completed", "decision"} <= fields


def test_status_reuses_the_existing_token():
    """No new credential: the candidate already holds this one."""
    import inspect
    from app.routers import applicants

    source = inspect.getsource(applicants.get_own_status)
    assert "_applicant_by_submit_token" in source
