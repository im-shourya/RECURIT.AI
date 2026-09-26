"""
RECRUIT.AI — SQLAlchemy Database Models
Complete PostgreSQL schema for the recruitment platform.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Date, DateTime,
    ForeignKey, Enum as SAEnum, JSON, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship, DeclarativeBase
import enum


# ──────────────────────────────────────────────
# Base
# ──────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────
class TaskType(str, enum.Enum):
    TASK = "task"
    GITHUB = "github"


class QuestionLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class DriveStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"


class ApplicantStatus(str, enum.Enum):
    APPLIED = "applied"
    TASK_SENT = "task_sent"
    SUBMITTED = "submitted"
    INTERVIEW_SENT = "interview_sent"
    INTERVIEWED = "interviewed"
    SELECTED = "selected"
    REJECTED = "rejected"


class EmailType(str, enum.Enum):
    APPLIED = "applied"
    TASK = "task"
    INTERVIEW = "interview"
    RESULT = "result"


# ──────────────────────────────────────────────
# Organisations
# ──────────────────────────────────────────────
class Organisation(Base):
    __tablename__ = "organisations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    description = Column(Text, default="")
    domain_tags = Column(ARRAY(String), default=list)
    logo_url = Column(Text, default="")
    # Recruiters are emailed when a candidate finishes an interview. Opt-out
    # rather than opt-in: a drive owner who hears nothing assumes the platform
    # is idle, which is the failure this notification exists to prevent.
    notify_on_interview = Column(Boolean, default=True, nullable=False, server_default="true")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    drives = relationship("Drive", back_populates="organisation", cascade="all, delete-orphan")
    reset_tokens = relationship("PasswordResetToken", back_populates="organisation", cascade="all, delete-orphan")


# ──────────────────────────────────────────────
# Drives (Recruitment Campaigns)
# ──────────────────────────────────────────────
class Drive(Base):
    __tablename__ = "drives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False)
    task_type = Column(SAEnum(TaskType, name="task_type_enum", values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    task_description = Column(Text, default="")
    question_level = Column(SAEnum(QuestionLevel, name="question_level_enum", values_callable=lambda obj: [e.value for e in obj]), default=QuestionLevel.BEGINNER)
    apply_deadline = Column(Date, nullable=False)
    task_deadline = Column(Date, nullable=True)  # Only needed when task_type = 'task'
    link_token = Column(String(64), unique=True, nullable=False, index=True)
    qr_code_url = Column(Text, default="")
    status = Column(SAEnum(DriveStatus, name="drive_status_enum", values_callable=lambda obj: [e.value for e in obj]), default=DriveStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    organisation = relationship("Organisation", back_populates="drives")
    applicants = relationship("Applicant", back_populates="drive", cascade="all, delete-orphan")


# ──────────────────────────────────────────────
# Applicants
# ──────────────────────────────────────────────
class Applicant(Base):
    __tablename__ = "applicants"
    __table_args__ = (
        # The duplicate check in the apply handler reads before it writes, so
        # two requests arriving together could both pass it and create two
        # applicants for the same person. The database is the only place that
        # race can actually be closed.
        UniqueConstraint("drive_id", "email", name="uq_applicant_drive_email"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drive_id = Column(UUID(as_uuid=True), ForeignKey("drives.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    reg_no = Column(String(100), default="")
    skills = Column(ARRAY(String), default=list)
    primary_domain = Column(String(255), default="")
    github_url = Column(Text, default="")
    # Unguessable capability token for the public submission endpoint. The
    # applicant's UUID used to be the only thing guarding that route, which
    # meant anyone holding an id could submit on someone else's behalf.
    submit_token = Column(String(64), unique=True, nullable=True, index=True)
    status = Column(
        SAEnum(ApplicantStatus, name="applicant_status_enum", values_callable=lambda obj: [e.value for e in obj]),
        default=ApplicantStatus.APPLIED
    )
    applied_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    drive = relationship("Drive", back_populates="applicants")
    submission = relationship("Submission", back_populates="applicant", uselist=False, cascade="all, delete-orphan")
    interview = relationship("Interview", back_populates="applicant", uselist=False, cascade="all, delete-orphan")
    email_logs = relationship("EmailLog", back_populates="applicant", cascade="all, delete-orphan")


# ──────────────────────────────────────────────
# Submissions (Task or GitHub project)
# ──────────────────────────────────────────────
class Submission(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicant_id = Column(UUID(as_uuid=True), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False, unique=True)
    file_url = Column(Text, default="")
    github_url = Column(Text, default="")
    description = Column(Text, default="")
    repolens_analysis = Column(JSONB, default=dict)
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    applicant = relationship("Applicant", back_populates="submission")


# ──────────────────────────────────────────────
# Interviews
# ──────────────────────────────────────────────
class Interview(Base):
    __tablename__ = "interviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicant_id = Column(UUID(as_uuid=True), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False, unique=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    # Interview links used to be valid forever. Nullable so rows created
    # before this column existed keep working rather than reading as expired.
    expires_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    recording_url = Column(Text, default="")
    transcript = Column(JSONB, default=list)  # List of {role, text, timestamp}
    score_intro = Column(Integer, default=0)
    score_project = Column(Integer, default=0)
    score_domain = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    malpractice_flags = Column(JSONB, default=list)  # List of {type, timestamp, detail}

    # Relationships
    applicant = relationship("Applicant", back_populates="interview")


# ──────────────────────────────────────────────
# Password Reset Tokens
# ──────────────────────────────────────────────
class PasswordResetToken(Base):
    """
    A single-use, short-lived password reset grant.

    Only the SHA-256 hash of the token is stored. The plaintext exists solely
    in the emailed link, so a database leak cannot be replayed to take over
    accounts. Kept in its own table rather than as columns on `organisations`
    so that `create_all()` provisions it on existing databases — adding
    columns to an existing table would need a migration, and this project has
    none yet.
    """
    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    organisation = relationship("Organisation", back_populates="reset_tokens")


class EmailStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


# ──────────────────────────────────────────────
# Email Outbox
# ──────────────────────────────────────────────
class EmailOutbox(Base):
    """
    A queued outbound email.

    Emails were handed to FastAPI BackgroundTasks, which run in-process: if
    the worker restarted between the response and the send, that email was
    gone, with no record that it had ever been attempted. For a result
    notification or a password reset link, silently losing it is the worst
    possible failure.

    The row is written inside the request, so the intent to send survives a
    restart even if the send itself does not. A sweeper retries anything left
    pending.
    """
    __tablename__ = "email_outbox"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    to_email = Column(String(255), nullable=False, index=True)
    subject = Column(Text, nullable=False)
    html = Column(Text, nullable=False)
    text = Column(Text, nullable=False, default="")
    status = Column(
        SAEnum(EmailStatus, name="email_status_enum", values_callable=lambda obj: [e.value for e in obj]),
        default=EmailStatus.PENDING,
        nullable=False,
        index=True,
    )
    attempts = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, default="")
    provider_message_id = Column(String(255), default="")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    sent_at = Column(DateTime(timezone=True), nullable=True)


# ──────────────────────────────────────────────
# Email Logs
# ──────────────────────────────────────────────
class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicant_id = Column(UUID(as_uuid=True), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    type = Column(SAEnum(EmailType, name="email_type_enum", values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    sent_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    emailjs_msg_id = Column(String(255), default="")

    # Relationships
    applicant = relationship("Applicant", back_populates="email_logs")
