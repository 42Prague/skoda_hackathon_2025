"""
Async Test Configuration
------------------------
Pytest fixtures for async testing of all components.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel
from httpx import AsyncClient
from fastapi import FastAPI

from swx_api.core.config.settings import settings
from swx_api.core.main import app
from swx_api.core.database.db import get_async_session
from swx_api.app.models.skill_models import (
    EmployeeRecord,
    SkillAnalysisRecord,
    DatasetRecord,
    LearningHistory,
    AuditLog
)


# Test database URL (in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create async test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

# Create async test session factory
TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create async test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    async with TestAsyncSessionLocal() as session:
        yield session
        await session.rollback()
    
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(scope="function")
async def test_app() -> FastAPI:
    """Create test FastAPI app with test database."""
    # Override get_async_session dependency
    async def override_get_session():
        async with TestAsyncSessionLocal() as session:
            yield session
    
    app.dependency_overrides[get_async_session] = override_get_session
    
    yield app
    
    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def sample_employee_data():
    """Sample employee data for testing."""
    return {
        "employee_id": "EMP001",
        "department": "Engineering",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "metadata": {"experience_years": 5}
    }


@pytest.fixture
async def sample_employees_data():
    """Multiple sample employees for testing."""
    return [
        {
            "employee_id": "EMP001",
            "department": "Engineering",
            "skills": ["Python", "FastAPI", "PostgreSQL"],
        },
        {
            "employee_id": "EMP002",
            "department": "Engineering",
            "skills": ["JavaScript", "React", "Node.js"],
        },
        {
            "employee_id": "EMP003",
            "department": "Data Science",
            "skills": ["Python", "Machine Learning", "TensorFlow"],
        },
    ]


@pytest.fixture
def temp_data_dir(tmp_path: Path):
    """Create temporary data directory for file I/O tests."""
    data_dir = tmp_path / "data"
    (data_dir / "raw").mkdir(parents=True)
    (data_dir / "normalized").mkdir(parents=True)
    (data_dir / "processed").mkdir(parents=True)
    (data_dir / "logs").mkdir(parents=True)
    return data_dir
