"""Chat router for streaming responses."""

import asyncio
import json
import logging
from typing import AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    stream: bool = Field(default=True, description="Enable streaming response")


class ChatChunk(BaseModel):
    """Individual chunk of chat response."""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str = "fastapi-chat"
    choices: list[dict]


async def simulate_chat_response(message: str) -> AsyncGenerator[str, None]:
    """
    Simulate a streaming chat response.

    In a real implementation, this would integrate with an LLM API like OpenAI,
    Anthropic, or a local model.

    Args:
        message: The user's input message

    Yields:
        JSON-formatted chunks of the response
    """
    logger.info(f"Processing chat message: {message[:50]}...")

    # Simulate response based on user message
    if "hello" in message.lower():
        response_text = "Hello! How can I help you today? I'm a FastAPI chat bot ready to assist you with any questions you might have."
    elif "weather" in message.lower():
        response_text = "I'm sorry, I don't have access to real-time weather data. You might want to check a weather service for current conditions."
    elif "time" in message.lower():
        current_time = datetime.now().strftime("%H:%M:%S")
        response_text = f"The current time is {current_time}. Is there anything else I can help you with?"
    else:
        response_text = f"You said: '{message}'. That's interesting! I'm a simple chat bot, so I can only provide basic responses right now. How else can I assist you?"

    # Split response into words for streaming effect
    words = response_text.split()

    for i, word in enumerate(words):
        chunk_id = f"chatcmpl-{datetime.now().timestamp():.0f}-{i}"

        if i == 0:
            # First chunk
            chunk = ChatChunk(
                id=chunk_id,
                created=int(datetime.now().timestamp()),
                choices=[{
                    "index": 0,
                    "delta": {
                        "role": "assistant",
                        "content": word + " "
                    },
                    "finish_reason": None
                }]
            )
        elif i == len(words) - 1:
            # Last chunk
            chunk = ChatChunk(
                id=chunk_id,
                created=int(datetime.now().timestamp()),
                choices=[{
                    "index": 0,
                    "delta": {
                        "content": word
                    },
                    "finish_reason": "stop"
                }]
            )
        else:
            # Middle chunks
            chunk = ChatChunk(
                id=chunk_id,
                created=int(datetime.now().timestamp()),
                choices=[{
                    "index": 0,
                    "delta": {
                        "content": word + " "
                    },
                    "finish_reason": None
                }]
            )

        # Yield in Server-Sent Events format
        yield f"data: {chunk.model_dump_json()}\n\n"

        # Add realistic delay between words
        await asyncio.sleep(0.1)

    # Final chunk to indicate completion
    final_chunk = {
        "id": f"chatcmpl-{datetime.now().timestamp():.0f}-final",
        "object": "chat.completion.chunk",
        "created": int(datetime.now().timestamp()),
        "model": "fastapi-chat",
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": "stop"
        }]
    }

    yield f"data: {json.dumps(final_chunk)}\n\n"
    yield "data: [DONE]\n\n"

    logger.info("Chat response streaming completed")


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Stream a chat response to the user.

    This endpoint accepts a user message and returns a streaming response
    in the OpenAI-compatible Server-Sent Events (SSE) format.

    Args:
        request: Chat request containing the user message

    Returns:
        StreamingResponse: Streaming chat response in SSE format

    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        logger.info(f"Chat endpoint called with message length: {len(request.message)}")

        if not request.stream:
            # Non-streaming response (for compatibility)
            # Generate response using the same logic as streaming
            if "hello" in request.message.lower():
                response_text = "Hello! How can I help you today? I'm a FastAPI chat bot ready to assist you with any questions you might have."
            elif "weather" in request.message.lower():
                response_text = "I'm sorry, I don't have access to real-time weather data. You might want to check a weather service for current conditions."
            elif "time" in request.message.lower():
                current_time = datetime.now().strftime("%H:%M:%S")
                response_text = f"The current time is {current_time}. Is there anything else I can help you with?"
            else:
                response_text = f"You said: '{request.message}'. That's interesting! I'm a simple chat bot, so I can only provide basic responses right now. How else can I assist you?"

            response_data = {
                "id": f"chatcmpl-{datetime.now().timestamp():.0f}",
                "object": "chat.completion",
                "created": int(datetime.now().timestamp()),
                "model": "fastapi-chat",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }]
            }
            return JSONResponse(content=response_data)

        # Streaming response
        return StreamingResponse(
            simulate_chat_response(request.message),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8",
            }
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/chat/info")
async def chat_info():
    """
    Get information about the chat endpoint.

    Returns:
        dict: Information about the chat service
    """
    return {
        "service": "fastapi-chat",
        "version": "0.1.0",
        "description": "Streaming chat endpoint with OpenAI-compatible format",
        "supported_features": [
            "streaming_responses",
            "server_sent_events",
            "openai_compatible_format"
        ],
        "usage": {
            "endpoint": "/api/v1/chat",
            "method": "POST",
            "content_type": "application/json",
            "example_request": {
                "message": "Hello, how are you?",
                "stream": True
            }
        }
    }
