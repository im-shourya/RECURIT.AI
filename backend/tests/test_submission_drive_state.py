"""
Tests that a submission respects the drive it belongs to.

`submit_task` used to check only the task deadline, so a closed drive kept
taking work through submit tokens issued while it was open, and a GitHub drive
accepted a task submission it has no task for. The apply endpoint already
refused both.
"""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.documents import Applicant, DriveStatus, TaskType
from app.services import storage_service

client = TestClient(app)


def _submit(applicant):
    return client.post(f"/api/submit/{applicant.submit_token}", json={"description": "work"})


def _upload(applicant):
    return client.post(
        f"/api/submit/{applicant.submit_token}/upload",
        files={"file": ("cv.pdf", b"data", "application/pdf")},
    )


@pytest.fixture(autouse=True)
def _no_storage(monkeypatch):
    # A refused upload must be refused before storage is touched.
    monkeypatch.setattr(storage_service, "is_configured", lambda: True)
    monkeypatch.setattr(
        storage_service, "_client", lambda: pytest.fail("must not reach storage")
    )


@pytest.mark.parametrize("send", [_submit, _upload])
async def test_a_closed_drive_takes_no_work(drive, applicant, send):
    drive.status = DriveStatus.CLOSED
    await drive.save()

    response = send(applicant)

    assert response.status_code == 400
    assert "no longer accepting" in response.json()["detail"]
    assert (await Applicant.get(applicant.id)).submission is None


@pytest.mark.parametrize("send", [_submit, _upload])
async def test_a_github_drive_takes_no_task_submission(drive, applicant, send):
    drive.task_type = TaskType.GITHUB
    await drive.save()

    response = send(applicant)

    assert response.status_code == 400
    assert "does not take task submissions" in response.json()["detail"]


@pytest.mark.parametrize("send", [_submit, _upload])
async def test_the_task_deadline_still_applies(drive, applicant, send):
    drive.task_deadline = date.today() - timedelta(days=1)
    await drive.save()

    response = send(applicant)

    assert response.status_code == 400
    assert "deadline" in response.json()["detail"]


async def test_an_open_task_drive_still_takes_a_submission(applicant):
    assert _submit(applicant).status_code == 201
