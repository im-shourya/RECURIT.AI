"""add submit_token and interview expiry

Two security columns:

  applicants.submit_token  — unguessable capability token for the public
      submission endpoint, which previously accepted a bare applicant UUID
  interviews.expires_at    — interview links previously never expired

Both are nullable so that rows created before this migration keep working:
an existing interview with a NULL expires_at is treated as "no expiry set"
rather than as already expired, and existing applicants are backfilled with
a generated token below.

Revision ID: 0002_security_tokens
Revises: baseline_0001
Create Date: 2026-09-22
"""

import secrets

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_security_tokens"
down_revision = "baseline_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("applicants", sa.Column("submit_token", sa.String(length=64), nullable=True))
    op.create_index(
        op.f("ix_applicants_submit_token"), "applicants", ["submit_token"], unique=True
    )
    op.add_column(
        "interviews", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True)
    )

    # Backfill: every existing applicant needs a token, or their submission
    # link stops working. Generated per row rather than in SQL so the values
    # come from the same CSPRNG the application uses.
    #
    # Skipped when rendering offline SQL (`alembic upgrade --sql`), which has
    # no connection to read existing rows from. An offline run therefore
    # produces the DDL only, and the backfill must be applied online.
    if op.get_context().as_sql:
        print("-- NOTE: submit_token backfill skipped in offline mode; run online to populate existing rows")
        return

    connection = op.get_bind()
    applicants = sa.table(
        "applicants",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("submit_token", sa.String),
    )
    for (applicant_id,) in connection.execute(sa.select(applicants.c.id)).fetchall():
        connection.execute(
            applicants.update()
            .where(applicants.c.id == applicant_id)
            .values(submit_token=secrets.token_urlsafe(32))
        )


def downgrade() -> None:
    op.drop_column("interviews", "expires_at")
    op.drop_index(op.f("ix_applicants_submit_token"), table_name="applicants")
    op.drop_column("applicants", "submit_token")
