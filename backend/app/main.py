"""
RECRUIT.AI — Main Application Entry Point
Registers all routers, configures CORS, and creates database tables on startup.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import create_tables
from app.routers import auth, drives, applicants, applicant_admin, interviews, analytics


# ── Lifespan: create tables on startup ──
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 RECRUIT.AI Backend starting up (env: {settings.ENVIRONMENT})...")

    if settings.AUTO_CREATE_TABLES:
        # Convenience for a throwaway local database. create_all() only ever
        # creates missing tables — it never alters an existing one — so
        # relying on it in a deployed environment means a changed column is
        # silently skipped and the app runs against a schema it expects but
        # does not have.
        create_tables()
        print("⚠️  AUTO_CREATE_TABLES is on: tables created from models.")
        print("    Do not use this where data matters; run migrations instead.")
    else:
        print("📦 Schema is managed by Alembic. Apply with: alembic upgrade head")

    yield
    print("👋 RECRUIT.AI Backend shutting down...")


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
def health_check():
    return {"status": "healthy"}
