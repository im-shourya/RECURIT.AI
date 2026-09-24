"""
RECRUIT.AI — Applicant Admin Router (Organisation-only)
GET    /applicants                       — List, filter, search
GET    /applicants/export                — CSV export
GET    /applicants/{id}                  — Full profile
GET    /applicants/{id}/submission-file  — Short-lived download link
GET    /applicants/{id}/recording-file   — Short-lived interview playback link
POST   /applicants/{id}/decision         — Hire / reject
POST   /applicants/{id}/resend-email     — Re-send a transactional email
POST   /applicants/bulk-decision         — Decide up to 100 at once
DELETE /applicants/{id}                  — Erase a candidate

Every endpoint is authenticated and scoped to the calling organisation.
Applicants carry org_id directly, so the scoping is a field match rather than
the join it used to be — a denormalisation that keeps the check to one filter.
"""

import csv
import io
import logging
import re
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.models.documents import (
    Applicant,
    ApplicantStatus,
    AuditAction,
    Drive,
    EmailLogEntry,
    EmailType,
    Organisation,
    TaskType,
    UserRole,
)
from app.models.schemas import (
    ApplicantDecisionRequest,
    InterviewSummaryResponse,
    SubmissionResponse,
    ApplicantDecisionResponse,
    ApplicantResponse,
    BulkDecisionRequest,
    BulkDecisionResponse,
    ResendEmailRequest,
    StoredFileLinkResponse,
    SubmissionFileLinkResponse,
)
from app.services import audit, storage_service
from app.services.auth_service import get_current_org, require_role
from app.services.email_service import (
    send_application_email,
    send_interview_email,
    send_result_email,
    send_task_email,
)

settings = get_settings()
log = logging.getLogger("recruit.applicants")

router = APIRouter(prefix="/applicants", tags=["Applicants (Organisation)"])


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def applicant_to_response(a: Applicant) -> ApplicantResponse:
    """Shared with the drives router, which embeds applicants in drive detail."""
    # Submission and interview are embedded now, so neither has an id of its
    # own. Both are 1:1 with the applicant, so the applicant's id identifies
    # them — the same value /interview/{token}/detail already reports.
    submission = (
        SubmissionResponse(
            id=a.id,
            applicant_id=a.id,
            file_url=a.submission.file_url or "",
            github_url=a.submission.github_url or "",
            description=a.submission.description or "",
            repolens_analysis=a.submission.repolens_analysis or {},
            submitted_at=a.submission.submitted_at,
        )
        if a.submission
        else None
    )

    interview = (
        InterviewSummaryResponse(
            id=a.id,
            token=a.interview.token,
            started_at=a.interview.started_at,
            ended_at=a.interview.ended_at,
            recording_url=a.interview.recording_url or "",
            score_intro=a.interview.score_intro,
            score_project=a.interview.score_project,
            score_domain=a.interview.score_domain,
            total_score=a.interview.total_score,
            malpractice_flags=a.interview.malpractice_flags or [],
        )
        if a.interview
        else None
    )

    return ApplicantResponse(
        id=a.id,
        drive_id=a.drive_id,
        name=a.name,
        email=a.email,
        reg_no=a.reg_no or "",
        skills=a.skills or [],
        primary_domain=a.primary_domain or "",
        github_url=a.github_url or "",
        status=a.status.value,
        applied_at=a.applied_at,
        submission=submission,
        interview=interview,
    )


async def _owned_applicant(applicant_id: UUID, org: Organisation) -> Applicant:
    """
    Fetch an applicant belonging to the calling organisation.

    A missing document and one owned by another organisation both raise 404 —
    never 403 — so this does not leak whether a given id exists.
    """
    applicant = await Applicant.find_one(
        Applicant.id == applicant_id, Applicant.org_id == org.id
    )
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    return applicant


