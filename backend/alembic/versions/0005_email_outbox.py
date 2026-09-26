"""add email outbox

Emails were handed to FastAPI BackgroundTasks, which run in-process: a restart
between the response and the send lost the message, with no record it had ever
been attempted. For a result notification or a password reset link that is the
worst possible failure.

Every outbound email is now written here before delivery is attempted, so the
intent to send survives a restart. A sweeper retries anything left pending.

Revision ID: 0005_email_outbox
Revises: 0004_apply_uniqueness
Create Date: 2026-09-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_email_outbox"
down_revision = "0004_apply_uniqueness"
branch_labels = None
depends_on = None

email_status_enum = sa.Enum(
    "pending", "sent", "failed", name="email_status_enum"
)

# Referenced by the column with create_type=False. Without that the column
# definition emits its own CREATE TYPE alongside the explicit one above, which
# is harmless online (checkfirst) but produces a duplicate that fails when the
# migration is rendered to SQL and run as a script.
email_status_column_type = postgresql.ENUM(
    "pending", "sent", "failed", name="email_status_enum", create_type=False
)


def upgrade() -> None:
    email_status_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "email_outbox",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("to_email", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("html", sa.Text(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("status", email_status_column_type, nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_email_outbox_to_email"), "email_outbox", ["to_email"])
    # The sweeper only ever scans for pending rows, so this is the index that
    # keeps it from walking the whole table as sent mail accumulates.
    op.create_index(op.f("ix_email_outbox_status"), "email_outbox", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_email_outbox_status"), table_name="email_outbox")
    op.drop_index(op.f("ix_email_outbox_to_email"), table_name="email_outbox")
    op.drop_table("email_outbox")
    email_status_enum.drop(op.get_bind(), checkfirst=True)
