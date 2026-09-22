"""
RECRUIT.AI — Analytics Router
GET /analytics/dashboard — headline counts and distributions
"""

from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from app.models.documents import Applicant, Drive, DriveStatus, Organisation
from app.models.schemas import AnalyticsResponse, ChartDataPoint
from app.services.auth_service import get_current_org

router = APIRouter(prefix="/analytics", tags=["Analytics"])

SCORE_BUCKETS = ["0-20", "21-40", "41-60", "61-80", "81-100"]


def _bucket(score: int) -> str:
    if score <= 20:
        return "0-20"
    if score <= 40:
        return "21-40"
    if score <= 60:
        return "41-60"
    if score <= 80:
        return "61-80"
    return "81-100"


@router.get("/dashboard", response_model=AnalyticsResponse)
async def get_dashboard_analytics(org: Organisation = Depends(get_current_org)):
    drives = await Drive.find(Drive.org_id == org.id).to_list()
    applicants = await Applicant.find(Applicant.org_id == org.id).to_list()

    # Only completed interviews count towards scores; one still in progress
    # has a score of 0 that would drag the average down.
    completed = [
        a.interview for a in applicants if a.interview and a.interview.ended_at
    ]

    avg_score = (
        int(sum(i.total_score or 0 for i in completed) / len(completed))
        if completed
        else 0
    )

    scores = Counter(_bucket(i.total_score or 0) for i in completed)
    score_dist = [ChartDataPoint(name=b, value=scores.get(b, 0)) for b in SCORE_BUCKETS]

    domains = Counter(a.primary_domain or "Unknown" for a in applicants)
    top = domains.most_common(5)
    domain_dist = [ChartDataPoint(name=k, value=v) for k, v in top]
    if len(domains) > 5:
        other = sum(v for k, v in domains.items() if k not in dict(top))
        domain_dist.append(ChartDataPoint(name="Other", value=other))

    statuses = Counter(a.status.value.replace("_", " ").title() for a in applicants)
    status_dist = [ChartDataPoint(name=k, value=v) for k, v in statuses.items()]

    # Last seven days, including days with no applications so the chart has an
    # unbroken axis.
    now = datetime.now(timezone.utc)
    trends = {
        (now - timedelta(days=offset)).strftime("%b %d"): 0
        for offset in range(6, -1, -1)
    }
    for a in applicants:
        applied_at = a.applied_at
        if not applied_at:
            continue
        if applied_at.tzinfo is None:
            applied_at = applied_at.replace(tzinfo=timezone.utc)
        if 0 <= (now - applied_at).days <= 6:
            key = applied_at.strftime("%b %d")
            if key in trends:
                trends[key] += 1

    return AnalyticsResponse(
        total_drives=len(drives),
        active_drives=sum(1 for d in drives if d.status == DriveStatus.ACTIVE),
        total_applicants=len(applicants),
        total_interviews=len(completed),
        avg_score=avg_score,
        score_distribution=score_dist,
        domain_distribution=domain_dist,
        status_distribution=status_dist,
        recent_trend=[ChartDataPoint(name=k, value=v) for k, v in trends.items()],
    )
