"""
RECRUIT.AI — Analytics Router
GET /analytics/dashboard — headline counts and distributions
"""

from collections import Counter
from datetime import datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends

from app.models.documents import Applicant, Drive, DriveStatus, Organisation
from app.models.schemas import AnalyticsResponse, ChartDataPoint
from app.services.auth_service import get_current_org

router = APIRouter(prefix="/analytics", tags=["Analytics"])

SCORE_BUCKETS = ["0-20", "21-40", "41-60", "61-80", "81-100"]
# $bucket lower bounds, one per label above. Each bucket includes its upper
# edge, so 20 lands in "0-20" and 21 in "21-40".
_BUCKET_BOUNDARIES = [float("-inf"), 21, 41, 61, 81, float("inf")]

# Only completed interviews count towards scores; one still in progress has a
# score of 0 that would drag the average down. Matched on type rather than
# "not null" so an applicant with no interview at all can never slip through.
_COMPLETED = {"$match": {"interview.ended_at": {"$type": "date"}}}
_SCORE = {"$ifNull": ["$interview.total_score", 0]}


def _pipeline(trend_start: datetime) -> list[dict]:
    """
    Every applicant figure in one round trip. The counting happens in the
    database, so nothing but the handful of result rows reaches the API.
    """
    return [
        {
            "$facet": {
                "total": [{"$count": "n"}],
                "interviews": [
                    _COMPLETED,
                    {"$group": {"_id": None, "n": {"$sum": 1}, "score": {"$sum": _SCORE}}},
                ],
                "scores": [
                    _COMPLETED,
                    {
                        "$bucket": {
                            "groupBy": _SCORE,
                            "boundaries": _BUCKET_BOUNDARIES,
                            "output": {"n": {"$sum": 1}},
                        }
                    },
                ],
                "domains": [{"$group": {"_id": "$primary_domain", "n": {"$sum": 1}}}],
                "statuses": [{"$group": {"_id": "$status", "n": {"$sum": 1}}}],
                "trend": [
                    {"$match": {"applied_at": {"$gte": trend_start}}},
                    {
                        "$group": {
                            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$applied_at"}},
                            "n": {"$sum": 1},
                        }
                    },
                ],
            }
        }
    ]


def _count(rows: list[dict]) -> int:
    return rows[0]["n"] if rows else 0


@router.get("/dashboard", response_model=AnalyticsResponse)
async def get_dashboard_analytics(org: Organisation = Depends(get_current_org)):
    # Last seven days, including days with no applications so the chart has an
    # unbroken axis. Days are UTC calendar days.
    now = datetime.now(timezone.utc)
    days = [(now - timedelta(days=offset)).date() for offset in range(6, -1, -1)]
    trend_start = datetime.combine(days[0], time.min, tzinfo=timezone.utc)

    total_drives = await Drive.find(Drive.org_id == org.id).count()
    active_drives = await Drive.find(
        Drive.org_id == org.id, Drive.status == DriveStatus.ACTIVE
    ).count()

    result = await (
        Applicant.find(Applicant.org_id == org.id)
        .aggregate(_pipeline(trend_start))
        .to_list()
    )
    facets = result[0] if result else {}

    interviews = facets.get("interviews") or [{"n": 0, "score": 0}]
    total_interviews = interviews[0]["n"]
    avg_score = (
        int(interviews[0]["score"] / total_interviews) if total_interviews else 0
    )

    # $bucket labels each row with its lower boundary.
    by_lower = {row["_id"]: row["n"] for row in facets.get("scores", [])}
    score_dist = [
        ChartDataPoint(name=label, value=by_lower.get(lower, 0))
        for label, lower in zip(SCORE_BUCKETS, _BUCKET_BOUNDARIES)
    ]

    # Grouped in the database; only the relabelling happens here, on one row
    # per distinct value.
    domains: Counter[str] = Counter()
    for row in facets.get("domains", []):
        domains[row["_id"] or "Unknown"] += row["n"]
    top = domains.most_common(5)
    domain_dist = [ChartDataPoint(name=k, value=v) for k, v in top]
    if len(domains) > 5:
        other = sum(v for k, v in domains.items() if k not in dict(top))
        domain_dist.append(ChartDataPoint(name="Other", value=other))

    status_dist = [
        ChartDataPoint(name=row["_id"].replace("_", " ").title(), value=row["n"])
        for row in facets.get("statuses", [])
    ]

    per_day = {row["_id"]: row["n"] for row in facets.get("trend", [])}
    trend = [
        ChartDataPoint(name=day.strftime("%b %d"), value=per_day.get(day.isoformat(), 0))
        for day in days
    ]

    return AnalyticsResponse(
        total_drives=total_drives,
        active_drives=active_drives,
        total_applicants=_count(facets.get("total", [])),
        total_interviews=total_interviews,
        avg_score=avg_score,
        score_distribution=score_dist,
        domain_distribution=domain_dist,
        status_distribution=status_dist,
        recent_trend=trend,
    )
