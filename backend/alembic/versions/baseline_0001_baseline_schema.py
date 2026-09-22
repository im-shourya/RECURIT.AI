"""baseline schema

Baseline migration capturing the schema as it stood when Alembic was first
wired up: organisations, drives, applicants, submissions, interviews,
email_logs and password_reset_tokens.

Generated from the SQLAlchemy models rather than transcribed by hand, so it
matches app/models/database.py exactly.

For an existing database that already has these tables (they were created by
Base.metadata.create_all on startup), do not run this migration — mark it as
already applied instead:

    alembic stamp baseline_0001

A fresh database runs it normally with `alembic upgrade head`.

Revision ID: baseline_0001
Revises:
Create Date: 2026-09-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import String, Text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "baseline_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('organisations',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('domain_tags', postgresql.ARRAY(String()), nullable=True),
    sa.Column('logo_url', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organisations_email'), 'organisations', ['email'], unique=True)
    op.create_table('drives',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('domain', sa.String(length=255), nullable=False),
    sa.Column('task_type', sa.Enum('task', 'github', name='task_type_enum'), nullable=False),
    sa.Column('task_description', sa.Text(), nullable=True),
    sa.Column('question_level', sa.Enum('beginner', 'intermediate', 'advanced', name='question_level_enum'), nullable=True),
    sa.Column('apply_deadline', sa.Date(), nullable=False),
    sa.Column('task_deadline', sa.Date(), nullable=True),
    sa.Column('link_token', sa.String(length=64), nullable=False),
    sa.Column('qr_code_url', sa.Text(), nullable=True),
    sa.Column('status', sa.Enum('active', 'closed', name='drive_status_enum'), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['org_id'], ['organisations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_drives_link_token'), 'drives', ['link_token'], unique=True)
    op.create_table('password_reset_tokens',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['org_id'], ['organisations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_password_reset_tokens_token_hash'), 'password_reset_tokens', ['token_hash'], unique=True)
    op.create_table('applicants',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('drive_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('reg_no', sa.String(length=100), nullable=True),
    sa.Column('skills', postgresql.ARRAY(String()), nullable=True),
    sa.Column('primary_domain', sa.String(length=255), nullable=True),
    sa.Column('github_url', sa.Text(), nullable=True),
    sa.Column('status', sa.Enum('applied', 'task_sent', 'submitted', 'interview_sent', 'interviewed', 'selected', 'rejected', name='applicant_status_enum'), nullable=True),
    sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['drive_id'], ['drives.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_applicants_email'), 'applicants', ['email'], unique=False)
    op.create_table('email_logs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('applicant_id', sa.UUID(), nullable=False),
    sa.Column('type', sa.Enum('applied', 'task', 'interview', 'result', name='email_type_enum'), nullable=False),
    sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('emailjs_msg_id', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('interviews',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('applicant_id', sa.UUID(), nullable=False),
    sa.Column('token', sa.String(length=64), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('recording_url', sa.Text(), nullable=True),
    sa.Column('transcript', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('score_intro', sa.Integer(), nullable=True),
    sa.Column('score_project', sa.Integer(), nullable=True),
    sa.Column('score_domain', sa.Integer(), nullable=True),
    sa.Column('total_score', sa.Integer(), nullable=True),
    sa.Column('malpractice_flags', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('applicant_id')
    )
    op.create_index(op.f('ix_interviews_token'), 'interviews', ['token'], unique=True)
    op.create_table('submissions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('applicant_id', sa.UUID(), nullable=False),
    sa.Column('file_url', sa.Text(), nullable=True),
    sa.Column('github_url', sa.Text(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('repolens_analysis', postgresql.JSONB(astext_type=Text()), nullable=True),
    sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('applicant_id')
    )


def downgrade() -> None:
    # Dropping the tables leaves the PostgreSQL enum types behind, so they
    # are removed explicitly at the end of this function.
    op.drop_table('submissions')
    op.drop_index(op.f('ix_interviews_token'), table_name='interviews')
    op.drop_table('interviews')
    op.drop_table('email_logs')
    op.drop_index(op.f('ix_applicants_email'), table_name='applicants')
    op.drop_table('applicants')
    op.drop_index(op.f('ix_password_reset_tokens_token_hash'), table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
    op.drop_index(op.f('ix_drives_link_token'), table_name='drives')
    op.drop_table('drives')
    op.drop_index(op.f('ix_organisations_email'), table_name='organisations')
    op.drop_table('organisations')
    for enum_name in (
        "email_type_enum",
        "applicant_status_enum",
        "drive_status_enum",
        "question_level_enum",
        "task_type_enum",
    ):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
