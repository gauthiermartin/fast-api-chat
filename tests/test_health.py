"""Tests for health endpoint."""

import pytest


def test_health_check_success(client):
    """Test successful health check."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "fastapi-chat"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data

def test_health_check_response_model(client, mock_datetime):
    """Test health check response matches expected model."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()
    expected_timestamp = mock_datetime.isoformat()

    assert data == {
        "status": "healthy",
        "timestamp": expected_timestamp,
        "service": "fastapi-chat",
        "version": "0.1.0"
    }

def test_health_check_content_type(client):
    """Test health check returns correct content type."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

@pytest.mark.asyncio
async def test_health_check_logs(client, caplog):
    """Test health check generates appropriate logs."""
    with caplog.at_level("INFO"):
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert "Health check requested" in caplog.text
    assert "Health check completed successfully" in caplog.text
