"""
RECRUIT.AI — Interview Router
GET  /interview/{token}           — Validate token, return config
POST /interview/{token}/start     — Begin the session
POST /interview/{token}/answer    — Submit an answer, get the next question
POST /interview/{token}/end       — End and score
POST /interview/{token}/recording — Upload the recording
GET  /interview/{token}/detail    — Full detail, organisation only

The interview is embedded in the applicant document, so every lookup here is
a query on the parent collection by the indexed nested field.
"""

import logging
from datetime import datetime, timezone

from fastapi import (
    APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status,
)

from app.config import get_settings
from app.models.documents import (
    Applicant,
    ApplicantStatus,
    Drive,
    Organisation,
    User,
)
from app.models.schemas import (
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    InterviewConfigResponse,
    InterviewDetailResponse,
    InterviewEndRequest,
    InterviewEndResponse,
    InterviewStartResponse,
)
from app.services import storage_service
from app.services.auth_service import get_current_org
from app.services.rate_limit import RateLimit
from app.services.email_service import send_interview_completed_email

settings = get_settings()
log = logging.getLogger("recruit.interviews")
router = APIRouter(prefix="/interview", tags=["Interview"])


async def _by_token(token: str) -> Applicant:
    applicant = await Applicant.find_one({"interview.token": token})
    if not applicant or not applicant.interview:
        raise HTTPException(
            status_code=404, detail="Interview not found or link is invalid"
        )
    return applicant


async def _active(token: str) -> Applicant:
    """
    Look up an interview and reject links that are no longer usable.

    expires_at is optional: interviews created before expiry existed have none
    and are treated as "no expiry set" rather than expired, so the change does
    not invalidate interviews already in flight.
    """
    applicant = await _by_token(token)
    interview = applicant.interview

    if interview.ended_at:
        raise HTTPException(
            status_code=400, detail="This interview has already been completed"
        )

    if interview.expires_at:
        expires_at = interview.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="This interview link has expired")

    return applicant


# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
@router.get(
    "/{token}",
    response_model=InterviewConfigResponse,
    dependencies=[Depends(RateLimit("interview_config", limit=60, window_seconds=3600,
                                    key_param="token"))],
)
async def get_interview_config(token: str):
    applicant = await _active(token)
    drive = await Drive.get(applicant.drive_id)
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    repolens = {}
    if applicant.submission and applicant.submission.repolens_analysis:
        repolens = applicant.submission.repolens_analysis

    return InterviewConfigResponse(
        interview_id=applicant.id,
        applicant_name=applicant.name,
        drive_name=drive.name,
        domain=drive.domain,
        question_level=drive.question_level.value,
        task_type=drive.task_type.value,
        repolens_analysis=repolens,
        max_duration_seconds=300,
    )


# ──────────────────────────────────────────────
# START
# ──────────────────────────────────────────────
@router.post(
    "/{token}/start",
    response_model=InterviewStartResponse,
    dependencies=[Depends(RateLimit("interview_start", limit=10, window_seconds=3600,
                                    key_param="token"))],
)
async def start_interview(token: str):
    applicant = await _active(token)

    if applicant.interview.started_at:
        raise HTTPException(status_code=400, detail="Interview has already started")

    applicant.interview.started_at = datetime.now(timezone.utc)
    applicant.interview.transcript = []
    applicant.status = ApplicantStatus.INTERVIEWED
    await applicant.save()

    return InterviewStartResponse(interview_id=applicant.id)


