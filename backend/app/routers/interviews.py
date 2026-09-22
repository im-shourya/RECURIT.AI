"""
RECRUIT.AI — Interview Router
GET  /interview/{token}         — Validate token, return interview config
POST /interview/{token}/start   — Begin session, start recording
POST /interview/{token}/answer  — Submit answer turn, get next question
POST /interview/{token}/end     — End session, compute score, upload recording
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import (
    APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status,
)
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.database import Interview, Applicant, ApplicantStatus, Drive, Organisation
from app.services.auth_service import get_current_org
from app.services.email_service import send_interview_completed_email
from app.services import storage_service
from app.config import get_settings

settings = get_settings()
log = logging.getLogger("recruit.interviews")
from app.models.schemas import (
    InterviewConfigResponse,
    InterviewStartResponse,
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    InterviewEndRequest,
    InterviewEndResponse,
    InterviewDetailResponse,
)

router = APIRouter(prefix="/interview", tags=["Interview"])


def _active_interview(token: str, db: Session) -> Interview:
    """
    Look up an interview by token and reject links that are no longer usable.

    expires_at is nullable: rows created before expiry existed have no value
    and are treated as "never given an expiry" rather than as expired, so the
    change does not invalidate interviews already in flight.
    """
    interview = db.query(Interview).filter(Interview.token == token).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found or link is invalid")

    if interview.ended_at:
        raise HTTPException(status_code=400, detail="This interview has already been completed")

    if interview.expires_at and interview.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="This interview link has expired")

    return interview


# ──────────────────────────────────────────────
# VALIDATE TOKEN & GET CONFIG
# ──────────────────────────────────────────────
@router.get("/{token}", response_model=InterviewConfigResponse)
def get_interview_config(token: str, db: Session = Depends(get_db)):
    interview = _active_interview(token, db)

    applicant = interview.applicant
    drive = applicant.drive

    # Fetch RepoLens analysis if available
    repolens_data = {}
    if applicant.submission and applicant.submission.repolens_analysis:
        repolens_data = applicant.submission.repolens_analysis

    return InterviewConfigResponse(
        interview_id=interview.id,
        applicant_name=applicant.name,
        drive_name=drive.name,
        domain=drive.domain,
        question_level=drive.question_level.value,
        task_type=drive.task_type.value,
        repolens_analysis=repolens_data,
        max_duration_seconds=300,
    )


# ──────────────────────────────────────────────
# START INTERVIEW SESSION
# ──────────────────────────────────────────────
@router.post("/{token}/start", response_model=InterviewStartResponse)
def start_interview(token: str, db: Session = Depends(get_db)):
    interview = _active_interview(token, db)

    if interview.started_at:
        raise HTTPException(status_code=400, detail="Interview has already started")

    interview.started_at = datetime.now(timezone.utc)
    interview.transcript = []

    applicant = interview.applicant
    applicant.status = ApplicantStatus.INTERVIEWED
    db.commit()
    db.refresh(interview)

    return InterviewStartResponse(interview_id=interview.id)


# ──────────────────────────────────────────────
# SUBMIT AN ANSWER TURN
# ──────────────────────────────────────────────
@router.post("/{token}/answer", response_model=InterviewAnswerResponse)
def submit_answer(
    token: str,
    body: InterviewAnswerRequest,
    db: Session = Depends(get_db),
):
    interview = _active_interview(token, db)

    if not interview.started_at:
        raise HTTPException(status_code=400, detail="Interview has not started yet")

    # Append to transcript
    transcript = interview.transcript or []
    transcript.append({
        "round": body.round_name,
        "question": body.question_text,
        "answer": body.answer_text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    interview.transcript = transcript
    db.commit()

    # ── Generate next question ──
    # In production, this calls the AI service. For now, return structured placeholders.
    round_questions = {
        "intro": [
            "Tell me about yourself and your background.",
            "What motivates you to join this club?",
            "What are your key strengths?",
        ],
        "project": [
            "Walk me through the architecture of your project.",
            "What was the most challenging part of building this?",
            "How would you improve this project if you had more time?",
        ],
        "domain": [
            "Explain a core concept in your primary domain.",
            "How would you approach solving a real-world problem in this area?",
            "What recent trends in this field are you following?",
        ],
    }

    questions = round_questions.get(body.round_name, [])
    current_count = len([t for t in transcript if t["round"] == body.round_name])

    if current_count < len(questions):
        next_q = questions[current_count] if current_count < len(questions) else ""
        is_last = False
    else:
        # Move to next round or end
        round_order = ["intro", "project", "domain"]
        current_idx = round_order.index(body.round_name) if body.round_name in round_order else 2
        if current_idx < 2:
            next_round = round_order[current_idx + 1]
            next_q = round_questions[next_round][0]
            return InterviewAnswerResponse(
                next_question=next_q,
                round_name=next_round,
                is_last=False,
            )
        else:
            return InterviewAnswerResponse(
                next_question="Thank you! That concludes your interview.",
                round_name="domain",
                is_last=True,
            )

    return InterviewAnswerResponse(
        next_question=next_q,
        round_name=body.round_name,
        is_last=is_last,
    )


# ──────────────────────────────────────────────
# END INTERVIEW SESSION
# ──────────────────────────────────────────────
@router.post("/{token}/end", response_model=InterviewEndResponse)
def end_interview(
    token: str,
    body: InterviewEndRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    interview = db.query(Interview).filter(Interview.token == token).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview.ended_at:
        raise HTTPException(status_code=400, detail="Interview already ended")

    interview.ended_at = datetime.now(timezone.utc)
    # body.recording_url is deliberately ignored: it let the client decide
    # what the recording pointed at. Recordings arrive via
    # POST /interview/{token}/recording, which stores them server-side.

    # ── Compute scores ──
    # In production, this calls the AI scoring engine (BERT embeddings, rubric evaluation).
    # For now, generate placeholder scores based on transcript length.
    transcript = interview.transcript or []
    intro_answers = [t for t in transcript if t["round"] == "intro"]
    project_answers = [t for t in transcript if t["round"] == "project"]
    domain_answers = [t for t in transcript if t["round"] == "domain"]

    # Simple scoring: more complete answers = higher score (placeholder)
    interview.score_intro = min(len(intro_answers) * 25, 100)
    interview.score_project = min(len(project_answers) * 25, 100)
    interview.score_domain = min(len(domain_answers) * 25, 100)
    interview.total_score = (interview.score_intro + interview.score_project + interview.score_domain) // 3

    db.commit()
    db.refresh(interview)

    # Tell the recruiter. Without this they only learn an interview finished
    # by opening the dashboard and looking.
    applicant = interview.applicant
    org = applicant.drive.organisation
    if org.notify_on_interview and org.email:
        background_tasks.add_task(
            send_interview_completed_email,
            to_email=org.email,
            to_name=org.name,
            applicant_name=applicant.name,
            drive_name=applicant.drive.name,
            total_score=interview.total_score or 0,
            review_url=f"{settings.FRONTEND_URL}/dashboard/drives/{applicant.drive_id}",
        )

    return InterviewEndResponse(
        total_score=interview.total_score,
        score_intro=interview.score_intro,
        score_project=interview.score_project,
        score_domain=interview.score_domain,
    )


# ──────────────────────────────────────────────
# GET FULL INTERVIEW DETAIL (for org dashboard)
# ──────────────────────────────────────────────
@router.get("/{token}/detail", response_model=InterviewDetailResponse)
def get_interview_detail(
    token: str,
    org: Organisation = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    """
    Full interview detail for the recruiting organisation.

    This was unauthenticated despite its own docstring saying "for org
    dashboard": anyone holding an interview token — the candidate, or anyone
    they forwarded the link to — could read the transcript, the scores and the
    malpractice flags. It now requires a signed-in organisation, and the
    interview must belong to one of that organisation's drives.
    """
    interview = (
        db.query(Interview)
        .join(Applicant, Interview.applicant_id == Applicant.id)
        .join(Drive, Applicant.drive_id == Drive.id)
        .filter(Interview.token == token, Drive.org_id == org.id)
        .first()
    )
    if not interview:
        # Same 404 whether the token is unknown or belongs to another
        # organisation, so this cannot be used to probe for valid tokens.
        raise HTTPException(status_code=404, detail="Interview not found")

    applicant = interview.applicant
    drive = applicant.drive

    return InterviewDetailResponse(
        id=interview.id,
        token=interview.token,
        started_at=interview.started_at,
        ended_at=interview.ended_at,
        recording_url=interview.recording_url or "",
        transcript=interview.transcript or [],
        score_intro=interview.score_intro,
        score_project=interview.score_project,
        score_domain=interview.score_domain,
        total_score=interview.total_score,
        malpractice_flags=interview.malpractice_flags or [],
        applicant_name=applicant.name,
        drive_name=drive.name,
    )


# ──────────────────────────────────────────────
# UPLOAD THE RECORDING
# ──────────────────────────────────────────────
@router.post("/{token}/recording", status_code=status.HTTP_204_NO_CONTENT)
async def upload_recording(
    token: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Store the interview recording.

    Previously `recording_url` was accepted as a string on /end and saved
    verbatim, so the client decided what the recording pointed at — it could
    be any URL, or nothing. The file now goes to object storage under a
    server-generated key and the stored value is that key.

    Deliberately not gated on the expiry check: a candidate finishing right on
    the boundary must still be able to upload what they just recorded.
    """
    interview = db.query(Interview).filter(Interview.token == token).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if not storage_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Recording upload is unavailable: object storage is not configured",
        )

    try:
        key = storage_service.upload_recording(
            interview_id=interview.id,
            filename=file.filename or "",
            stream=file.file,
        )
    except storage_service.UnsupportedFileType as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except storage_service.UploadTooLarge as exc:
        raise HTTPException(status_code=413, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except storage_service.StorageError as exc:
        log.error(
            "recording upload failed",
            extra={"interview_id": str(interview.id), "error": str(exc)},
        )
        raise HTTPException(status_code=502, detail="Upload failed, please try again")

    interview.recording_url = key
    db.commit()
    return None
