"""
RECRUIT.AI — Main Application Entry Point
Registers routers, configures CORS, and manages the MongoDB connection.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware

from app import db
from app.config import get_settings
from app.error_tracking import configure_error_tracking
from app.logging_config import configure_logging
from app.routers import (
    analytics, applicant_admin, applicants, audit, auth, drives, interviews, team,
)
from app.services import email_outbox

settings = get_settings()

configure_logging()
configure_error_tracking()
log = logging.getLogger("recruit.startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("starting up", extra={"environment": settings.ENVIRONMENT})

    # Opens the connection pool and creates the indexes declared on each
    # document. Those indexes are what still enforce the uniqueness rules that
    # used to be table constraints, so this is not optional setup.
    await db.connect()
    log.info("database ready; indexes applied")

    sweeper_stop = asyncio.Event()
    sweeper_task = None
    if settings.OUTBOX_SWEEPER_ENABLED:
        sweeper_task = asyncio.create_task(email_outbox.run_sweeper(sweeper_stop))
        log.info("email outbox sweeper started")

    yield

    if sweeper_task is not None:
        sweeper_stop.set()
        try:
            # Bounded so a stuck sweep cannot hold shutdown open indefinitely.
            await asyncio.wait_for(sweeper_task, timeout=5)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            sweeper_task.cancel()

    await db.disconnect()
    log.info("shutting down")


app = FastAPI(
    title="RECRUIT.AI",
    description="AI-powered recruitment platform for college clubs and organisations",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS ──
# "*" cannot be combined with allow_credentials: the CORS spec forbids a
# wildcard on a credentialed response, so browsers reject every such request.
_origins = [o.strip() for o in settings.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]

if "*" in _origins:
    raise RuntimeError(
        "CORS_ALLOWED_ORIGINS cannot be '*': a wildcard origin is invalid on "
        "credentialed requests and browsers will reject it. List the exact "
        "origins instead, comma-separated."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# ── Routers ──
app.include_router(auth.router, prefix="/api")
app.include_router(drives.router, prefix="/api")
app.include_router(applicants.router, prefix="/api")
app.include_router(applicant_admin.router, prefix="/api")
app.include_router(interviews.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(team.router, prefix="/api")


# ── Health ──
@app.get("/", tags=["Health"])
def root():
    return {
        "service": "RECRUIT.AI Backend",
        "status": "running",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check(response: Response):
    """
    Liveness plus a real dependency check.

    This used to return healthy unconditionally, so it stayed green while the
    database was unreachable — exactly when an orchestrator most needs to
    know.
    """
    checks = {"database": "ok"}
    healthy = True

    try:
        await db.ping()
    except Exception as exc:
        # The reason is logged; the response stays generic so an
        # unauthenticated probe cannot read connection strings back.
        healthy = False
        checks["database"] = "unavailable"
        logging.getLogger("recruit.health").error(
            "database health check failed", extra={"error": type(exc).__name__}
        )

    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {"status": "healthy" if healthy else "degraded", "checks": checks}
