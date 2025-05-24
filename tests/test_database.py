"""
Tests for the insurance claims database functionality.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from sqlmodel import Session, create_engine, SQLModel
from pydantic import ValidationError
from app.models.database import InsuranceClaim, get_engine


# Test database engine (in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL, echo=False)


@pytest.fixture(scope="function")
def test_session():
    """Create a test database session."""
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture
def sample_claim():
    """Create a sample insurance claim for testing."""
    return InsuranceClaim(
        claim_id="TEST001",
        policy_id="POL001",
        customer_age=35,
        customer_gender="M",
        customer_state="CA",
        vehicle_make="Toyota",
        vehicle_model="Sedan",
        vehicle_year=2020,
        claim_date=datetime(2024, 1, 15, 10, 30, 0),
        claim_type="Collision",
        claim_amount=Decimal("5000.00"),
        deductible=1000,
        claim_status="Approved",
        annual_premium=Decimal("1200.00"),
        is_fraud=False
    )


class TestInsuranceClaimModel:
    """Test the InsuranceClaim SQLModel."""

    def test_create_claim(self, test_session, sample_claim):
        """Test creating a new insurance claim."""
        # Add claim to session
        test_session.add(sample_claim)
        test_session.commit()
        test_session.refresh(sample_claim)

        # Verify the claim was created
        assert sample_claim.claim_id == "TEST001"
        assert sample_claim.created_at is not None
        assert sample_claim.updated_at is None

    def test_claim_validation(self):
        """Test claim data validation."""
        # Test invalid age - use model_validate to trigger Pydantic validation
        with pytest.raises(ValidationError):
            InsuranceClaim.model_validate({
                "claim_id": "TEST002",
                "policy_id": "POL002",
                "customer_age": 150,  # Invalid age
                "customer_gender": "M",
                "customer_state": "CA",
                "vehicle_make": "Toyota",
                "vehicle_model": "Sedan",
                "vehicle_year": 2020,
                "claim_date": datetime.now(),
                "claim_type": "Collision",
                "claim_amount": Decimal("5000.00"),
                "deductible": 1000,
                "claim_status": "Approved",
                "annual_premium": Decimal("1200.00"),
                "is_fraud": False
            })

    def test_claim_decimal_fields(self, test_session):
        """Test decimal field handling."""
        claim = InsuranceClaim(
            claim_id="TEST003",
            policy_id="POL003",
            customer_age=30,
            customer_gender="F",
            customer_state="NY",
            vehicle_make="Honda",
            vehicle_model="SUV",
            vehicle_year=2021,
            claim_date=datetime.now(),
            claim_type="Comprehensive",
            claim_amount=Decimal("12345.67"),
            deductible=500,
            claim_status="Pending",
            annual_premium=Decimal("1500.50"),
            is_fraud=True
        )

        test_session.add(claim)
        test_session.commit()
        test_session.refresh(claim)

        # Verify decimal precision is maintained
        assert claim.claim_amount == Decimal("12345.67")
        assert claim.annual_premium == Decimal("1500.50")
        assert claim.is_fraud


class TestClaimsAPI:
    """Test the claims API endpoints."""

    @pytest.fixture
    def override_get_session(self, test_session):
        """Override the get_session dependency for testing."""
        def _get_test_session():
            yield test_session
        return _get_test_session

    def test_create_multiple_claims(self, test_session):
        """Test creating multiple claims."""
        claims = [
            InsuranceClaim(
                claim_id=f"TEST{i:03d}",
                policy_id=f"POL{i:03d}",
                customer_age=25 + i,
                customer_gender="M" if i % 2 == 0 else "F",
                customer_state="CA",
                vehicle_make="Toyota",
                vehicle_model="Sedan",
                vehicle_year=2020,
                claim_date=datetime.now(),
                claim_type="Collision",
                claim_amount=Decimal(f"{1000 + i * 100}.00"),
                deductible=1000,
                claim_status="Approved" if i % 2 == 0 else "Denied",
                annual_premium=Decimal("1200.00"),
                is_fraud=i % 5 == 0  # Every 5th claim is fraud
            )
            for i in range(10)
        ]

        test_session.add_all(claims)
        test_session.commit()

        # Verify all claims were created
        from sqlmodel import select
        all_claims = test_session.exec(select(InsuranceClaim)).fetchall()
        assert len(all_claims) == 10

        # Test filtering by status
        approved_claims = test_session.exec(
            select(InsuranceClaim).where(InsuranceClaim.claim_status == "Approved")
        ).fetchall()
        assert len(approved_claims) == 5

        # Test filtering by fraud
        fraud_claims = test_session.exec(
            select(InsuranceClaim).where(InsuranceClaim.is_fraud)
        ).fetchall()
        assert len(fraud_claims) == 2  # Claims at index 0 and 5


def test_database_connection():
    """Test database connection and engine creation."""
    engine = get_engine()
    assert engine is not None

    # Test that we can create tables
    SQLModel.metadata.create_all(engine)


def test_claim_json_serialization(sample_claim):
    """Test that claims can be serialized to JSON."""
    claim_dict = sample_claim.model_dump()

    # Verify key fields are present
    assert claim_dict["claim_id"] == "TEST001"
    assert claim_dict["policy_id"] == "POL001"
    assert isinstance(claim_dict["claim_amount"], Decimal)
    assert isinstance(claim_dict["annual_premium"], Decimal)
    assert not claim_dict["is_fraud"]


def test_claim_config_example():
    """Test that the claim model's example configuration is valid."""
    config_example = InsuranceClaim.Config.json_schema_extra["example"]

    # Verify example has all required fields
    required_fields = [
        "claim_id", "policy_id", "customer_age", "customer_gender",
        "customer_state", "vehicle_make", "vehicle_model", "vehicle_year",
        "claim_date", "claim_type", "claim_amount", "deductible",
        "claim_status", "annual_premium", "is_fraud"
    ]

    for field in required_fields:
        assert field in config_example, f"Missing field in example: {field}"
