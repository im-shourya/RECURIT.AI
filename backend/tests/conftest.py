"""
Shared test fixtures.

The Postgres suite could never touch a database: the models needed PostgreSQL
types that SQLite cannot host, and no server was available, so anything
DB-shaped was asserted against fakes or source text.

mongomock_motor runs an in-process MongoDB stand-in that Beanie initialises
against normally, so these tests execute real queries — filters, sorts,
projections and index-backed uniqueness — without a server. Coverage is
genuinely better after the move, not worse.

Known limits of the stand-in: it does not enforce unique indexes. Tests that
care about uniqueness assert the index is *declared*, and the real enforcement
is noted as unverified.
"""

import asyncio
from datetime import date, timedelta

import pytest
import pytest_asyncio
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient

from app.models.documents import (
    ALL_DOCUMENTS,
    Applicant,
    Drive,
    Organisation,
    TaskType,
    User,
    UserRole,
)
from app.services.auth_service import hash_password


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db():
    """A clean in-process database for each test."""
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client["recruit_ai_test"], document_models=ALL_DOCUMENTS
    )
    yield client


@pytest_asyncio.fixture
async def org(db) -> Organisation:
    organisation = Organisation(name="Sparkles Ltd", email="org@example.com")
    await organisation.insert()
    return organisation


@pytest_asyncio.fixture
async def owner(org) -> User:
    user = User(
        org_id=org.id,
        name="Owner",
        email="owner@example.com",
        password_hash=hash_password("correct-horse"),
        role=UserRole.OWNER,
    )
    await user.insert()
    return user


@pytest_asyncio.fixture
async def other_org(db) -> Organisation:
    """A second organisation, for checking that scoping actually holds."""
    organisation = Organisation(name="Rival Inc", email="rival@example.com")
    await organisation.insert()
    return organisation


@pytest_asyncio.fixture
async def drive(org) -> Drive:
    record = Drive(
        org_id=org.id,
        name="Frontend Engineer",
        domain="Web Development",
        task_type=TaskType.TASK,
        task_description="Build a small dashboard.",
        apply_deadline=date.today() + timedelta(days=7),
        task_deadline=date.today() + timedelta(days=14),
        link_token="drive-link-token",
    )
    await record.insert()
    return record


@pytest_asyncio.fixture
async def applicant(drive) -> Applicant:
    record = Applicant(
        drive_id=drive.id,
        org_id=drive.org_id,
        name="Alex Developer",
        email="alex@example.com",
        reg_no="REG-1",
        skills=["React", "TypeScript"],
        primary_domain="Web Development",
        submit_token="submit-token-alex",
    )
    await record.insert()
    return record
