"""Shared test fixtures and configuration."""

import pytest
import sqlite3
from fastapi.testclient import TestClient
from datetime import datetime
from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel
from fastapi import FastAPI
from app.main import app
from app.routers.claims import get_session
from app.routers import health, chat, claims


# Test database configuration - Use SQLite in memory for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for datetime handling."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_test_session():
    """Get test database session."""
    with Session(engine) as session:
        yield session


@pytest.fixture(scope="function")
def test_client():
    """Create test client with test database."""
    # Create a new FastAPI app without lifespan for testing
    test_app = FastAPI(
        title="FastAPI Insurance Claims Test",
        description="Test application for insurance claims",
        version="0.1.0",
    )

    # Include routers
    test_app.include_router(health.router, prefix="/api/v1", tags=["health"])
    test_app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
    test_app.include_router(claims.router, prefix="/api/v1", tags=["claims"])

    # Create test database tables
    SQLModel.metadata.create_all(engine)

    # Override the database dependency
    test_app.dependency_overrides[get_session] = get_test_session

    with TestClient(test_app) as client:
        yield client

    # Clean up
    test_app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def client():
    """Create test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_datetime(monkeypatch):
    """Mock datetime for consistent testing."""
    fixed_datetime = datetime(2023, 1, 1, 12, 0, 0)

    class MockDateTime:
        @classmethod
        def now(cls):
            return fixed_datetime

    monkeypatch.setattr("app.routers.health.datetime", MockDateTime)
    return fixed_datetime
