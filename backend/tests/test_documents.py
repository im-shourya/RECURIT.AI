"""
Tests for the MongoDB document model.

These run real queries against an in-process MongoDB stand-in, so they cover
behaviour the PostgreSQL suite could only assert against source text: filters
actually filter, embedded documents actually round-trip, and the scoping that
keeps one organisation out of another's data is executed rather than read.
"""

from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.documents import (
    Applicant,
    ApplicantStatus,
    AuditLog,
    Drive,
    EmailLogEntry,
    EmailType,
    Interview,
    Organisation,
    PasswordResetToken,
    Submission,
    TaskType,
    User,
    UserRole,
)


# ──────────────────────────────────────────────
# Round-tripping
# ──────────────────────────────────────────────
async def test_uuid_ids_survive_a_round_trip(applicant):
    """
    Ids stay UUIDs rather than becoming ObjectIds: they appear in links
    already sent to candidates and in audit entries that must keep resolving.
    """
    fetched = await Applicant.get(applicant.id)
    assert fetched is not None
    assert fetched.id == applicant.id
    assert str(fetched.id) == str(applicant.id)


async def test_embedded_submission_round_trips(applicant):
    """Submission was a separate table; it is now part of the applicant."""
    applicant.submission = Submission(
        github_url="https://github.com/alexdev/project",
        description="My project",
        repolens_analysis={"stars": 12, "languages": ["TypeScript"]},
    )
    await applicant.save()

    fetched = await Applicant.get(applicant.id)
    assert fetched.submission is not None
    assert fetched.submission.github_url == "https://github.com/alexdev/project"
    # Nested dicts must survive, since RepoLens output is free-form.
    assert fetched.submission.repolens_analysis["languages"] == ["TypeScript"]


async def test_embedded_interview_is_findable_by_token(applicant):
    """
    The interview is embedded but still reached by token alone — that is how
    the candidate opens it, and it is why the nested field is indexed.
    """
    applicant.interview = Interview(token="interview-token-xyz")
    await applicant.save()

    found = await Applicant.find_one({"interview.token": "interview-token-xyz"})
    assert found is not None
    assert found.id == applicant.id


async def test_email_logs_accumulate(applicant):
    applicant.email_logs.append(EmailLogEntry(type=EmailType.APPLIED))
    applicant.email_logs.append(EmailLogEntry(type=EmailType.INTERVIEW))
    await applicant.save()

    fetched = await Applicant.get(applicant.id)
    assert [e.type for e in fetched.email_logs] == [
        EmailType.APPLIED,
        EmailType.INTERVIEW,
    ]


def test_enum_values_serialise_as_the_same_strings():
    """
    Every enum subclasses str, which is what makes BSON store the value rather
    than a nested object — so stored data and API responses read exactly as
    they did under PostgreSQL.
    """
    assert issubclass(ApplicantStatus, str)
    assert ApplicantStatus.APPLIED == "applied"
    assert TaskType.GITHUB == "github"
    assert UserRole.OWNER == "owner"


# ──────────────────────────────────────────────
# Organisation scoping — executed, not inspected
# ──────────────────────────────────────────────
async def test_scoping_excludes_another_organisation(applicant, other_org):
    """
    The authorization boundary for every admin endpoint. Previously this could
    only be asserted by inspecting compiled SQL; here the query runs.
    """
    intruder = Applicant(
        drive_id=applicant.drive_id,
        org_id=other_org.id,
        name="Rival Candidate",
        email="rival@example.com",
        submit_token="other-token",
    )
    await intruder.insert()

    mine = await Applicant.find(Applicant.org_id == applicant.org_id).to_list()

    assert applicant.id in {a.id for a in mine}
    assert intruder.id not in {a.id for a in mine}


async def test_lookup_by_id_and_org_misses_across_organisations(applicant, other_org):
    """A correct id plus the wrong organisation must resolve to nothing."""
    found = await Applicant.find_one(
        Applicant.id == applicant.id, Applicant.org_id == other_org.id
    )
    assert found is None


# ──────────────────────────────────────────────
# Filtering and search
# ──────────────────────────────────────────────
async def test_status_filter(applicant, drive):
    other = Applicant(
        drive_id=drive.id,
        org_id=drive.org_id,
        name="Selected Person",
        email="selected@example.com",
        status=ApplicantStatus.SELECTED,
        submit_token="token-2",
    )
    await other.insert()

    selected = await Applicant.find(
        Applicant.org_id == drive.org_id,
        Applicant.status == ApplicantStatus.SELECTED,
    ).to_list()

    assert [a.id for a in selected] == [other.id]


async def test_counting_ignores_pagination(drive):
    for index in range(5):
        await Applicant(
            drive_id=drive.id,
            org_id=drive.org_id,
            name=f"Person {index}",
            email=f"person{index}@example.com",
            submit_token=f"token-{index}",
        ).insert()

    query = Applicant.find(Applicant.org_id == drive.org_id)
    total = await query.count()
    page = await query.limit(2).to_list()

    assert total == 5, "the count must be of the filtered set, not the page"
    assert len(page) == 2


# ──────────────────────────────────────────────
# Indexes
# ──────────────────────────────────────────────
def _indexes(document) -> list[tuple[set[str], bool]]:
    """(set of indexed field names, whether unique) for each declared index."""
    out = []
    for index in document.Settings.indexes:
        doc = index.document if hasattr(index, "document") else index
        out.append((set(doc["key"].keys()), bool(doc.get("unique", False))))
    return out


def test_duplicate_application_index_is_declared():
    """
    Replaces UNIQUE (drive_id, email). The handler checks before inserting,
    which is a read then a write, so only the index closes that race.
    """
    assert any(
        fields == {"drive_id", "email"} and unique
        for fields, unique in _indexes(Applicant)
    ), "no unique (drive_id, email) index declared"


def test_sign_in_email_is_uniquely_indexed():
    assert any(
        fields == {"email"} and unique for fields, unique in _indexes(User)
    ), "users.email must be uniquely indexed; it is the sign-in identifier"


def test_interview_token_is_indexed_on_the_parent():
    """Embedded, but still looked up by token alone."""
    assert any("interview.token" in fields for fields, _ in _indexes(Applicant))


def test_reset_tokens_expire_by_ttl():
    """
    MongoDB reaps expired tokens itself. Postgres had no equivalent, so spent
    tokens accumulated forever.
    """
    ttl = [
        index.document
        for index in PasswordResetToken.Settings.indexes
        if "expireAfterSeconds" in getattr(index, "document", {})
    ]
    assert ttl, "no TTL index on password_reset_tokens"


# ──────────────────────────────────────────────
# Audit independence
# ──────────────────────────────────────────────
async def test_audit_entry_outlives_its_subject(applicant, org):
    """
    The entry must survive deletion of what it describes, or erasing a
    candidate would also erase the record that they were erased. Under
    Postgres a foreign key would have cascaded it away; here there is no
    reference at all.
    """
    from app.models.documents import AuditAction

    await AuditLog(
        org_id=org.id,
        action=AuditAction.APPLICANT_DELETED,
        entity_type="applicant",
        entity_id=applicant.id,
        entity_label=applicant.name,
    ).insert()

    await applicant.delete()

    entries = await AuditLog.find(AuditLog.org_id == org.id).to_list()
    assert len(entries) == 1
    # The label is what keeps it readable: the id now resolves to nothing.
    assert entries[0].entity_label == "Alex Developer"
    assert await Applicant.get(applicant.id) is None
