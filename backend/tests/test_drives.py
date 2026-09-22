"""
Tests for drive editing and deletion.

Deletion cascades to applicants, submissions, interviews and email logs, so the
guard around it is the part worth pinning down.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.models.schemas import DriveUpdateRequest

client = TestClient(app)
DRIVE_ID = uuid.uuid4()


# ──────────────────────────────────────────────
# Authentication boundary
# ──────────────────────────────────────────────
@pytest.mark.parametrize(
    "method,path",
    [
        ("patch", f"/api/drives/{DRIVE_ID}"),
        ("delete", f"/api/drives/{DRIVE_ID}"),
    ],
)
def test_requires_authentication(method, path):
    kwargs = {"json": {"name": "Renamed"}} if method == "patch" else {}
    response = getattr(client, method)(path, **kwargs)
    assert response.status_code == 401


# ──────────────────────────────────────────────
# What may be edited
# ──────────────────────────────────────────────
def test_partial_update_only_carries_supplied_fields():
    """
    exclude_unset is what makes this a genuine PATCH. Without it every omitted
    field would be written back as None and silently wipe the drive.
    """
    body = DriveUpdateRequest(name="Renamed")
    assert body.model_dump(exclude_unset=True) == {"name": "Renamed"}


@pytest.mark.parametrize(
    "field",
    ["link_token", "qr_code_url", "org_id", "task_type", "id"],
)
def test_immutable_fields_are_not_editable(field):
    """
    Rotating link_token would break every share link and QR code already handed
    out; task_type would strand applicants mid-flow; org_id would hand the
    drive to another organisation. None may be set through this endpoint.
    """
    assert field not in DriveUpdateRequest.model_fields


@pytest.mark.parametrize("level", ["beginner", "intermediate", "advanced"])
def test_question_level_accepts_valid_values(level):
    assert DriveUpdateRequest(question_level=level).question_level == level


@pytest.mark.parametrize("level", ["expert", "BEGINNER", "", "0"])
def test_question_level_rejects_invalid_values(level):
    with pytest.raises(ValidationError):
        DriveUpdateRequest(question_level=level)


@pytest.mark.parametrize("status", ["active", "closed"])
def test_status_accepts_valid_values(status):
    assert DriveUpdateRequest(status=status).status == status


@pytest.mark.parametrize("status", ["deleted", "ACTIVE", "open"])
def test_status_rejects_invalid_values(status):
    with pytest.raises(ValidationError):
        DriveUpdateRequest(status=status)


def test_name_has_a_minimum_length():
    with pytest.raises(ValidationError):
        DriveUpdateRequest(name="x")


def test_empty_update_is_representable_and_caught_by_the_router():
    """The router rejects an empty patch with 400; the schema itself allows it."""
    assert DriveUpdateRequest().model_dump(exclude_unset=True) == {}


# ──────────────────────────────────────────────
# Contract
# ──────────────────────────────────────────────
def test_routes_are_registered():
    paths = app.openapi()["paths"]
    assert "patch" in paths["/api/drives/{drive_id}"]
    assert "delete" in paths["/api/drives/{drive_id}"]


def test_delete_exposes_a_confirm_guard():
    """
    Deletion cascades to candidate data, so the destructive path must be opt-in
    rather than the default.
    """
    delete = app.openapi()["paths"]["/api/drives/{drive_id}"]["delete"]
    params = {p["name"] for p in delete.get("parameters", [])}
    assert "confirm" in params
