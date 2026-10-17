"""
Tests that recruiters never receive a candidate's interview token.

The interview endpoints are unauthenticated and gated only on that token, so
any response carrying it handed every team member a working capability to
open, start or answer someone else's interview.
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.models.documents import Interview
from app.routers.applicant_admin import applicant_to_response, get_applicant_interview

TOKEN = "live-interview-token-do-not-leak"


@pytest.fixture
async def interviewed(applicant):
    applicant.interview = Interview(
        token=TOKEN,
        transcript=[{"round": "intro", "question": "Hi?", "answer": "Hello"}],
        score_intro=50,
        total_score=50,
    )
    await applicant.save()
    return applicant


async def test_applicant_response_carries_no_interview_token(interviewed):
    body = applicant_to_response(interviewed).model_dump_json()
    assert TOKEN not in body


async def test_recruiter_reads_the_interview_by_applicant_id(interviewed, org, drive):
    detail = await get_applicant_interview(interviewed.id, org=org)

    assert detail.transcript[0]["answer"] == "Hello"
    assert detail.drive_name == drive.name
    assert TOKEN not in detail.model_dump_json()


async def test_another_organisations_candidate_is_not_found(interviewed, other_org):
    with pytest.raises(HTTPException) as exc:
        await get_applicant_interview(interviewed.id, org=other_org)
    assert exc.value.status_code == 404


async def test_a_candidate_without_an_interview_is_not_found(applicant, org):
    with pytest.raises(HTTPException) as exc:
        await get_applicant_interview(applicant.id, org=org)
    assert exc.value.status_code == 404


def test_interview_detail_by_id_requires_authentication():
    response = TestClient(app).get(
        "/api/applicants/3f7c1a52-1d44-4a5e-9c3b-9f2a7e6d5c41/interview"
    )
    assert response.status_code == 401
