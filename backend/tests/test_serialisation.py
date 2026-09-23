"""
Response serialisation against real documents.

Two 500s reached a running server because nothing exercised the path from a
stored document through the response model:

  - ApplicantResponse.interview required an `id`, but the interview is
    embedded now and has no identity of its own
  - DriveResponse required org_id, which the serialiser did not pass

Both are the same class of bug: the response schemas still described the
relational shape. These tests build documents, run them through the real
serialisers, and validate the result.
"""

from datetime import date, timedelta

from app.models.documents import (
    Applicant,
    Drive,
    EmailLogEntry,
    EmailType,
    Interview,
    Submission,
    TaskType,
)
from app.routers.applicant_admin import applicant_to_response
from app.routers.drives import _to_response as drive_to_response


# ──────────────────────────────────────────────
# Applicant
# ──────────────────────────────────────────────
async def test_applicant_without_interview_serialises(applicant):
    out = applicant_to_response(applicant)
    assert out.id == applicant.id
    assert out.interview is None
    assert out.submission is None


async def test_applicant_with_embedded_interview_serialises(applicant):
    """
    The embedded interview has no id of its own. This raised
    "interview.id Field required" against real data.
    """
    applicant.interview = Interview(
        token="tok-abc", score_intro=75, score_project=80,
        score_domain=90, total_score=81,
    )
    await applicant.save()

    out = applicant_to_response(applicant)
    assert out.interview is not None
    assert out.interview.token == "tok-abc"
    assert out.interview.total_score == 81
    # 1:1 with the applicant, so the applicant's id identifies it — the same
    # value /interview/{token}/detail reports.
    assert out.interview.id == applicant.id


async def test_applicant_with_submission_serialises(applicant):
    applicant.submission = Submission(
        github_url="https://github.com/x/y", description="notes",
        repolens_analysis={"stars": 3},
    )
    await applicant.save()

    out = applicant_to_response(applicant)
    assert out.submission is not None
    assert out.submission.github_url == "https://github.com/x/y"
    assert out.submission.repolens_analysis == {"stars": 3}


async def test_applicant_tolerates_missing_optional_fields(drive):
    """Documents migrated from PostgreSQL may have nothing in these."""
    bare = Applicant(
        drive_id=drive.id, org_id=drive.org_id,
        name="Bare", email="bare@example.com",
    )
    await bare.insert()

    out = applicant_to_response(bare)
    assert out.reg_no == ""
    assert out.skills == []
    assert out.github_url == ""


async def test_email_logs_do_not_break_serialisation(applicant):
    applicant.email_logs.append(EmailLogEntry(type=EmailType.APPLIED))
    await applicant.save()
    applicant_to_response(applicant)


# ──────────────────────────────────────────────
# Drive
# ──────────────────────────────────────────────
async def test_drive_serialises_with_org_id(drive):
    """org_id was required by the schema and omitted by the serialiser."""
    out = drive_to_response(drive, applicant_count=3)
    assert out.org_id == drive.org_id
    assert out.id == drive.id
    assert out.applicant_count == 3


async def test_drive_without_task_deadline_serialises(org):
    """A GitHub drive has no task deadline."""
    record = Drive(
        org_id=org.id, name="GH", domain="Web", task_type=TaskType.GITHUB,
        apply_deadline=date.today() + timedelta(days=3), link_token="gh-token",
    )
    await record.insert()

    out = drive_to_response(record)
    assert out.task_deadline is None
    assert out.task_type == "github"


async def test_drive_enums_serialise_as_strings(drive):
    """The API contract is strings, not enum objects."""
    out = drive_to_response(drive)
    assert isinstance(out.task_type, str)
    assert isinstance(out.status, str)
    assert isinstance(out.question_level, str)
