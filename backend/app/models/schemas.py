"""
RECRUIT.AI — Pydantic Schemas
Request / Response models for all API endpoints.
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ══════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════
class OrgRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6)
    description: str = ""
    domain_tags: list[str] = []
    logo_url: str = ""


class OrgLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OrgProfileResponse(BaseModel):
    id: UUID
    name: str
    email: str
    description: str
    domain_tags: list[str]
    logo_url: str
    created_at: datetime

    class Config:
        from_attributes = True


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class OrgProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    domain_tags: Optional[list[str]] = None
    logo_url: Optional[str] = None


# ══════════════════════════════════════════════
# DRIVES
# ══════════════════════════════════════════════
class DriveCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    domain: str = Field(..., min_length=2, max_length=255)
    task_type: str = Field(..., pattern="^(task|github)$")
    task_description: str = ""
    question_level: str = Field(default="beginner", pattern="^(beginner|intermediate|advanced)$")
    apply_deadline: date
    task_deadline: Optional[date] = None


class DriveResponse(BaseModel):
    id: UUID
    org_id: UUID
    name: str
    domain: str
    task_type: str
    task_description: str
    question_level: str
    apply_deadline: date
    task_deadline: Optional[date]
    link_token: str
    qr_code_url: str
    status: str
    created_at: datetime
    applicant_count: int = 0

    class Config:
        from_attributes = True


class DriveDetailResponse(DriveResponse):
    organisation_name: str = ""
    applicants: list["ApplicantResponse"] = []


class DriveUpdateRequest(BaseModel):
    """
    Partial update of a drive. Every field is optional; only the ones sent are
    applied. `link_token`, `qr_code_url` and `org_id` are deliberately absent —
    rotating the public link would silently break every share and QR code
    already handed out.
    """
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    domain: Optional[str] = Field(None, min_length=2, max_length=255)
    task_description: Optional[str] = None
    question_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")
    apply_deadline: Optional[date] = None
    task_deadline: Optional[date] = None
    status: Optional[str] = Field(None, pattern="^(active|closed)$")


class DriveStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|closed)$")


class DrivePublicResponse(BaseModel):
    """What an applicant sees when they open the apply link."""
    id: UUID
    name: str
    domain: str
    task_type: str
    task_description: str
    question_level: str
    apply_deadline: date
    task_deadline: Optional[date]
    organisation_name: str
    organisation_logo: str
    status: str

    class Config:
        from_attributes = True


# ══════════════════════════════════════════════
# APPLICANTS
# ══════════════════════════════════════════════
class ApplyRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    reg_no: str = ""
    skills: list[str] = []
    primary_domain: str = ""
    github_url: str = ""


class ApplicantResponse(BaseModel):
    id: UUID
    drive_id: UUID
    name: str
    email: str
    reg_no: str
    skills: list[str]
    primary_domain: str
    github_url: str
    status: str
    applied_at: datetime
    submission: Optional["SubmissionResponse"] = None
    interview: Optional["InterviewSummaryResponse"] = None

    class Config:
        from_attributes = True


class ApplicantStatusUpdate(BaseModel):
    status: str = Field(
        ...,
        pattern="^(applied|task_sent|submitted|interview_sent|interviewed|selected|rejected)$",
    )


class ApplicantDecisionRequest(BaseModel):
    """A recruiter's final hire / reject decision on one applicant."""
    decision: str = Field(..., pattern="^(selected|rejected)$")


class ApplicantDecisionResponse(BaseModel):
    id: UUID
    name: str
    email: str
    status: str
    result_email_sent: bool


# ══════════════════════════════════════════════
# SUBMISSIONS
# ══════════════════════════════════════════════
class SubmissionCreateRequest(BaseModel):
    file_url: str = ""
    github_url: str = ""
    description: str = ""


class FileUploadResponse(BaseModel):
    """Returned by the upload endpoint; `file_url` holds the stored object key."""
    file_url: str
    filename: str


class SubmissionFileLinkResponse(BaseModel):
    """A short-lived link to a stored submission file."""
    url: str
    expires_in_seconds: int


class SubmissionResponse(BaseModel):
    id: UUID
    applicant_id: UUID
    file_url: str
    github_url: str
    description: str
    repolens_analysis: dict
    submitted_at: datetime

    class Config:
        from_attributes = True


# ══════════════════════════════════════════════
# INTERVIEWS
# ══════════════════════════════════════════════
class InterviewConfigResponse(BaseModel):
    """Sent to the candidate when they open the interview link."""
    interview_id: UUID
    applicant_name: str
    drive_name: str
    domain: str
    question_level: str
    task_type: str
    repolens_analysis: dict = {}
    max_duration_seconds: int = 300  # 5 minutes


class InterviewStartResponse(BaseModel):
    interview_id: UUID
    message: str = "Interview session started. Good luck!"


class InterviewAnswerRequest(BaseModel):
    question_text: str
    answer_text: str
    round_name: str = Field(..., pattern="^(intro|project|domain)$")


class InterviewAnswerResponse(BaseModel):
    next_question: str
    round_name: str
    is_last: bool = False


class InterviewEndRequest(BaseModel):
    recording_url: str = ""


class InterviewEndResponse(BaseModel):
    total_score: int
    score_intro: int
    score_project: int
    score_domain: int
    message: str = "Interview completed. Thank you!"


class InterviewSummaryResponse(BaseModel):
    id: UUID
    token: str
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    recording_url: str
    score_intro: int
    score_project: int
    score_domain: int
    total_score: int
    malpractice_flags: list

    class Config:
        from_attributes = True


class InterviewDetailResponse(InterviewSummaryResponse):
    transcript: list
    applicant_name: str = ""
    drive_name: str = ""


# ══════════════════════════════════════════════
# EMAIL
# ══════════════════════════════════════════════
class EmailLogResponse(BaseModel):
    id: UUID
    applicant_id: UUID
    type: str
    sent_at: datetime
    emailjs_msg_id: str

    class Config:
        from_attributes = True


# ══════════════════════════════════════════════
# ANALYTICS
# ══════════════════════════════════════════════
class ChartDataPoint(BaseModel):
    name: str
    value: int

class AnalyticsResponse(BaseModel):
    total_drives: int
    active_drives: int
    total_applicants: int
    total_interviews: int
    avg_score: int
    
    score_distribution: list[ChartDataPoint]
    domain_distribution: list[ChartDataPoint]
    status_distribution: list[ChartDataPoint]
    recent_trend: list[ChartDataPoint]
    
    class Config:
        from_attributes = True

# Forward references for nested models
DriveDetailResponse.model_rebuild()
ApplicantResponse.model_rebuild()