def _build_conditions(
    org: Organisation,
    drive_id: Optional[UUID],
    status: Optional[str],
    q: Optional[str],
) -> list:
    """
    Shared by list and export, so an export can never widen the scoping or
    filters a list would have applied.
    """
    conditions = [Applicant.org_id == org.id]

    if drive_id:
        conditions.append(Applicant.drive_id == drive_id)

    if status:
        valid = {s.value for s in ApplicantStatus}
        if status not in valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Expected one of: {', '.join(sorted(valid))}",
            )
        conditions.append(Applicant.status == ApplicantStatus(status))

    if q:
        # re.escape matters: without it a search for "a.b" or "a|b" would be
        # interpreted as a pattern, and a crafted term could pin the database
        # on a pathological regex.
        pattern = re.compile(re.escape(q), re.IGNORECASE)
        conditions.append(
            {
                "$or": [
                    {"name": pattern},
                    {"email": pattern},
                    {"reg_no": pattern},
                ]
            }
        )

    return conditions


def _csv_safe(value) -> str:
    """
    Neutralise spreadsheet formula injection.

    Applicant names and skills come from a public form, and Excel and Sheets
    evaluate any cell beginning with =, +, - or @.
    """
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + text
    return text


# ──────────────────────────────────────────────
# LIST
# ──────────────────────────────────────────────
@router.get("", response_model=list[ApplicantResponse])
async def list_applicants(
    response: Response,
    drive_id: Optional[UUID] = Query(None, description="Restrict to one drive"),
    status: Optional[str] = Query(None, description="Filter by applicant status"),
    q: Optional[str] = Query(None, max_length=255, description="Search name, email or reg no"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    org: Organisation = Depends(get_current_org),
):
    conditions = _build_conditions(org, drive_id, status, q)
    query = Applicant.find(*conditions)

    # Counted before limit/offset: counting after would just report the page
    # size back. Headers rather than a {items, total} wrapper, so the body
    # stays a plain array and existing callers keep working.
    total = await query.count()
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Limit"] = str(limit)
    response.headers["X-Offset"] = str(offset)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count, X-Limit, X-Offset"

    applicants = (
        await query.sort(-Applicant.applied_at).skip(offset).limit(limit).to_list()
    )
    return [applicant_to_response(a) for a in applicants]


# ──────────────────────────────────────────────
# CSV EXPORT
#
# Declared before /{applicant_id}: FastAPI matches in definition order, so a
# later /export would be captured by the UUID route and rejected as invalid.
# ──────────────────────────────────────────────
@router.get("/export")
async def export_applicants(
    drive_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None, max_length=255),
    org: Organisation = Depends(get_current_org),
):
    conditions = _build_conditions(org, drive_id, status, q)
    applicants = (
        await Applicant.find(*conditions).sort(-Applicant.applied_at).to_list()
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Name", "Email", "Reg No", "Primary Domain", "Skills", "GitHub",
        "Status", "Applied At", "Submitted At", "Total Score",
        "Intro", "Project", "Domain",
    ])

    for a in applicants:
        interview, submission = a.interview, a.submission
        writer.writerow([
            _csv_safe(a.name),
            _csv_safe(a.email),
            _csv_safe(a.reg_no or ""),
            _csv_safe(a.primary_domain or ""),
            _csv_safe(", ".join(a.skills or [])),
            _csv_safe(a.github_url or ""),
            _csv_safe(a.status.value),
            a.applied_at.isoformat() if a.applied_at else "",
            submission.submitted_at.isoformat() if submission and submission.submitted_at else "",
            interview.total_score if interview else "",
            interview.score_intro if interview else "",
            interview.score_project if interview else "",
            interview.score_domain if interview else "",
        ])

    buffer.seek(0)
    filename = f"applicants-{datetime.now(timezone.utc):%Y%m%d}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ──────────────────────────────────────────────
# PROFILE
# ──────────────────────────────────────────────
@router.get("/{applicant_id}", response_model=ApplicantResponse)
async def get_applicant(
    applicant_id: UUID,
    org: Organisation = Depends(get_current_org),
):
    return applicant_to_response(await _owned_applicant(applicant_id, org))


