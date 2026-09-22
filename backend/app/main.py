"""
RECRUIT.AI — Main Application Entry Point
Registers all routers, configures CORS, and creates database tables on startup.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from app.db import create_tables, engine
from app.error_tracking import configure_error_tracking
from app.logging_config import configure_logging
from app.routers import auth, drives, applicants, applicant_admin, interviews, analytics


# ── Lifespan: create tables on startup ──
settings = get_settings()

configure_logging()
configure_error_tracking()
log = logging.getLogger("recruit.startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("starting up", extra={"environment": settings.ENVIRONMENT})

    if settings.AUTO_CREATE_TABLES:
        # Convenience for a throwaway local database. create_all() only ever
        # creates missing tables — it never alters an existing one — so
        # relying on it in a deployed environment means a changed column is
        # silently skipped and the app runs against a schema it expects but
        # does not have.
        create_tables()
        log.warning(
            "AUTO_CREATE_TABLES is on: tables created from models. "
            "Do not use this where data matters; run migrations instead."
        )
    else:
        log.info("schema managed by Alembic (alembic upgrade head)")

    yield
    log.info("shutting down")


# ── FastAPI App ──
app = FastAPI(
    title="RECRUIT.AI",
    description="AI-powered recruitment platform for college clubs and organisations",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS ──
# "*" cannot be combined with allow_credentials: the CORS spec forbids a
# wildcard on a credentialed response, so browsers reject every such request.
# The previous config paired them, which meant the permissive setting did not
# even work — it only looked permissive.
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


# ── Register Routers ──
app.include_router(auth.router, prefix="/api")
app.include_router(drives.router, prefix="/api")
app.include_router(applicants.router, prefix="/api")
app.include_router(applicant_admin.router, prefix="/api")
app.include_router(interviews.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")


# ── Health Check ──
@app.get("/", tags=["Health"])
def root():
    return {
        "service": "RECRUIT.AI Backend",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check(response: Response):
    """
    Liveness plus a real dependency check.

    This used to return {"status": "healthy"} unconditionally, so it stayed
    green while the database was unreachable — exactly when an orchestrator
    most needs to know. It now runs SELECT 1 and reports 503 if that fails,
    so a failed deploy is caught rather than rolled out.
    """
    checks = {"database": "ok"}
    healthy = True

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        # The reason is logged; the response stays generic so an unauthenticated
        # probe cannot read connection strings or internal hostnames back.
        healthy = False
        checks["database"] = "unavailable"
        logging.getLogger("recruit.health").error(
            "database health check failed", extra={"error": type(exc).__name__}
        )

    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {"status": "healthy" if healthy else "degraded", "checks": checks}
