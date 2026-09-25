"""add organisation notification preference

organisations.notify_on_interview — whether to email the recruiting
organisation when a candidate finishes an interview.

Defaults to true, with a server_default so existing rows are backfilled by
the ALTER itself rather than left NULL. Opt-out rather than opt-in: a drive
owner who hears nothing assumes the platform is idle, which is the failure
this notification exists to prevent.

Revision ID: 0003_org_notifications
Revises: 0002_security_tokens
Create Date: 2026-09-22
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_org_notifications"
down_revision = "0002_security_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "organisations",
        sa.Column(
            "notify_on_interview",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    op.drop_column("organisations", "notify_on_interview")
