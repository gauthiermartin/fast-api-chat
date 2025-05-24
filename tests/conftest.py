"""Shared test fixtures and configuration."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from app.main import app


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
