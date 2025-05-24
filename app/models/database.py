"""
Database models using SQLModel for the insurance claims system.
"""

from datetime import datetime, UTC
from decimal import Decimal
from typing import Optional
from sqlmodel import SQLModel, Field, create_engine
from sqlalchemy import Column, Numeric
import os

class InsuranceClaim(SQLModel, table=True):
    """SQLModel for insurance claims data."""

    __tablename__ = "insurance_claims"

    # Primary key
    claim_id: str = Field(primary_key=True, max_length=20, description="Unique claim identifier")

    # Policy information
    policy_id: str = Field(max_length=20, index=True, description="Policy identifier")

    # Customer demographics
    customer_age: int = Field(ge=18, le=120, description="Customer age")
    customer_gender: str = Field(max_length=1, regex="^[MF]$", description="Customer gender (M/F)")
    customer_state: str = Field(max_length=2, description="Customer state code")

    # Vehicle information
    vehicle_make: str = Field(max_length=50, description="Vehicle manufacturer")
    vehicle_model: str = Field(max_length=50, description="Vehicle model")
    vehicle_year: int = Field(ge=1900, le=2030, description="Vehicle year")

    # Claim details
    claim_date: datetime = Field(description="Date when claim was filed")
    claim_type: str = Field(max_length=50, description="Type of insurance claim")
    claim_amount: Decimal = Field(
        sa_column=Column(Numeric(12, 2)),
        ge=0,
        description="Claim amount in USD"
    )
    deductible: int = Field(ge=0, description="Deductible amount")
    claim_status: str = Field(max_length=30, description="Current status of the claim")

    # Financial information
    annual_premium: Decimal = Field(
        sa_column=Column(Numeric(10, 2)),
        ge=0,
        description="Annual premium amount"
    )

    # Fraud detection
    is_fraud: bool = Field(default=False, description="Fraud indicator")

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Record creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Record last update timestamp")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "claim_id": "CLM00000001",
                "policy_id": "POL000001",
                "customer_age": 35,
                "customer_gender": "M",
                "customer_state": "CA",
                "vehicle_make": "Toyota",
                "vehicle_model": "Sedan",
                "vehicle_year": 2020,
                "claim_date": "2024-01-15T10:30:00",
                "claim_type": "Collision",
                "claim_amount": 5000.00,
                "deductible": 1000,
                "claim_status": "Approved",
                "annual_premium": 1200.00,
                "is_fraud": False
            }
        }


# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:password@localhost:5433/insurance_claims"
)

# Create engine
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    """Create database tables."""
    SQLModel.metadata.create_all(engine)


def get_engine():
    """Get database engine."""
    return engine
