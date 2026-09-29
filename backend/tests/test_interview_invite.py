"""
Tests for the recruiter checkpoint between submission and interview.

Submitting used to set `submitted` and overwrite it with `interview_sent` two
lines later, so nobody ever sat in `submitted` and everyone who submitted
anything was interviewed. Submission now stops at `submitted`, and a recruiter
moves the candidate on.
"""

from fastapi.testclient import TestClient

from app.main import app
from app.models.documents import (
    Applicant,
    ApplicantStatus,
    AuditAction,
    AuditLog,
    Submission,
    User,
    UserRole,
)
from app.services.auth_service import hash_password, issue_token

client = TestClient(app)


def _auth(user) -> dict:
    return {"Authorization": f"Bearer {issue_token(user)}"}


async def _submitted(applicant: Applicant) -> Applicant:
    applicant.submission = Submission(description="done")
    applicant.status = ApplicantStatus.SUBMITTED
    await applicant.save()
    return applicant


async def test_submitting_stops_at_submitted(applicant):
    response = client.post(
        f"/api/submit/{applicant.submit_token}", json={"description": "My work"}
    )
    assert response.status_code == 201

    stored = await Applicant.get(applicant.id)
    assert stored.status == ApplicantStatus.SUBMITTED
    assert stored.interview is None, "submission must not mint an interview"


async def test_invite_moves_a_submitted_candidate_to_interview(applicant, owner):
    await _submitted(applicant)

    response = client.post(f"/api/applicants/{applicant.id}/invite", headers=_auth(owner))

    assert response.status_code == 200
    assert response.json()["status"] == "interview_sent"
    stored = await Applicant.get(applicant.id)
    assert stored.status == ApplicantStatus.INTERVIEW_SENT
    assert stored.interview is not None and stored.interview.token


async def test_invite_is_audited(applicant, owner):
    await _submitted(applicant)
    client.post(f"/api/applicants/{applicant.id}/invite", headers=_auth(owner))

    entries = await AuditLog.find(AuditLog.entity_id == applicant.id).to_list()
    assert [e.action for e in entries] == [AuditAction.APPLICANT_INVITED]


async def test_invite_refuses_a_candidate_who_has_not_submitted(applicant, owner):
    response = client.post(f"/api/applicants/{applicant.id}/invite", headers=_auth(owner))
    assert response.status_code == 400
    assert (await Applicant.get(applicant.id)).interview is None


async def test_invite_cannot_mint_a_second_interview(applicant, owner):
    """A second invite would silently invalidate the link already emailed."""
    await _submitted(applicant)
    client.post(f"/api/applicants/{applicant.id}/invite", headers=_auth(owner))
    first = (await Applicant.get(applicant.id)).interview.token

    response = client.post(f"/api/applicants/{applicant.id}/invite", headers=_auth(owner))

    assert response.status_code == 400
    assert (await Applicant.get(applicant.id)).interview.token == first


async def test_members_cannot_invite(applicant, org):
    member = User(
        org_id=org.id,
        name="Member",
        email="member@example.com",
        password_hash=hash_password("correct-horse"),
        role=UserRole.MEMBER,
    )
    await member.insert()
    await _submitted(applicant)

    response = client.post(f"/api/applicants/{applicant.id}/invite", headers=_auth(member))

    assert response.status_code == 403
