"""Health check router for FastAPI application."""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

class HealthResponse(BaseModel):
    """Health response model."""
    status: str
    timestamp: datetime
    service: str
    version: str

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns:
        HealthResponse: Current health status of the application

    Raises:
        HTTPException: If service is unhealthy
    """
    try:
        logger.info("Health check requested")

        response = HealthResponse(
            status="healthy",
            timestamp=datetime.now(),
            service="fastapi-chat",
            version="0.1.0"
        )

        logger.info("Health check completed successfully")
        return response

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Service unhealthy"
        )
