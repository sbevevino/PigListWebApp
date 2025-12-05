"""
Pytest configuration and shared fixtures.

This module provides test fixtures and configuration for the test suite.
Fixtures handle test database setup, client creation, and authentication.
"""

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator, Generator

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.base import Base, get_db
from app.core.config import settings
from app.models.user import User
from app.core.security import get_password_hash

# Test database URL (separate from development database)
# Use same credentials as dev database, just different database name
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    "piglist_dev",
    "piglist_test"
)
# Ensure we're using the correct password (piglist_dev_pass, not piglist_test_pass)
if "piglist_test_pass" in TEST_DATABASE_URL:
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace(
        "piglist_test_pass",
        "piglist_dev_pass"
    )

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create event loop for async tests.

    Session-scoped event loop for running async tests.
    Required for pytest-asyncio
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """
    Create test database engine.

    Creates a fresh database engine for each test function.
    Tables are created before the test and dropped after.
    """
    # Create async engine with NullPull (no connection pooling for tests)
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Dispose of engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session.

    Provides a database session for each test function.
    Session is automatically rolled back after the test.
    """
    # Create session factory
    async_session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Create and yield session
    async with async_session_maker() as session:
        yield session

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test client with database override.

    Provides an async HTTP client for testing API endpoints.
    Database dependency is overridden to use test database.
    """
    # Override database dependency
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db

    # Create and yield client
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # Clear overrides
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """
    Create a test user in the database.

    Provides a pre-created user for testing authentication and protected endpoints.
    """
    user = User(
        email="testuser@example.com",
        password_hash=get_password_hash("TestPass123"),
        display_name="Test User",
        is_active=True
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user

@pytest_asyncio.fixture
async def auth_token(
    client: AsyncClient,
    test_user: User
) -> str:
    """
    Get authentication token for test user.

    Logs in the test user and returns the access token for testing protected endpoints.
    """
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "TestPass123"
        }
    )

    return response.json()["access_token"]

@pytest_asyncio.fixture
async def auth_headers(auth_token: str) -> dict:
    """
    Get authorization headers with token.

    Provides properly formatted authorization headers for testing protected endpoints.
    """
    return {"Authorization": f"Bearer {auth_token}"}