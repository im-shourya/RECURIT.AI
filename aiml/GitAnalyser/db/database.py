"""
Database configuration and session management.
Uses async SQLAlchemy with SQLite.
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from sqlalchemy.engine import Engine

DATABASE_URL = "sqlite+aiosqlite:///./app.db"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for getting database sessions."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database and enable foreign keys."""
    async with engine.begin() as conn:
        # Enable foreign keys for SQLite
        await conn.exec_driver_sql("PRAGMA foreign_keys = ON;")
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)