# ──────────────────────────────────────────────
# SUBMISSION FILE LINK
# ──────────────────────────────────────────────
@router.get("/{applicant_id}/submission-file", response_model=SubmissionFileLinkResponse)
async def get_submission_file_link(
    applicant_id: UUID,
    org: Organisation = Depends(get_current_org),
):
    """
    Submission objects are private, so this is the only way to read one. The
    link is minted per request and expires in minutes.
    """
    applicant = await _owned_applicant(applicant_id, org)

    if not applicant.submission or not applicant.submission.file_url:
        raise HTTPException(status_code=404, detail="This applicant has no uploaded file")

    stored = applicant.submission.file_url
    try:
        url = storage_service.presigned_get_url(stored)
    except storage_service.StorageError as exc:
        log.error(
            "could not sign submission download",
            extra={"applicant_id": str(applicant_id), "error": str(exc)},
        )
        raise HTTPException(status_code=502, detail="Could not generate a download link")

    if not url:
        # Either storage is unconfigured, or this document predates uploads
        # and holds a plain URL the candidate supplied.
        if stored.startswith(("http://", "https://")):
            return SubmissionFileLinkResponse(url=stored, expires_in_seconds=0)
        raise HTTPException(
            status_code=503,
            detail="File downloads are not available: object storage is not configured",
        )

    return SubmissionFileLinkResponse(
        url=url, expires_in_seconds=storage_service.PRESIGNED_URL_TTL_SECONDS
    )


# ──────────────────────────────────────────────
# INTERVIEW RECORDING LINK
# ──────────────────────────────────────────────
@router.get("/{applicant_id}/recording-file", response_model=StoredFileLinkResponse)
async def get_recording_file_link(
    applicant_id: UUID,
    org: Organisation = Depends(get_current_org),
):
    """
    Short-lived playback link for an interview recording.

    `interview.recording_url` holds an object key, not a URL — the upload
    endpoint returns a server-generated key and recordings are stored private.
    Without this there was no way to turn that key back into something
    playable, so a recruiter could never watch what was captured.

    Scoped through _owned_applicant, so another organisation's id is a 404
    rather than a signed link to their candidate's video.
    """
    applicant = await _owned_applicant(applicant_id, org)

    if not applicant.interview or not applicant.interview.recording_url:
        raise HTTPException(
            status_code=404, detail="This applicant has no interview recording"
        )

    stored = applicant.interview.recording_url
    try:
        url = storage_service.presigned_get_url(stored)
    except storage_service.StorageError as exc:
        log.error(
            "could not sign recording playback",
            extra={"applicant_id": str(applicant_id), "error": str(exc)},
        )
        raise HTTPException(status_code=502, detail="Could not generate a playback link")

    if not url:
        # Either storage is unconfigured, or this is a legacy row from when
        # /end accepted a recording_url from the client and stored it verbatim.
        if stored.startswith(("http://", "https://")):
            return StoredFileLinkResponse(url=stored, expires_in_seconds=0)
        raise HTTPException(
            status_code=503,
            detail="Recording playback is not available: object storage is not configured",
        )

    return StoredFileLinkResponse(
        url=url, expires_in_seconds=storage_service.PRESIGNED_URL_TTL_SECONDS
    )


