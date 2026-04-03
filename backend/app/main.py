"""
RECRUIT.AI — Main Application Entry Point
Registers all routers, configures CORS, and creates database tables on startup.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import create_tables
from app.routers import auth, drives, applicants, interviews


# ── Lifespan: create tables on startup ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 RECRUIT.AI Backend starting up...")
    create_tables()
    print("✅ Database tables ready")
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Register Routers ──
app.include_router(auth.router, prefix="/api")
app.include_router(drives.router, prefix="/api")
app.include_router(applicants.router, prefix="/api")
app.include_router(interviews.router, prefix="/api")


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
