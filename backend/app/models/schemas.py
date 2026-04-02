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
    status: str


# ══════════════════════════════════════════════
# SUBMISSIONS
# ══════════════════════════════════════════════
class SubmissionCreateRequest(BaseModel):
    file_url: str = ""
    github_url: str = ""
    description: str = ""


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


# Forward references for nested models
DriveDetailResponse.model_rebuild()
ApplicantResponse.model_rebuild()
