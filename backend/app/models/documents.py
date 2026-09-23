"""
RECRUIT.AI — MongoDB Documents (Beanie)

Replaces the SQLAlchemy models. The shape is not a table-for-table
translation, because copying a relational schema into MongoDB gives you the
costs of both and the benefits of neither.

What changed and why:

  Submission and Interview were 1:1 with Applicant and only ever read through
  one. They are now embedded, which removes two collections, two joins and two
  cascade rules — the row could never exist without its applicant anyway.

  EmailLog is append-only, small, and only ever read for one applicant. It is
  an embedded list.

  AuditLog stays its own collection, deliberately. It has to outlive the
  documents it describes: embedding it would mean deleting a candidate also
  deleted the record that they were deleted.

  PasswordResetToken stays separate and gains a TTL index, so expired tokens
  are reaped by the server instead of accumulating.

Referential integrity is no longer the database's job. Every cascade is in
app/services/cascade.py, and every uniqueness rule that was a constraint is
now a unique index declared below.

Ids stay UUIDs rather than ObjectIds: they appear in links already sent to
candidates, and in rows of the audit log that must keep resolving.
"""

from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

import pymongo
from beanie import Document
from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ──────────────────────────────────────────────
# Enums — unchanged values, so stored data and
# API responses read exactly as before
# ──────────────────────────────────────────────
class TaskType(str, Enum):
    TASK = "task"
    GITHUB = "github"


class QuestionLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class DriveStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"


class ApplicantStatus(str, Enum):
    APPLIED = "applied"
    TASK_SENT = "task_sent"
    SUBMITTED = "submitted"
    INTERVIEW_SENT = "interview_sent"
    INTERVIEWED = "interviewed"
    SELECTED = "selected"
    REJECTED = "rejected"


class EmailType(str, Enum):
    APPLIED = "applied"
    TASK = "task"
    INTERVIEW = "interview"
    RESULT = "result"


class EmailStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


ROLE_RANK = {UserRole.MEMBER: 0, UserRole.ADMIN: 1, UserRole.OWNER: 2}


class AuditAction(str, Enum):
    MEMBER_INVITED = "member.invited"
    MEMBER_ROLE_CHANGED = "member.role_changed"
    MEMBER_REMOVED = "member.removed"
    APPLICANT_SELECTED = "applicant.selected"
    APPLICANT_REJECTED = "applicant.rejected"
    APPLICANT_DELETED = "applicant.deleted"
    DRIVE_CREATED = "drive.created"
    DRIVE_UPDATED = "drive.updated"
    DRIVE_DELETED = "drive.deleted"
    PASSWORD_CHANGED = "org.password_changed"


# ──────────────────────────────────────────────
# Embedded documents
# ──────────────────────────────────────────────
class Submission(BaseModel):
    """A candidate's task or project submission. Embedded in Applicant."""
    file_url: str = ""
    github_url: str = ""
    description: str = ""
    repolens_analysis: dict = Field(default_factory=dict)
    submitted_at: datetime = Field(default_factory=_now)


class Interview(BaseModel):
    """
    A candidate's interview. Embedded in Applicant.

    `token` is indexed on the parent collection so an interview can still be
    fetched by token alone, which is how the candidate reaches it.
    """
    token: str
    expires_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    recording_url: str = ""
    transcript: list = Field(default_factory=list)
    score_intro: int = 0
    score_project: int = 0
    score_domain: int = 0
    total_score: int = 0
    malpractice_flags: list = Field(default_factory=list)


class EmailLogEntry(BaseModel):
    """One sent email. Embedded list on Applicant."""
    type: EmailType
    sent_at: datetime = Field(default_factory=_now)
    provider_message_id: str = ""


# ──────────────────────────────────────────────
# Collections
# ──────────────────────────────────────────────
class Organisation(Document):
    id: UUID = Field(default_factory=uuid4)
    name: str
    # Kept for display and contact. The sign-in credential lives on User.
    email: str
    description: str = ""
    domain_tags: list[str] = Field(default_factory=list)
    logo_url: str = ""
    notify_on_interview: bool = True
    created_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "organisations"


class User(Document):
    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    name: str = ""
    email: str
    # None until an invited member sets a password. Such a user cannot sign
    # in, because no password hashes to None.
    password_hash: Optional[str] = None
    role: UserRole = UserRole.MEMBER
    is_active: bool = True
    created_at: datetime = Field(default_factory=_now)
    last_login_at: Optional[datetime] = None

    class Settings:
        name = "users"
        indexes = [
            pymongo.IndexModel([("org_id", pymongo.ASCENDING)]),
            # Email is the sign-in identifier, so it is unique across the
            # whole deployment, not per organisation.
            pymongo.IndexModel([("email", pymongo.ASCENDING)], unique=True),
        ]


