"""
Tests for the dashboard analytics.

These run the real query against the in-process database, so they pin down
what the dashboard shows rather than how it is computed.
"""

from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.documents import (
    Applicant,
    ApplicantStatus,
    Drive,
    DriveStatus,
    Interview,
    TaskType,
)
from app.routers.analytics import get_dashboard_analytics


async def _add_drive(org, token: str, status=DriveStatus.ACTIVE) -> Drive:
    record = Drive(
        org_id=org.id,
        name=token,
        domain="Web",
        task_type=TaskType.GITHUB,
        apply_deadline=date.today() + timedelta(days=7),
        link_token=token,
        status=status,
    )
    await record.insert()
    return record


async def _add_applicant(
    drive: Drive,
    n: int,
    *,
    domain: str = "Web",
    status=ApplicantStatus.APPLIED,
    applied_days_ago: int = 0,
    score: int | None = None,
    finished: bool = True,
) -> Applicant:
    interview = None
    if score is not None:
        interview = Interview(
            token=f"iv-{drive.link_token}-{n}",
            ended_at=datetime.now(timezone.utc) if finished else None,
            total_score=score,
        )
    record = Applicant(
        drive_id=drive.id,
        org_id=drive.org_id,
        name=f"Candidate {n}",
        email=f"c{n}@{drive.link_token}.test",
        submit_token=f"st-{drive.link_token}-{n}",
        primary_domain=domain,
        status=status,
        applied_at=datetime.now(timezone.utc) - timedelta(days=applied_days_ago),
        interview=interview,
    )
    await record.insert()
    return record


def _as_dict(points) -> dict[str, int]:
    return {p.name: p.value for p in points}


async def test_an_empty_organisation_reports_zeroes(org):
    result = await get_dashboard_analytics(org=org)

    assert result.total_drives == 0
    assert result.active_drives == 0
    assert result.total_applicants == 0
    assert result.total_interviews == 0
    assert result.avg_score == 0
    assert _as_dict(result.score_distribution) == {
        "0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0,
    }
    assert result.domain_distribution == []
    assert result.status_distribution == []
    assert len(result.recent_trend) == 7
    assert all(p.value == 0 for p in result.recent_trend)


async def test_headline_counts(org):
    live = await _add_drive(org, "live")
    await _add_drive(org, "closed", status=DriveStatus.CLOSED)
    await _add_applicant(live, 1, score=90)
    await _add_applicant(live, 2, score=30)
    await _add_applicant(live, 3, score=0, finished=False)
    await _add_applicant(live, 4)

    result = await get_dashboard_analytics(org=org)

    assert result.total_drives == 2
    assert result.active_drives == 1
    assert result.total_applicants == 4
    # An interview still in progress is not counted, and its 0 does not drag
    # the average down.
    assert result.total_interviews == 2
    assert result.avg_score == 60


async def test_average_score_rounds_down(org):
    drive = await _add_drive(org, "d")
    for n, score in enumerate([50, 51, 51]):
        await _add_applicant(drive, n, score=score)

    assert (await get_dashboard_analytics(org=org)).avg_score == 50


async def test_score_buckets_include_their_upper_edge(org):
    drive = await _add_drive(org, "d")
    for n, score in enumerate([0, 20, 21, 40, 41, 60, 61, 80, 81, 100]):
        await _add_applicant(drive, n, score=score)

    result = await get_dashboard_analytics(org=org)

    assert _as_dict(result.score_distribution) == {
        "0-20": 2, "21-40": 2, "41-60": 2, "61-80": 2, "81-100": 2,
    }
    assert [p.name for p in result.score_distribution] == [
        "0-20", "21-40", "41-60", "61-80", "81-100",
    ]


async def test_domains_keep_the_top_five_and_fold_the_rest_into_other(org):
    drive = await _add_drive(org, "d")
    n = 0
    for domain, count in [("A", 6), ("B", 5), ("C", 4), ("D", 3), ("E", 2), ("F", 1), ("G", 1)]:
        for _ in range(count):
            n += 1
            await _add_applicant(drive, n, domain=domain)

    result = await get_dashboard_analytics(org=org)

    assert [(p.name, p.value) for p in result.domain_distribution] == [
        ("A", 6), ("B", 5), ("C", 4), ("D", 3), ("E", 2), ("Other", 2),
    ]


async def test_a_missing_domain_is_reported_as_unknown(org):
    drive = await _add_drive(org, "d")
    await _add_applicant(drive, 1, domain="")
    await _add_applicant(drive, 2, domain="")

    result = await get_dashboard_analytics(org=org)

    assert _as_dict(result.domain_distribution) == {"Unknown": 2}


async def test_statuses_are_labelled_for_display(org):
    drive = await _add_drive(org, "d")
    await _add_applicant(drive, 1, status=ApplicantStatus.APPLIED)
    await _add_applicant(drive, 2, status=ApplicantStatus.APPLIED)
    await _add_applicant(drive, 3, status=ApplicantStatus.INTERVIEW_SENT)

    result = await get_dashboard_analytics(org=org)

    assert _as_dict(result.status_distribution) == {"Applied": 2, "Interview Sent": 1}


async def test_trend_covers_the_last_seven_days(org):
    drive = await _add_drive(org, "d")
    await _add_applicant(drive, 1, applied_days_ago=0)
    await _add_applicant(drive, 2, applied_days_ago=0)
    await _add_applicant(drive, 3, applied_days_ago=3)
    await _add_applicant(drive, 4, applied_days_ago=30)

    result = await get_dashboard_analytics(org=org)
    today = datetime.now(timezone.utc)

    assert len(result.recent_trend) == 7
    assert result.recent_trend[-1].name == today.strftime("%b %d")
    trend = _as_dict(result.recent_trend)
    assert trend[today.strftime("%b %d")] == 2
    assert trend[(today - timedelta(days=3)).strftime("%b %d")] == 1
    assert sum(trend.values()) == 3


async def test_another_organisations_data_is_never_counted(org, other_org):
    ours = await _add_drive(org, "ours")
    theirs = await _add_drive(other_org, "theirs")
    await _add_applicant(ours, 1, score=80, domain="Web")
    await _add_applicant(theirs, 2, score=10, domain="ML")

    result = await get_dashboard_analytics(org=org)

    assert result.total_drives == 1
    assert result.total_applicants == 1
    assert result.avg_score == 80
    assert _as_dict(result.domain_distribution) == {"Web": 1}