# ──────────────────────────────────────────────
# ANSWER
# ──────────────────────────────────────────────
@router.post(
    "/{token}/answer",
    response_model=InterviewAnswerResponse,
    # An interview is nine questions. This allows retries and a reconnect
    # without letting anyone append to a transcript indefinitely.
    dependencies=[Depends(RateLimit("interview_answer", limit=60, window_seconds=3600,
                                    key_param="token"))],
)
async def submit_answer(token: str, body: InterviewAnswerRequest):
    applicant = await _active(token)

    if not applicant.interview.started_at:
        raise HTTPException(status_code=400, detail="Interview has not started yet")

    transcript = applicant.interview.transcript or []
    transcript.append({
        "round": body.round_name,
        "question": body.question_text,
        "answer": body.answer_text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    applicant.interview.transcript = transcript
    await applicant.save()

    # ── Next question ──
    # Still the placeholder set: these are fixed strings, not generated, and
    # the scoring below counts answers rather than reading them. Wiring the AI
    # service is tracked separately.
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
    asked = len([t for t in transcript if t["round"] == body.round_name])

    if asked < len(questions):
        return InterviewAnswerResponse(
            next_question=questions[asked], round_name=body.round_name, is_last=False
        )

    order = ["intro", "project", "domain"]
    index = order.index(body.round_name) if body.round_name in order else 2
    if index < 2:
        next_round = order[index + 1]
        return InterviewAnswerResponse(
            next_question=round_questions[next_round][0],
            round_name=next_round,
            is_last=False,
        )

    return InterviewAnswerResponse(
        next_question="Thank you! That concludes your interview.",
        round_name="domain",
        is_last=True,
    )


# ──────────────────────────────────────────────
# END
# ──────────────────────────────────────────────
@router.post(
    "/{token}/end",
    response_model=InterviewEndResponse,
    dependencies=[Depends(RateLimit("interview_end", limit=10, window_seconds=3600,
                                    key_param="token"))],
)
async def end_interview(
    token: str,
    body: InterviewEndRequest,
    background_tasks: BackgroundTasks,
):
    """
    Deliberately does not apply the expiry check: a candidate whose link
    expires mid-interview must still be able to finish and be scored.
    """
    applicant = await _by_token(token)
    interview = applicant.interview

    if interview.ended_at:
        raise HTTPException(status_code=400, detail="Interview already ended")

    interview.ended_at = datetime.now(timezone.utc)
    # body.recording_url is ignored: it let the client decide what the
    # recording pointed at. Recordings arrive via /recording instead.

    transcript = interview.transcript or []
    intro = [t for t in transcript if t["round"] == "intro"]
    project = [t for t in transcript if t["round"] == "project"]
    domain = [t for t in transcript if t["round"] == "domain"]

    # Placeholder scoring, carried over unchanged: this counts how many
    # answers were submitted, not what they contained.
    interview.score_intro = min(len(intro) * 25, 100)
    interview.score_project = min(len(project) * 25, 100)
    interview.score_domain = min(len(domain) * 25, 100)
    interview.total_score = (
        interview.score_intro + interview.score_project + interview.score_domain
    ) // 3

    await applicant.save()

    # Tell the recruiter. Without this they only learn an interview finished
    # by opening the dashboard and looking.
    org = await Organisation.get(applicant.org_id)
    drive = await Drive.get(applicant.drive_id)
    if org and org.notify_on_interview and org.email:
        background_tasks.add_task(
            send_interview_completed_email,
            to_email=org.email,
            to_name=org.name,
            applicant_name=applicant.name,
            drive_name=drive.name if drive else "",
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
# RECORDING
# ──────────────────────────────────────────────
@router.post(
    "/{token}/recording",
    status_code=status.HTTP_204_NO_CONTENT,
    # Each accepted recording is up to 200MB. Without a cap this endpoint is
    # the cheapest way to run up an object-storage bill.
    dependencies=[Depends(RateLimit("interview_recording", limit=5, window_seconds=3600,
                                    key_param="token"))],
)
async def upload_recording(token: str, file: UploadFile = File(...)):
    """
    recording_url used to be a string accepted on /end and stored verbatim, so
    the client decided what it pointed at. The file now goes to object storage
    under a server-generated key.

    Not gated on expiry: a candidate finishing on the boundary must still be
    able to upload what they just recorded.
    """
    applicant = await _by_token(token)

    if not storage_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Recording upload is unavailable: object storage is not configured",
        )

    try:
        key = storage_service.upload_recording(
            interview_id=applicant.id,
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
            extra={"applicant_id": str(applicant.id), "error": str(exc)},
        )
        raise HTTPException(status_code=502, detail="Upload failed, please try again")

    applicant.interview.recording_url = key
    await applicant.save()
    return None


# ──────────────────────────────────────────────
# DETAIL (organisation only)
# ──────────────────────────────────────────────
@router.get("/{token}/detail", response_model=InterviewDetailResponse)
async def get_interview_detail(
    token: str,
    org: Organisation = Depends(get_current_org),
):
    """
    This was unauthenticated despite its own docstring saying "for org
    dashboard": anyone holding an interview token could read the transcript,
    the scores and the malpractice flags.

    An unknown token and another organisation's token both return 404, so it
    cannot be used to probe for valid tokens.
    """
    applicant = await Applicant.find_one(
        {"interview.token": token, "org_id": org.id}
    )
    if not applicant or not applicant.interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    drive = await Drive.get(applicant.drive_id)
    interview = applicant.interview

    return InterviewDetailResponse(
        id=applicant.id,
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
        drive_name=drive.name if drive else "",
    )
