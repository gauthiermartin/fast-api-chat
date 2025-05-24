"""
Database router for insurance claims API.
Provides endpoints for managing insurance claims data.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from decimal import Decimal
from datetime import datetime, UTC
from pydantic import BaseModel, Field

from app.models.database import InsuranceClaim, get_engine


class InsuranceClaimResponse(BaseModel):
    """Response model for insurance claims."""
    claim_id: str
    policy_id: str
    customer_age: int
    customer_gender: str
    customer_state: str
    vehicle_make: str
    vehicle_model: str
    vehicle_year: int
    claim_date: datetime
    claim_type: str
    claim_amount: float  # Convert Decimal to float
    deductible: int
    claim_status: str
    annual_premium: float  # Convert Decimal to float
    is_fraud: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    @classmethod
    def from_db_model(cls, db_model: InsuranceClaim) -> "InsuranceClaimResponse":
        """Convert database model to response model."""
        return cls(
            claim_id=db_model.claim_id,
            policy_id=db_model.policy_id,
            customer_age=db_model.customer_age,
            customer_gender=db_model.customer_gender,
            customer_state=db_model.customer_state,
            vehicle_make=db_model.vehicle_make,
            vehicle_model=db_model.vehicle_model,
            vehicle_year=db_model.vehicle_year,
            claim_date=db_model.claim_date,
            claim_type=db_model.claim_type,
            claim_amount=float(db_model.claim_amount),
            deductible=db_model.deductible,
            claim_status=db_model.claim_status,
            annual_premium=float(db_model.annual_premium),
            is_fraud=db_model.is_fraud,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at
        )


class InsuranceClaimCreate(BaseModel):
    """Request model for creating insurance claims."""
    claim_id: str = Field(..., max_length=20)
    policy_id: str = Field(..., max_length=20)
    customer_age: int = Field(..., ge=18, le=120)
    customer_gender: str = Field(..., pattern="^[MF]$")
    customer_state: str = Field(..., max_length=2)
    vehicle_make: str = Field(..., max_length=50)
    vehicle_model: str = Field(..., max_length=50)
    vehicle_year: int = Field(..., ge=1900, le=2030)
    claim_date: datetime
    claim_type: str = Field(..., max_length=50)
    claim_amount: float = Field(..., ge=0)
    deductible: int = Field(..., ge=0)
    claim_status: str = Field(..., max_length=30)
    annual_premium: float = Field(..., ge=0)
    is_fraud: bool = False

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class InsuranceClaimUpdate(BaseModel):
    """Request model for updating insurance claims."""
    policy_id: Optional[str] = Field(None, max_length=20)
    customer_age: Optional[int] = Field(None, ge=18, le=120)
    customer_gender: Optional[str] = Field(None, pattern="^[MF]$")
    customer_state: Optional[str] = Field(None, max_length=2)
    vehicle_make: Optional[str] = Field(None, max_length=50)
    vehicle_model: Optional[str] = Field(None, max_length=50)
    vehicle_year: Optional[int] = Field(None, ge=1900, le=2030)
    claim_date: Optional[datetime] = None
    claim_type: Optional[str] = Field(None, max_length=50)
    claim_amount: Optional[float] = Field(None, ge=0)
    deductible: Optional[int] = Field(None, ge=0)
    claim_status: Optional[str] = Field(None, max_length=30)
    annual_premium: Optional[float] = Field(None, ge=0)
    is_fraud: Optional[bool] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

router = APIRouter(
    prefix="/claims",
    tags=["Insurance Claims"],
    responses={404: {"description": "Not found"}},
)


def get_session():
    """Get database session dependency."""
    engine = get_engine()
    with Session(engine) as session:
        yield session


@router.get("/", response_model=List[InsuranceClaimResponse])
async def get_claims(
    session: Session = Depends(get_session),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    claim_status: Optional[str] = Query(None, description="Filter by claim status"),
    is_fraud: Optional[bool] = Query(None, description="Filter by fraud indicator"),
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum claim amount"),
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum claim amount"),
):
    """Get insurance claims with optional filtering."""

    try:
        # Build query
        query = select(InsuranceClaim)

        # Apply filters
        if claim_status:
            query = query.where(InsuranceClaim.claim_status == claim_status)

        if is_fraud is not None:
            query = query.where(InsuranceClaim.is_fraud == is_fraud)

        if min_amount is not None:
            query = query.where(InsuranceClaim.claim_amount >= Decimal(str(min_amount)))

        if max_amount is not None:
            query = query.where(InsuranceClaim.claim_amount <= Decimal(str(max_amount)))

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        claims = session.exec(query).fetchall()
        return [InsuranceClaimResponse.from_db_model(claim) for claim in claims]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{claim_id}", response_model=InsuranceClaimResponse)
async def get_claim_by_id(
    claim_id: str,
    session: Session = Depends(get_session)
):
    """Get a specific insurance claim by ID."""

    try:
        claim = session.get(InsuranceClaim, claim_id)
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        return InsuranceClaimResponse.from_db_model(claim)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/", response_model=InsuranceClaimResponse)
async def create_claim(
    claim_data: InsuranceClaimCreate,
    session: Session = Depends(get_session)
):
    """Create a new insurance claim."""

    try:
        # Check if claim already exists
        existing_claim = session.get(InsuranceClaim, claim_data.claim_id)
        if existing_claim:
            raise HTTPException(status_code=400, detail="Claim ID already exists")

        # Create InsuranceClaim from the request data
        claim = InsuranceClaim(
            claim_id=claim_data.claim_id,
            policy_id=claim_data.policy_id,
            customer_age=claim_data.customer_age,
            customer_gender=claim_data.customer_gender,
            customer_state=claim_data.customer_state,
            vehicle_make=claim_data.vehicle_make,
            vehicle_model=claim_data.vehicle_model,
            vehicle_year=claim_data.vehicle_year,
            claim_date=claim_data.claim_date,
            claim_type=claim_data.claim_type,
            claim_amount=Decimal(str(claim_data.claim_amount)),
            deductible=claim_data.deductible,
            claim_status=claim_data.claim_status,
            annual_premium=Decimal(str(claim_data.annual_premium)),
            is_fraud=claim_data.is_fraud,
            created_at=datetime.now(UTC),
            updated_at=None
        )

        # Save to database
        session.add(claim)
        session.commit()
        session.refresh(claim)

        return InsuranceClaimResponse.from_db_model(claim)

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put("/{claim_id}", response_model=InsuranceClaimResponse)
async def update_claim(
    claim_id: str,
    updated_data: InsuranceClaimUpdate,
    session: Session = Depends(get_session)
):
    """Update an existing insurance claim."""

    try:
        # Get existing claim
        claim = session.get(InsuranceClaim, claim_id)
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")

        # Update fields
        update_dict = updated_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if field in ['claim_amount', 'annual_premium'] and value is not None:
                # Convert float to Decimal for monetary fields
                setattr(claim, field, Decimal(str(value)))
            else:
                setattr(claim, field, value)

        # Update timestamp
        claim.updated_at = datetime.now(UTC)

        # Save to database
        session.add(claim)
        session.commit()
        session.refresh(claim)

        return InsuranceClaimResponse.from_db_model(claim)

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete("/{claim_id}")
async def delete_claim(
    claim_id: str,
    session: Session = Depends(get_session)
):
    """Delete an insurance claim."""

    try:
        claim = session.get(InsuranceClaim, claim_id)
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")

        session.delete(claim)
        session.commit()

        return {"message": f"Claim {claim_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/stats/summary")
async def get_claims_summary(session: Session = Depends(get_session)):
    """Get summary statistics for insurance claims."""

    try:
        # Get all claims
        claims = session.exec(select(InsuranceClaim)).fetchall()

        if not claims:
            return {
                "total_claims": 0,
                "total_amount": 0,
                "avg_amount": 0,
                "fraud_count": 0,
                "fraud_percentage": 0,
                "status_distribution": {},
                "claim_type_distribution": {}
            }

        # Calculate statistics
        total_claims = len(claims)
        total_amount = sum(float(claim.claim_amount) for claim in claims)
        avg_amount = total_amount / total_claims if total_claims > 0 else 0
        fraud_count = sum(1 for claim in claims if claim.is_fraud)
        fraud_percentage = (fraud_count / total_claims * 100) if total_claims > 0 else 0

        # Status distribution
        status_dist = {}
        for claim in claims:
            status_dist[claim.claim_status] = status_dist.get(claim.claim_status, 0) + 1

        # Claim type distribution
        type_dist = {}
        for claim in claims:
            type_dist[claim.claim_type] = type_dist.get(claim.claim_type, 0) + 1

        return {
            "total_claims": total_claims,
            "total_amount": round(total_amount, 2),
            "avg_amount": round(avg_amount, 2),
            "fraud_count": fraud_count,
            "fraud_percentage": round(fraud_percentage, 2),
            "status_distribution": status_dist,
            "claim_type_distribution": type_dist
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
