"""add users and roles

The organisation used to be the login: one email, one password, shared by
everyone who needed access. That forced password sharing, made it impossible
to tell who made a decision, and meant revoking one person's access changed it
for everybody.

Migration strategy — existing logins must keep working:

  Every organisation is given exactly one OWNER user carrying the SAME email
  and the SAME password hash. The hash is copied, never regenerated, so every
  current password continues to work and nobody is locked out or forced to
  reset.

organisations.email and organisations.password_hash are left in place. They
are no longer the credential, but dropping them in the same migration would
make rollback lossy — the columns are the only copy of that data if the users
table is dropped.

Revision ID: 0007_users_and_roles
Revises: 0006_audit_log
Create Date: 2026-09-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007_users_and_roles"
down_revision = "0006_audit_log"
branch_labels = None
depends_on = None

_ROLES = ("owner", "admin", "member")
user_role_enum = sa.Enum(*_ROLES, name="user_role_enum")
user_role_column = postgresql.ENUM(*_ROLES, name="user_role_enum", create_type=False)

_NEW_AUDIT_ACTIONS = ("member.invited", "member.role_changed", "member.removed")


def upgrade() -> None:
    user_role_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        # Nullable: an invited member has no password until they set one.
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("role", user_role_column, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_org_id"), "users", ["org_id"])
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.add_column(
        "password_reset_tokens", sa.Column("user_id", sa.UUID(), nullable=True)
    )
    op.create_foreign_key(
        "fk_password_reset_tokens_user_id",
        "password_reset_tokens",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Audit actions for member management.
    for action in _NEW_AUDIT_ACTIONS:
        op.execute(f"ALTER TYPE audit_action_enum ADD VALUE IF NOT EXISTS '{action}'")

    if op.get_context().as_sql:
        print(
            "-- NOTE: owner backfill skipped in offline mode. "
            "Run online, or every existing organisation will have no user and "
            "nobody will be able to sign in."
        )
        return

    # Backfill: one OWNER per organisation, copying the existing credential.
    op.execute(
        """
        INSERT INTO users (id, org_id, name, email, password_hash, role, is_active, created_at)
        SELECT gen_random_uuid(), o.id, o.name, o.email, o.password_hash,
               'owner'::user_role_enum, true, COALESCE(o.created_at, NOW())
        FROM organisations o
        WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.org_id = o.id)
        """
    )

    # Existing reset tokens point at an organisation; attach them to its owner
    # so a link already in someone's inbox still works.
    op.execute(
        """
        UPDATE password_reset_tokens t
        SET user_id = u.id
        FROM users u
        WHERE u.org_id = t.org_id AND t.user_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_password_reset_tokens_user_id", "password_reset_tokens", type_="foreignkey"
    )
    op.drop_column("password_reset_tokens", "user_id")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_org_id"), table_name="users")
    op.drop_table("users")
    user_role_enum.drop(op.get_bind(), checkfirst=True)
    # audit_action_enum values are intentionally left: PostgreSQL cannot drop
    # a value from an enum, and rows may already reference them.