class Drive(Document):
    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    name: str
    domain: str
    task_type: TaskType
    task_description: str = ""
    question_level: QuestionLevel = QuestionLevel.BEGINNER
    apply_deadline: date
    task_deadline: Optional[date] = None
    link_token: str
    qr_code_url: str = ""
    status: DriveStatus = DriveStatus.ACTIVE
    created_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "drives"
        indexes = [
            pymongo.IndexModel([("org_id", pymongo.ASCENDING)]),
            pymongo.IndexModel([("link_token", pymongo.ASCENDING)], unique=True),
        ]


class Applicant(Document):
    id: UUID = Field(default_factory=uuid4)
    drive_id: UUID
    # Denormalised from the drive so the common "everything for this org"
    # query does not need a lookup. Drives never change owner, so this cannot
    # drift.
    org_id: UUID
    name: str
    email: str
    reg_no: str = ""
    skills: list[str] = Field(default_factory=list)
    primary_domain: str = ""
    github_url: str = ""
    submit_token: Optional[str] = None
    status: ApplicantStatus = ApplicantStatus.APPLIED
    applied_at: datetime = Field(default_factory=_now)

    submission: Optional[Submission] = None
    interview: Optional[Interview] = None
    email_logs: list[EmailLogEntry] = Field(default_factory=list)

    class Settings:
        name = "applicants"
        indexes = [
            pymongo.IndexModel([("org_id", pymongo.ASCENDING)]),
            pymongo.IndexModel([("drive_id", pymongo.ASCENDING)]),
            pymongo.IndexModel([("email", pymongo.ASCENDING)]),
            # Replaces UNIQUE (drive_id, email): the apply handler checks
            # before inserting, which is a read then a write, so only the
            # index actually closes the race.
            pymongo.IndexModel(
                [("drive_id", pymongo.ASCENDING), ("email", pymongo.ASCENDING)],
                unique=True,
                name="uq_applicant_drive_email",
            ),
            # Sparse: most applicants have a token, but a partial index keeps
            # any missing ones from colliding on null.
            pymongo.IndexModel(
                [("submit_token", pymongo.ASCENDING)], unique=True, sparse=True
            ),
            # The interview is embedded but still reached by token alone.
            pymongo.IndexModel(
                [("interview.token", pymongo.ASCENDING)], unique=True, sparse=True
            ),
        ]


class PasswordResetToken(Document):
    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    user_id: Optional[UUID] = None
    token_hash: str
    expires_at: datetime
    used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "password_reset_tokens"
        indexes = [
            pymongo.IndexModel([("token_hash", pymongo.ASCENDING)], unique=True),
            pymongo.IndexModel([("user_id", pymongo.ASCENDING)]),
            # TTL: MongoDB reaps documents once expires_at passes. Postgres had
            # no equivalent, so spent tokens accumulated forever.
            pymongo.IndexModel([("expires_at", pymongo.ASCENDING)], expireAfterSeconds=0),
        ]


class AuditLog(Document):
    """
    Append-only record of consequential actions.

    Its own collection on purpose. It must outlive the documents it describes,
    so erasing a candidate cannot also erase the record that they were erased.
    The subject is stored as an id plus a label captured at write time.
    """
    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    action: AuditAction
    entity_type: str
    entity_id: Optional[UUID] = None
    entity_label: str = ""
    detail: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "audit_log"
        indexes = [
            pymongo.IndexModel([("org_id", pymongo.ASCENDING)]),
            pymongo.IndexModel([("action", pymongo.ASCENDING)]),
            pymongo.IndexModel([("entity_id", pymongo.ASCENDING)]),
            pymongo.IndexModel([("created_at", pymongo.DESCENDING)]),
        ]


class EmailOutbox(Document):
    id: UUID = Field(default_factory=uuid4)
    to_email: str
    subject: str
    html: str
    text: str = ""
    status: EmailStatus = EmailStatus.PENDING
    attempts: int = 0
    last_error: str = ""
    provider_message_id: str = ""
    created_at: datetime = Field(default_factory=_now)
    sent_at: Optional[datetime] = None

    class Settings:
        name = "email_outbox"
        indexes = [
            pymongo.IndexModel([("to_email", pymongo.ASCENDING)]),
            # The sweeper only scans pending rows, oldest first.
            pymongo.IndexModel(
                [("status", pymongo.ASCENDING), ("created_at", pymongo.ASCENDING)]
            ),
            # Delivered mail is reaped automatically. MongoDB's TTL ignores
            # documents where the field is null, so pending and failed rows —
            # which have no sent_at — are kept indefinitely for retry and for
            # inspection. Without this the collection only ever grows.
            pymongo.IndexModel(
                [("sent_at", pymongo.ASCENDING)],
                expireAfterSeconds=60 * 60 * 24 * 30,
                name="ttl_sent_at",
            ),
        ]


# Registered with Beanie at startup. Order does not matter; listed in the
# order they appear above for readability.
ALL_DOCUMENTS = [
    Organisation,
    User,
    Drive,
    Applicant,
    PasswordResetToken,
    AuditLog,
    EmailOutbox,
]
