"""
Tests that the Alembic baseline still matches the models.

The baseline was generated from app/models/database.py rather than written by
hand. These tests catch the drift that follows: a model changed without a
matching migration, which on a populated database means the app expects a
column the database does not have.

They parse the migration source rather than executing it, so no database is
needed.
"""

import ast
import pathlib

import pytest

from app.config import get_settings
from app.models.database import Base

MIGRATIONS_DIR = pathlib.Path(__file__).resolve().parents[1] / "alembic" / "versions"
BASELINE = MIGRATIONS_DIR / "baseline_0001_baseline_schema.py"


def _baseline_tree() -> ast.AST:
    return ast.parse(BASELINE.read_text())


def _created_tables() -> dict[str, set[str]]:
    """Map table name -> column names, as declared by op.create_table calls."""
    tables: dict[str, set[str]] = {}
    for node in ast.walk(_baseline_tree()):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "create_table"):
            continue
        if not node.args or not isinstance(node.args[0], ast.Constant):
            continue

        name = node.args[0].value
        columns: set[str] = set()
        for arg in node.args[1:]:
            if (
                isinstance(arg, ast.Call)
                and isinstance(arg.func, ast.Attribute)
                and arg.func.attr == "Column"
                and arg.args
                and isinstance(arg.args[0], ast.Constant)
            ):
                columns.add(arg.args[0].value)
        tables[name] = columns
    return tables


# ──────────────────────────────────────────────
# The migration exists at all
# ──────────────────────────────────────────────
def test_a_migration_exists():
    """
    Alembic was configured but `versions/` was empty, so nothing was ever
    migrated and the schema depended entirely on create_all().
    """
    revisions = [p for p in MIGRATIONS_DIR.glob("*.py") if p.name != "__init__.py"]
    assert revisions, "no Alembic revisions found"


def test_baseline_is_the_root_revision():
    src = BASELINE.read_text()
    assert "down_revision = None" in src


def test_migration_parses():
    _baseline_tree()


# ──────────────────────────────────────────────
# Parity with the models
# ──────────────────────────────────────────────
def test_every_model_table_is_in_the_baseline():
    """A new model without a migration fails here rather than in production."""
    migrated = set(_created_tables())
    declared = set(Base.metadata.tables)
    assert declared - migrated == set(), (
        f"models define tables with no migration: {sorted(declared - migrated)}"
    )


def test_baseline_creates_no_table_the_models_do_not_define():
    migrated = set(_created_tables())
    declared = set(Base.metadata.tables)
    assert migrated - declared == set(), (
        f"migration creates unknown tables: {sorted(migrated - declared)}"
    )


@pytest.mark.parametrize("table_name", sorted(Base.metadata.tables))
def test_columns_match_the_model(table_name):
    """
    Column-level parity. This is the case that actually bites: a column added
    to a model with no migration behind it.
    """
    migrated = _created_tables().get(table_name, set())
    declared = {c.name for c in Base.metadata.tables[table_name].columns}
    assert declared == migrated, (
        f"{table_name}: only in model {sorted(declared - migrated)}, "
        f"only in migration {sorted(migrated - declared)}"
    )


def test_downgrade_drops_the_enum_types():
    """
    Dropping a table leaves its PostgreSQL enum type behind, so a downgrade
    followed by an upgrade would fail on "type already exists".
    """
    src = BASELINE.read_text()
    for enum_name in (
        "task_type_enum",
        "question_level_enum",
        "drive_status_enum",
        "applicant_status_enum",
        "email_type_enum",
    ):
        assert enum_name in src, f"downgrade does not drop {enum_name}"


# ──────────────────────────────────────────────
# create_all must not be the default
# ──────────────────────────────────────────────
def test_auto_create_tables_is_off_by_default():
    """
    create_all() never alters an existing table, so leaving it on in a
    deployed environment hides schema drift instead of surfacing it.
    """
    assert get_settings().AUTO_CREATE_TABLES is False
