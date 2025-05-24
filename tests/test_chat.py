"""Tests for chat endpoint."""

import pytest
import json
from fastapi.testclient import TestClient


def test_chat_endpoint_non_streaming(client):
    """Test chat endpoint with non-streaming response."""
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Hello, world!",
            "stream": False
        }
    )

    assert response.status_code == 200

    data = response.json()
    assert data["object"] == "chat.completion"
    assert data["model"] == "fastapi-chat"
    assert "choices" in data
    assert len(data["choices"]) == 1
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert "Hello" in data["choices"][0]["message"]["content"]  # Should contain "Hello" since message contains "hello"


def test_chat_endpoint_streaming(client):
    """Test chat endpoint with streaming response."""
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Hello, how are you?",
            "stream": True
        }
    )

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]

    # Check that response is streaming
    content = response.text
    assert "data: " in content
    assert "chat.completion.chunk" in content
    assert "[DONE]" in content


def test_chat_endpoint_validation_empty_message(client):
    """Test chat endpoint with empty message."""
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "",
            "stream": True
        }
    )

    assert response.status_code == 422  # Validation error


def test_chat_endpoint_validation_long_message(client):
    """Test chat endpoint with message that's too long."""
    long_message = "a" * 2001  # Exceeds max_length of 2000

    response = client.post(
        "/api/v1/chat",
        json={
            "message": long_message,
            "stream": True
        }
    )

    assert response.status_code == 422  # Validation error


def test_chat_endpoint_different_responses(client):
    """Test that different messages produce different responses."""
    test_cases = [
        ("hello", "Hello"),
        ("what's the weather like?", "weather"),
        ("what time is it?", "time"),
        ("random question", "You said")
    ]

    for message, expected_keyword in test_cases:
        response = client.post(
            "/api/v1/chat",
            json={
                "message": message,
                "stream": False
            }
        )

        assert response.status_code == 200
        data = response.json()
        response_content = data["choices"][0]["message"]["content"]
        assert expected_keyword.lower() in response_content.lower()


def test_chat_info_endpoint(client):
    """Test chat info endpoint."""
    response = client.get("/api/v1/chat/info")

    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "fastapi-chat"
    assert data["version"] == "0.1.0"
    assert "description" in data
    assert "supported_features" in data
    assert "usage" in data

    # Check supported features
    features = data["supported_features"]
    assert "streaming_responses" in features
    assert "server_sent_events" in features
    assert "openai_compatible_format" in features


def test_chat_endpoint_streaming_format(client):
    """Test that streaming response follows proper SSE format."""
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "test",
            "stream": True
        }
    )

    assert response.status_code == 200
    content = response.text

    # Check for proper SSE format
    lines = content.split('\n')
    data_lines = [line for line in lines if line.startswith('data: ')]

    # Should have multiple data lines
    assert len(data_lines) > 1

    # Last line should be [DONE]
    assert any("[DONE]" in line for line in data_lines)

    # Check that JSON chunks are valid
    json_chunks = []
    for line in data_lines:
        if line.startswith('data: ') and not line.endswith('[DONE]'):
            try:
                json_data = json.loads(line[6:])  # Remove 'data: ' prefix
                json_chunks.append(json_data)
            except json.JSONDecodeError:
                if not line.endswith('[DONE]'):
                    pytest.fail(f"Invalid JSON in line: {line}")

    # Should have at least one valid JSON chunk
    assert len(json_chunks) > 0

    # Check structure of first chunk
    first_chunk = json_chunks[0]
    assert first_chunk["object"] == "chat.completion.chunk"
    assert first_chunk["model"] == "fastapi-chat"
    assert "choices" in first_chunk
    assert len(first_chunk["choices"]) == 1


@pytest.mark.asyncio
async def test_chat_endpoint_logs(client, caplog):
    """Test chat endpoint generates appropriate logs."""
    with caplog.at_level("INFO"):
        response = client.post(
            "/api/v1/chat",
            json={
                "message": "Hello, test!",
                "stream": True
            }
        )

    assert response.status_code == 200
    assert "Chat endpoint called" in caplog.text
    assert "Processing chat message" in caplog.text
