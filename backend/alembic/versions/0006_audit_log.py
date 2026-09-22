"""add audit log

Hiring decisions previously left no trace: nothing recorded who rejected a
candidate or when, which matters for resolving internal disputes and for
answering a candidate who asks why.

Deliberately no foreign key to applicants. The table has to outlive the rows
it describes, so erasing a candidate cannot also erase the record that they
were erased. The subject is stored as an id plus a label captured at the time.

Revision ID: 0006_audit_log
Revises: 0005_email_outbox
Create Date: 2026-09-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_audit_log"
down_revision = "0005_email_outbox"
branch_labels = None
depends_on = None

_ACTIONS = (
    "applicant.selected",
    "applicant.rejected",
    "applicant.deleted",
    "drive.created",
    "drive.updated",
    "drive.deleted",
    "org.password_changed",
)

audit_action_enum = sa.Enum(*_ACTIONS, name="audit_action_enum")
audit_action_column = postgresql.ENUM(*_ACTIONS, name="audit_action_enum", create_type=False)


def upgrade() -> None:
    audit_action_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "audit_log",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("action", audit_action_column, nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=True),
        sa.Column("entity_label", sa.String(length=255), nullable=True),
        sa.Column("detail", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_log_org_id"), "audit_log", ["org_id"])
    op.create_index(op.f("ix_audit_log_action"), "audit_log", ["action"])
    op.create_index(op.f("ix_audit_log_created_at"), "audit_log", ["created_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_log_created_at"), table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_action"), table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_org_id"), table_name="audit_log")
    op.drop_table("audit_log")
    audit_action_enum.drop(op.get_bind(), checkfirst=True)
