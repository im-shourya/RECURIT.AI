"""
Pytest configuration and fixtures.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient

from main import app
from db.database import Base


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_github_response():
    """Mock GitHub API response."""
    return {
        "id": 123456,
        "name": "test-repo",
        "full_name": "test-owner/test-repo",
        "owner": {"login": "test-owner"},
        "description": "Test repository",
        "language": "Python",
        "stargazers_count": 100,
        "forks_count": 50,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-15T00:00:00Z"
    }


@pytest.fixture
def mock_gemini_analysis():
    """Mock Gemini analysis response."""
    return {
        "summary": "Test repository for testing purposes",
        "purpose": "Testing",
        "tech_stack": [
            {"name": "Python", "category": "language", "version": "3.9+"}
        ],
        "primary_language": "Python",
        "architecture_pattern": "MVC",
        "components": [
            {"name": "API", "purpose": "REST API", "files": ["main.py"]}
        ],
        "data_flow": "Request -> Handler -> Response",
        "key_files": [
            {"path": "main.py", "role": "entry_point", "purpose": "Application entry"}
        ],
        "setup_steps": ["pip install -r requirements.txt", "python main.py"],
        "contribution_areas": ["Documentation", "Tests"],
        "risky_areas": ["Database migrations"],
        "known_issues": ["None"],
        "confidence_score": 0.9
    }
