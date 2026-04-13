"""
RECRUIT.AI — Analytics Router
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.database import Drive, Applicant, Interview, Organisation
from app.models.schemas import AnalyticsResponse, ChartDataPoint
from app.services.auth_service import get_current_org

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard", response_model=AnalyticsResponse)
def get_dashboard_analytics(
    org: Organisation = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    # Get all drives for this org
    drives = db.query(Drive).filter(Drive.org_id == org.id).all()
    drive_ids = [d.id for d in drives]
    
    total_drives = len(drives)
    active_drives = sum(1 for d in drives if d.status.value == "active")
    
    # Get applicants
    applicants = db.query(Applicant).filter(Applicant.drive_id.in_(drive_ids)).all() if drive_ids else []
    total_applicants = len(applicants)
    
    # Get interviews
    applicant_ids = [a.id for a in applicants]
    interviews = db.query(Interview).filter(Interview.applicant_id.in_(applicant_ids), Interview.ended_at.is_not(None)).all() if applicant_ids else []
    total_interviews = len(interviews)
    
    avg_score = 0
    if interviews:
        avg_score = int(sum(i.total_score or 0 for i in interviews) / total_interviews)
        
    # Score distribution (ranges: 0-20, 21-40, 41-60, 61-80, 81-100)
    scores = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    for i in interviews:
        s = i.total_score or 0
        if s <= 20: scores["0-20"] += 1
        elif s <= 40: scores["21-40"] += 1
        elif s <= 60: scores["41-60"] += 1
        elif s <= 80: scores["61-80"] += 1
        else: scores["81-100"] += 1
        
    score_dist = [ChartDataPoint(name=k, value=v) for k, v in scores.items()]
    
    # Domain distribution
    domains: Dict[str, int] = {}
    for a in applicants:
        dom = a.primary_domain or "Unknown"
        domains[dom] = domains.get(dom, 0) + 1
    # Sort top 5 and group rest as 'Other'
    sorted_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)
    domain_dist = [ChartDataPoint(name=k, value=v) for k, v in sorted_domains[:5]]
    if len(sorted_domains) > 5:
        other_val = sum(v for k, v in sorted_domains[5:])
        domain_dist.append(ChartDataPoint(name="Other", value=other_val))
        
    # Status distribution
    statuses: Dict[str, int] = {}
    for a in applicants:
        st = a.status.value.replace("_", " ").title()
        statuses[st] = statuses.get(st, 0) + 1
    status_dist = [ChartDataPoint(name=k, value=v) for k, v in statuses.items()]
    
    # Recent trend (last 7 days applicants)
    now = datetime.now(timezone.utc)
    trends: Dict[str, int] = {}
    for days_ago in range(6, -1, -1):
        d = (now - timedelta(days=days_ago)).strftime("%b %d")
        trends[d] = 0
        
    for a in applicants:
        if a.applied_at:
            delta = now - a.applied_at
            if delta.days <= 6 and delta.days >= 0:
                d = a.applied_at.strftime("%b %d")
                if d in trends:
                    trends[d] += 1
                    
    trend_dist = [ChartDataPoint(name=k, value=v) for k, v in trends.items()]

    return AnalyticsResponse(
        total_drives=total_drives,
        active_drives=active_drives,
        total_applicants=total_applicants,
        total_interviews=total_interviews,
        avg_score=avg_score,
        score_distribution=score_dist,
        domain_distribution=domain_dist,
        status_distribution=status_dist,
        recent_trend=trend_dist,
    )
