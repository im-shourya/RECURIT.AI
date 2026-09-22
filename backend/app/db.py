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

    await init_beanie(
        database=_client[settings.MONGODB_DB],
        document_models=ALL_DOCUMENTS,
    )
    log.info("connected to MongoDB", extra={"database": settings.MONGODB_DB})


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
