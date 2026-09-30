"""
Tests for the audit trail, candidate data deletion, and candidate
self-service status.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.documents import AuditAction, AuditLog
from app.models.schemas import ApplicantStatusView
from app.services import storage_service

client = TestClient(app)
APPLICANT_ID = uuid.uuid4()


# ──────────────────────────────────────────────
# Audit trail
# ──────────────────────────────────────────────
def test_audit_holds_no_reference_that_could_cascade():
    """
    The collection must outlive the documents it describes, or erasing a
    candidate would also erase the record that they were erased.

    Under PostgreSQL the risk was a foreign key cascading it away. Here there
    is no database-level relationship at all, so the equivalent risk is a
    future change embedding entries in the applicant document. Behaviour is
    verified for real in test_documents.py.
    """
    fields = set(AuditLog.model_fields)
    assert "org_id" in fields, "still scoped to an organisation"
    assert "entity_id" in fields and "entity_label" in fields


def test_audit_captures_a_label_not_just_an_id():
    """
    After the subject is deleted the id resolves to nothing, so the entry
    needs a human-readable label recorded at the time.
    """
    assert "entity_label" in AuditLog.model_fields


def test_audit_is_indexed_for_the_queries_it_serves():
    declared = [
        index.document for index in AuditLog.Settings.indexes
        if hasattr(index, "document")
    ]
    indexed = {field for d in declared for field in d["key"]}
    for field in ("org_id", "action", "created_at"):
        assert field in indexed, f"{field} not indexed"


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

    # The keys and the delete loop are shared with the drive and organisation
    # cascades; test_cascade.py exercises them against real documents.
    source = inspect.getsource(applicant_admin.delete_applicant)
    assert "cascade.stored_file_keys" in source
    assert "cascade.delete_stored_files" in source


def test_audit_is_recorded_before_the_row_is_deleted():
    import inspect
    from app.routers import applicant_admin

    source = inspect.getsource(applicant_admin.delete_applicant)
    assert source.index("audit.record") < source.index("await applicant.delete()")


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


def test_status_view_carries_the_task():
    """The submit page reads the task from here; there is no separate task page."""
    fields = set(ApplicantStatusView.model_fields)
    assert {"task_type", "task_description", "task_deadline"} <= fields


def test_status_reuses_the_existing_token():
    """No new credential: the candidate already holds this one."""
    import inspect
    from app.routers import applicants

    source = inspect.getsource(applicants.get_own_status)
    assert "_applicant_by_submit_token" in source


# ──────────────────────────────────────────────
# Drive open / close
# ──────────────────────────────────────────────
async def test_closing_and_reopening_a_drive_is_audited(org, drive):
    from app.models.schemas import DriveStatusUpdate
    from app.routers.drives import update_drive_status

    await update_drive_status(drive.id, DriveStatusUpdate(status="closed"), org=org)
    await update_drive_status(drive.id, DriveStatusUpdate(status="active"), org=org)

    entries = await AuditLog.find(AuditLog.org_id == org.id).sort(+AuditLog.created_at).to_list()
    assert [e.action for e in entries] == [AuditAction.DRIVE_CLOSED, AuditAction.DRIVE_OPENED]
    assert entries[0].entity_id == drive.id
    assert entries[0].entity_label == drive.name
    assert entries[0].detail == {"from": "active", "to": "closed"}


async def test_setting_a_drive_to_its_current_status_records_nothing(org, drive):
    from app.models.schemas import DriveStatusUpdate
    from app.routers.drives import update_drive_status

    await update_drive_status(drive.id, DriveStatusUpdate(status="active"), org=org)

    assert await AuditLog.find(AuditLog.org_id == org.id).count() == 0


# ──────────────────────────────────────────────
# Retention
# ──────────────────────────────────────────────
def test_audit_entries_expire_after_the_retention_period():
    """
    Entries hold names captured at write time, including those of candidates
    who have since been deleted, so they must not be kept indefinitely.
    """
    from app.models.documents import AUDIT_RETENTION_DAYS

    ttl = [
        index.document for index in AuditLog.Settings.indexes
        if index.document.get("expireAfterSeconds") is not None
    ]
    assert len(ttl) == 1
    assert list(ttl[0]["key"]) == ["created_at"]
    assert ttl[0]["expireAfterSeconds"] == AUDIT_RETENTION_DAYS * 24 * 60 * 60


def test_the_plain_created_at_index_is_retired():
    """
    The TTL index shares its key with the index it replaced. Left in place,
    that index would sit alongside it for no purpose, so boot drops it.
    """
    from app.db import SUPERSEDED_INDEXES

    assert "created_at_-1" in SUPERSEDED_INDEXES["audit_log"]
    names = {index.document.get("name") for index in AuditLog.Settings.indexes}
    assert "created_at_-1" not in names
