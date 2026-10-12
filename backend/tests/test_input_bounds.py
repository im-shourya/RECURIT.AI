"""
Tests for the size limits on free text.

Answers and submissions are embedded in the applicant document, which MongoDB
caps at 16MB. Without a bound, a handful of very large requests could push one
candidate's record past that cap and leave it permanently unwritable.
"""

from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.documents import Applicant, Interview
from app.models.schemas import (
    ApplyRequest,
    DriveCreateRequest,
    DriveUpdateRequest,
    InterviewAnswerRequest,
    OrgProfileUpdate,
    OrgRegisterRequest,
    SubmissionCreateRequest,
)
from app.routers.interviews import MAX_TRANSCRIPT_ENTRIES, submit_answer

BIG = "x" * 100_000


@pytest.mark.parametrize(
    "build",
    [
        lambda: InterviewAnswerRequest(question_text="q", answer_text=BIG, round_name="intro"),
        lambda: InterviewAnswerRequest(question_text=BIG, answer_text="a", round_name="intro"),
        lambda: SubmissionCreateRequest(description=BIG),
        lambda: DriveCreateRequest(
            name="Drive", domain="Web", task_type="task", task_description=BIG,
            apply_deadline=date.today(),
        ),
        lambda: DriveUpdateRequest(task_description=BIG),
        lambda: OrgProfileUpdate(description=BIG),
        lambda: OrgRegisterRequest(
            name="Club", email="c@example.com", password="long-enough", description=BIG
        ),
    ],
)
def test_oversized_text_is_rejected(build):
    with pytest.raises(ValidationError):
        build()


def _apply(**fields) -> ApplyRequest:
    return ApplyRequest(name="Alex", email="alex@example.com", **fields)


def test_skills_are_bounded_in_count_and_length():
    with pytest.raises(ValidationError):
        _apply(skills=[f"skill-{i}" for i in range(31)])
    with pytest.raises(ValidationError):
        _apply(skills=["x" * 51])
    assert len(_apply(skills=["React"] * 30).skills) == 30


def test_ordinary_input_is_unaffected():
    assert InterviewAnswerRequest(
        question_text="Tell me about yourself.",
        answer_text="A few paragraphs. " * 200,
        round_name="intro",
    )
    assert _apply(reg_no="21BCE1234", primary_domain="Web Development", skills=["React"])


async def test_answers_stop_once_the_transcript_is_full(applicant):
    applicant.interview = Interview(
        token="full-transcript",
        started_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        transcript=[
            {"round": "intro", "question": "q", "answer": "a"}
        ] * MAX_TRANSCRIPT_ENTRIES,
    )
    await applicant.save()

    with pytest.raises(HTTPException) as exc:
        await submit_answer(
            "full-transcript",
            InterviewAnswerRequest(question_text="q", answer_text="a", round_name="domain"),
        )

    assert exc.value.status_code == 409
    stored = await Applicant.get(applicant.id)
    assert len(stored.interview.transcript) == MAX_TRANSCRIPT_ENTRIES
