"""
RECRUIT.AI — Database Connection
Motor client and Beanie initialisation.

Replaces the SQLAlchemy engine and per-request session. Motor is async and
holds its own connection pool, so there is no session to open, hand to a
request and close again — documents are fetched through the model classes
directly.

That removes the get_db dependency every route used to declare. Routes that
still take one are unaffected callers of a no-op shim kept during the
transition; new code should not use it.
"""

import logging
from typing import Optional

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings
from app.models.documents import ALL_DOCUMENTS

settings = get_settings()
log = logging.getLogger("recruit.db")

_client: Optional[AsyncIOMotorClient] = None


def get_client() -> AsyncIOMotorClient:
    """The process-wide Motor client."""
    if _client is None:
        raise RuntimeError("MongoDB client is not initialised; call connect() first")
    return _client


async def connect() -> None:
    """
    Open the connection pool and register the document models.

    init_beanie also creates the indexes declared on each model. That is the
    closest thing MongoDB has to running a migration, and it is why the
    uniqueness rules that used to be table constraints still hold: they are
    now unique indexes, created here on every boot.
    """
    global _client

    _client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        uuidRepresentation="standard",
        serverSelectionTimeoutMS=settings.MONGODB_TIMEOUT_MS,
    )

    database = _client[settings.MONGODB_DB]
    await drop_superseded_indexes(database)
    await init_beanie(database=database, document_models=ALL_DOCUMENTS)
    log.info("connected to MongoDB", extra={"database": settings.MONGODB_DB})


# Indexes a model used to declare and no longer does. init_beanie only ever
# creates indexes, so without this a retired unique index keeps enforcing its
# rule in every existing deployment.
SUPERSEDED_INDEXES = {
    # Email was unique across the whole deployment, which stopped anyone
    # belonging to two organisations. Now unique per organisation.
    "users": ["email_1"],
    # A plain created_at index, replaced by a TTL index on the same key that
    # gives the audit log a retention period.
    "audit_log": ["created_at_-1"],
}


async def drop_superseded_indexes(database) -> None:
    """Drop retired indexes that are still present. Safe to run on every boot."""
    for collection, names in SUPERSEDED_INDEXES.items():
        try:
            existing = await database[collection].index_information()
        except Exception as exc:
            log.error(
                "could not read indexes",
                extra={"collection": collection, "error": type(exc).__name__},
            )
            continue
        for name in names:
            if name in existing:
                await database[collection].drop_index(name)
                log.info("dropped superseded index", extra={"collection": collection, "index": name})


async def disconnect() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


async def ping() -> bool:
    """True when the server answers. Used by the health check."""
    if _client is None:
        return False
    await _client.admin.command("ping")
    return True
