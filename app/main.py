"""FastAPI main application module."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import health, chat

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("FastAPI Chat application starting up...")
    yield
    # Shutdown
    logger.info("FastAPI Chat application shutting down...")

# Create FastAPI application
app = FastAPI(
    title="FastAPI Chat",
    description="A FastAPI application for chat functionality",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
