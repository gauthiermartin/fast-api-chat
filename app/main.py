"""FastAPI main application module."""

import logging
import sys  # Add this import
from contextlib import asynccontextmanager
from pathlib import Path  # Added
from fastapi import FastAPI
from app.routers import health, chat, claims
from app.models.database import create_db_and_tables, get_engine
from app.database.load_data import CSVDataImporter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the project root and data file path
# Assumes app/main.py is one level down from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE_PATH = PROJECT_ROOT / "data" / "insurance_claims.csv"

# Add project root to sys.path for robust module resolution
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("FastAPI Chat application starting up...")
    logger.info("Initializing database tables...")
    try:
        create_db_and_tables()
        logger.info("Database tables initialized successfully")

        # Check if data file exists and then import
        logger.info(f"Checking for data file at: {DATA_FILE_PATH}")
        if DATA_FILE_PATH.is_file():
            logger.info("Data file found. Attempting to import CSV data...")
            try:
                # Import data into the database
                importer = CSVDataImporter(csv_file=str(DATA_FILE_PATH), db_connection=get_engine())
                importer.load_csv_data()
                data_records = importer.prepare_data_for_import()
                importer.import_data(data_records)
                logger.info("Data imported successfully")
            except Exception as e:
                logger.error(f"Error importing data: {e}")
        else:
            logger.info(f"Data file not found at {DATA_FILE_PATH}. Skipping data import.")

    except Exception as e:
        logger.error(f"Failed to initialize database or run import script: {e}")
        import traceback
        logger.error(traceback.format_exc())
    yield
    # Shutdown
    logger.info("FastAPI Chat application shutting down...")


# Create FastAPI application
app = FastAPI(
    title="FastAPI Insurance Claims",
    description="A FastAPI application for managing insurance claims with chat functionality",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(claims.router, prefix="/api/v1", tags=["claims"])
