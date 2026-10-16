"""
Tests for the in-app notifications behind the dashboard bell.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.models.documents import (
    Applicant,
    Interview,
    Notification,
    NotificationKind,
    User,
    UserRole,
)
from app.models.schemas import ApplyRequest, SubmissionCreateRequest
from app.routers.applicants import submit_application, submit_task
from app.routers.interviews import end_interview
from app.routers.notifications import list_notifications, mark_all_read, mark_read
from app.services import cascade, notifications


@pytest.fixture
async def colleague(org) -> User:
    user = User(org_id=org.id, email="colleague@example.com", role=UserRole.MEMBER)
    await user.insert()
    return user


async def _kinds(org_id) -> list[str]:
    return [
        n.kind.value
        for n in await Notification.find(Notification.org_id == org_id).sort(
            Notification.created_at
        ).to_list()
    ]


# ──────────────────────────────────────────────
# Events that create one
# ──────────────────────────────────────────────
async def test_an_application_notifies_the_organisation(drive):
    await submit_application(
        drive.link_token,
        ApplyRequest(name="Sam Candidate", email="sam@example.com"),
        BackgroundTasks(),
    )

    [note] = await Notification.find(Notification.org_id == drive.org_id).to_list()
    assert note.kind == NotificationKind.APPLICATION_RECEIVED
    assert "Sam Candidate" in note.body and drive.name in note.body
    applicant = await Applicant.find_one(Applicant.email == "sam@example.com")
    assert note.link == f"/dashboard/applicants/{applicant.id}"


async def test_a_submission_notifies_the_organisation(applicant):
    await submit_task(applicant.submit_token, SubmissionCreateRequest(description="Done"))
    assert await _kinds(applicant.org_id) == ["submission.received"]


async def test_a_finished_interview_notifies_even_with_email_turned_off(org, applicant):
    org.notify_on_interview = False
    await org.save()
    applicant.interview = Interview(
        token="iv-token",
        started_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    await applicant.save()

    from app.models.schemas import InterviewEndRequest

    await end_interview("iv-token", InterviewEndRequest(), BackgroundTasks())
    assert await _kinds(org.id) == ["interview.completed"]


async def test_a_failed_write_does_not_fail_the_request(applicant, monkeypatch):
    async def _boom(*_args, **_kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(Notification, "insert", _boom)
    await notifications.about_applicant(
        applicant, NotificationKind.APPLICATION_RECEIVED, "t", "b"
    )


# ──────────────────────────────────────────────
# Reading and read state
# ──────────────────────────────────────────────
async def _seed(applicant, count=3):
    start = datetime.now(timezone.utc) - timedelta(minutes=count)
    for i in range(count):
        await notifications.about_applicant(
            applicant, NotificationKind.APPLICATION_RECEIVED, f"n{i}", ""
        )
        # Inserted within the same millisecond, so spread them out to give
        # the ordering something to order.
        note = await Notification.find_one(Notification.title == f"n{i}")
        note.created_at = start + timedelta(minutes=i)
        await note.save()


async def test_newest_first_with_an_unread_count(applicant, owner):
    await _seed(applicant)
    listing = await list_notifications(limit=20, user=owner)

    assert [n.title for n in listing.items] == ["n2", "n1", "n0"]
    assert listing.unread_count == 3
    assert not any(n.read for n in listing.items)


async def test_read_state_is_per_person(applicant, owner, colleague):
    await _seed(applicant, count=2)
    first = (await list_notifications(limit=20, user=owner)).items[0]

    await mark_read(first.id, user=owner)

    mine = await list_notifications(limit=20, user=owner)
    assert mine.unread_count == 1
    assert mine.items[0].read is True
    # A colleague still sees it as new.
    assert (await list_notifications(limit=20, user=colleague)).unread_count == 2


async def test_mark_all_read(applicant, owner, colleague):
    await _seed(applicant)
    await mark_all_read(user=owner)

    assert (await list_notifications(limit=20, user=owner)).unread_count == 0
    assert (await list_notifications(limit=20, user=colleague)).unread_count == 3


async def test_another_organisations_notifications_are_invisible(applicant, other_org):
    await _seed(applicant)
    outsider = User(org_id=other_org.id, email="out@example.com", role=UserRole.OWNER)
    await outsider.insert()

    listing = await list_notifications(limit=20, user=outsider)
    assert listing.items == [] and listing.unread_count == 0

    note = await Notification.find_one(Notification.org_id == applicant.org_id)
    with pytest.raises(HTTPException) as exc:
        await mark_read(note.id, user=outsider)
    assert exc.value.status_code == 404


# ──────────────────────────────────────────────
# Erasure
# ──────────────────────────────────────────────
async def test_erasing_a_candidate_erases_their_notifications(applicant):
    await _seed(applicant)
    await cascade.delete_applicant_notifications(applicant.id)
    assert await Notification.find(Notification.applicant_id == applicant.id).count() == 0


async def test_deleting_a_drive_or_organisation_removes_notifications(org, drive, applicant):
    await _seed(applicant)
    await cascade.delete_drive(drive)
    assert await Notification.find(Notification.org_id == org.id).count() == 0

    await notifications.notify(
        org_id=org.id, kind=NotificationKind.APPLICATION_RECEIVED, title="t"
    )
    await cascade.delete_organisation(org)
    assert await Notification.find(Notification.org_id == org.id).count() == 0


def test_notifications_expire():
    from app.models.documents import NOTIFICATION_RETENTION_DAYS

    ttl = [
        i for i in Notification.Settings.indexes
        if i.document.get("expireAfterSeconds") is not None
    ]
    assert ttl and ttl[0].document["expireAfterSeconds"] == (
        NOTIFICATION_RETENTION_DAYS * 24 * 60 * 60
    )
