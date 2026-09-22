"""prevent duplicate applications to the same drive

The apply handler checks for an existing applicant before inserting, but that
is a read followed by a write: two requests arriving together can both pass
the check and create two rows for the same person. Only the database can
close that window.

Adds UNIQUE (drive_id, email).

If the table already contains duplicates this migration will fail, which is
the correct outcome — they need resolving before the constraint can hold. The
query to find them:

    SELECT drive_id, email, count(*)
    FROM applicants GROUP BY drive_id, email HAVING count(*) > 1;

Revision ID: 0004_apply_uniqueness
Revises: 0003_org_notifications
Create Date: 2026-09-22
"""

from alembic import op

revision = "0004_apply_uniqueness"
down_revision = "0003_org_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_applicant_drive_email", "applicants", ["drive_id", "email"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_applicant_drive_email", "applicants", type_="unique")