# ──────────────────────────────────────────────
# DECISION
# ──────────────────────────────────────────────
@router.post(
    "/{applicant_id}/decision",
    response_model=ApplicantDecisionResponse,
    # The product's own wording: AI assists, the recruiter decides. A member
    # reviews evidence; deciding is an admin action.
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def decide_applicant(
    applicant_id: UUID,
    body: ApplicantDecisionRequest,
    background_tasks: BackgroundTasks,
    org: Organisation = Depends(get_current_org),
):
    """
    Record the recruiter's final decision and email the candidate.

    This is the step that closes the hiring loop: nothing else moves an
    applicant into selected or rejected.
    """
    applicant = await _owned_applicant(applicant_id, org)

    if applicant.status in (ApplicantStatus.SELECTED, ApplicantStatus.REJECTED):
        raise HTTPException(
            status_code=400,
            detail=f"A decision has already been recorded for this applicant ({applicant.status.value})",
        )

    applicant.status = (
        ApplicantStatus.SELECTED if body.decision == "selected" else ApplicantStatus.REJECTED
    )
    applicant.email_logs.append(EmailLogEntry(type=EmailType.RESULT))
    await applicant.save()

    drive = await Drive.get(applicant.drive_id)
    drive_name = drive.name if drive else ""

    await audit.record(
        org_id=org.id,
        action=(
            AuditAction.APPLICANT_SELECTED
            if applicant.status == ApplicantStatus.SELECTED
            else AuditAction.APPLICANT_REJECTED
        ),
        entity_type="applicant",
        entity_id=applicant.id,
        entity_label=applicant.name,
        detail={"drive": drive_name, "decision": body.decision},
    )

    score = applicant.interview.total_score if applicant.interview else 0
    background_tasks.add_task(
        send_result_email,
        to_email=applicant.email,
        to_name=applicant.name,
        drive_name=drive_name,
        result_status=applicant.status.value,
        score=score or 0,
    )

    return ApplicantDecisionResponse(
        id=applicant.id,
        name=applicant.name,
        email=applicant.email,
        status=applicant.status.value,
        result_email_sent=True,
    )


# ──────────────────────────────────────────────
# RESEND AN EMAIL
# ──────────────────────────────────────────────
@router.post(
    "/{applicant_id}/resend-email",
    status_code=204,
    # Sends mail to a candidate in the organisation's name.
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def resend_email(
    applicant_id: UUID,
    body: ResendEmailRequest,
    background_tasks: BackgroundTasks,
    org: Organisation = Depends(get_current_org),
):
    """
    Useful when a candidate deletes a link or the original bounced. Each
    resend is logged, so the trail shows the message really was sent twice.
    """
    applicant = await _owned_applicant(applicant_id, org)
    drive = await Drive.get(applicant.drive_id)
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    kind = body.type

    if kind == "task":
        if not drive.task_deadline or drive.task_type != TaskType.TASK:
            raise HTTPException(status_code=400, detail="This is not a task-based drive")
        background_tasks.add_task(
            send_task_email,
            to_email=applicant.email,
            to_name=applicant.name,
            drive_name=drive.name,
            task_description=drive.task_description or "",
            task_link=f"{settings.FRONTEND_URL}/task/{drive.link_token}",
            submission_link=f"{settings.FRONTEND_URL}/submit/{applicant.submit_token}",
            deadline=str(drive.task_deadline),
        )
    elif kind == "interview":
        if not applicant.interview:
            raise HTTPException(status_code=400, detail="This applicant has no interview yet")
        background_tasks.add_task(
            send_interview_email,
            to_email=applicant.email,
            to_name=applicant.name,
            drive_name=drive.name,
            interview_link=f"{settings.FRONTEND_URL}/interview/{applicant.interview.token}",
        )
    elif kind == "result":
        if applicant.status not in (ApplicantStatus.SELECTED, ApplicantStatus.REJECTED):
            raise HTTPException(
                status_code=400,
                detail="No decision has been recorded for this applicant yet",
            )
        background_tasks.add_task(
            send_result_email,
            to_email=applicant.email,
            to_name=applicant.name,
            drive_name=drive.name,
            result_status=applicant.status.value,
            score=(applicant.interview.total_score if applicant.interview else 0) or 0,
        )
    else:  # "applied"
        background_tasks.add_task(
            send_application_email,
            to_email=applicant.email,
            to_name=applicant.name,
            drive_name=drive.name,
            org_name=org.name,
        )

    applicant.email_logs.append(EmailLogEntry(type=EmailType(kind)))
    await applicant.save()
    return None


# ──────────────────────────────────────────────
# BULK DECISION
# ──────────────────────────────────────────────
@router.post(
    "/bulk-decision",
    response_model=BulkDecisionResponse,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def bulk_decision(
    body: BulkDecisionRequest,
    background_tasks: BackgroundTasks,
    org: Organisation = Depends(get_current_org),
):
    """
    Each id is re-checked against the calling organisation rather than trusted
    from the request, so another org's applicant cannot be slipped in. Ids
    that are not owned, or already decided, are reported in `skipped` instead
    of failing the whole batch.
    """
    target = (
        ApplicantStatus.SELECTED if body.decision == "selected" else ApplicantStatus.REJECTED
    )

    owned = {
        a.id: a
        for a in await Applicant.find(
            Applicant.org_id == org.id,
            {"_id": {"$in": list(body.applicant_ids)}},
        ).to_list()
    }

    updated: list[Applicant] = []
    skipped: list[str] = []

    for applicant_id in body.applicant_ids:
        applicant = owned.get(applicant_id)
        if applicant is None:
            skipped.append(f"{applicant_id}: not found")
            continue
        if applicant.status in (ApplicantStatus.SELECTED, ApplicantStatus.REJECTED):
            skipped.append(f"{applicant_id}: already {applicant.status.value}")
            continue

        applicant.status = target
        applicant.email_logs.append(EmailLogEntry(type=EmailType.RESULT))
        await applicant.save()
        updated.append(applicant)

    # Audit and mail only after the writes have landed, so nobody is told an
    # outcome that was not saved.
    for applicant in updated:
        drive = await Drive.get(applicant.drive_id)
        drive_name = drive.name if drive else ""

        await audit.record(
            org_id=org.id,
            action=(
                AuditAction.APPLICANT_SELECTED
                if target == ApplicantStatus.SELECTED
                else AuditAction.APPLICANT_REJECTED
            ),
            entity_type="applicant",
            entity_id=applicant.id,
            entity_label=applicant.name,
            detail={"drive": drive_name, "bulk": True},
        )
        background_tasks.add_task(
            send_result_email,
            to_email=applicant.email,
            to_name=applicant.name,
            drive_name=drive_name,
            result_status=target.value,
            score=(applicant.interview.total_score if applicant.interview else 0) or 0,
        )

    return BulkDecisionResponse(
        updated=len(updated), skipped=skipped, status=target.value
    )


# ──────────────────────────────────────────────
# DELETE A CANDIDATE'S DATA
# ──────────────────────────────────────────────
@router.delete(
    "/{applicant_id}",
    status_code=204,
    # Irreversible erasure of a person's data, including their transcript.
    dependencies=[Depends(require_role(UserRole.OWNER))],
)
async def delete_applicant(
    applicant_id: UUID,
    org: Organisation = Depends(get_current_org),
):
    """
    Permanently erase a candidate and everything recorded about them.

    The submission, interview, transcript and email logs are embedded, so they
    go with the document. Stored files are deleted separately: leaving a
    recording behind would make the deletion only partial.

    The audit entry is written first and deliberately outlives the applicant,
    so erasing someone cannot also erase the record that they were erased.
    """
    applicant = await _owned_applicant(applicant_id, org)

    keys = []
    if applicant.submission and applicant.submission.file_url:
        keys.append(applicant.submission.file_url)
    if applicant.interview and applicant.interview.recording_url:
        keys.append(applicant.interview.recording_url)

    drive = await Drive.get(applicant.drive_id)

    await audit.record(
        org_id=org.id,
        action=AuditAction.APPLICANT_DELETED,
        entity_type="applicant",
        entity_id=applicant.id,
        entity_label=applicant.name,
        detail={"drive": drive.name if drive else "", "stored_files": len(keys)},
    )

    await applicant.delete()

    # After the document is gone: a storage error must not leave the record in
    # place, and an orphaned object is recoverable where a half-deleted
    # candidate is not.
    for key in keys:
        try:
            storage_service.delete_object(key)
        except Exception as exc:
            log.error(
                "stored file left behind after applicant deletion",
                extra={"key": key, "error": type(exc).__name__},
            )

    return None
