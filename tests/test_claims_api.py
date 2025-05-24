"""
Integration tests for the insurance claims API endpoints.
"""

import pytest


@pytest.fixture
def sample_claim_data():
    """Sample claim data for testing."""
    return {
        "claim_id": "TEST001",
        "policy_id": "POL001",
        "customer_age": 35,
        "customer_gender": "M",
        "customer_state": "CA",
        "vehicle_make": "Toyota",
        "vehicle_model": "Sedan",
        "vehicle_year": 2020,
        "claim_date": "2024-01-15T10:30:00.000Z",  # ISO format with timezone
        "claim_type": "Collision",
        "claim_amount": 5000.00,
        "deductible": 1000,
        "claim_status": "Approved",
        "annual_premium": 1200.00,
        "is_fraud": False
    }


class TestClaimsAPIEndpoints:
    """Test the claims API endpoints."""

    def test_health_endpoint(self, test_client):
        """Test that the health endpoint works."""
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_create_claim(self, test_client, sample_claim_data):
        """Test creating a new claim."""
        response = test_client.post("/api/v1/claims/", json=sample_claim_data)
        assert response.status_code == 200

        data = response.json()
        assert data["claim_id"] == "TEST001"
        assert data["policy_id"] == "POL001"
        assert data["customer_age"] == 35
        assert data["claim_amount"] == 5000.00
        assert data["is_fraud"] is False
        assert "created_at" in data

    def test_get_claims_empty(self, test_client):
        """Test getting claims when database is empty."""
        response = test_client.get("/api/v1/claims/")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_claims_with_data(self, test_client, sample_claim_data):
        """Test getting claims after creating one."""
        # Create a claim first
        test_client.post("/api/v1/claims/", json=sample_claim_data)

        # Get claims
        response = test_client.get("/api/v1/claims/")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["claim_id"] == "TEST001"

    def test_get_claim_by_id(self, test_client, sample_claim_data):
        """Test getting a specific claim by ID."""
        # Create a claim first
        test_client.post("/api/v1/claims/", json=sample_claim_data)

        # Get the specific claim
        response = test_client.get("/api/v1/claims/TEST001")
        assert response.status_code == 200

        data = response.json()
        assert data["claim_id"] == "TEST001"
        assert data["customer_age"] == 35

    def test_get_claim_not_found(self, test_client):
        """Test getting a non-existent claim."""
        response = test_client.get("/api/v1/claims/NONEXISTENT")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_claim(self, test_client, sample_claim_data):
        """Test updating an existing claim."""
        # Create a claim first
        test_client.post("/api/v1/claims/", json=sample_claim_data)

        # Update the claim
        updated_data = sample_claim_data.copy()
        updated_data["claim_status"] = "Under Investigation"
        updated_data["claim_amount"] = 6000.00

        response = test_client.put("/api/v1/claims/TEST001", json=updated_data)
        assert response.status_code == 200

        data = response.json()
        assert data["claim_status"] == "Under Investigation"
        assert data["claim_amount"] == 6000.00
        assert "updated_at" in data

    def test_delete_claim(self, test_client, sample_claim_data):
        """Test deleting a claim."""
        # Create a claim first
        test_client.post("/api/v1/claims/", json=sample_claim_data)

        # Delete the claim
        response = test_client.delete("/api/v1/claims/TEST001")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify it's gone
        response = test_client.get("/api/v1/claims/TEST001")
        assert response.status_code == 404

    def test_claims_filtering(self, test_client):
        """Test filtering claims by various parameters."""
        # Create multiple claims
        claims_data = [
            {
                "claim_id": f"TEST{i:03d}",
                "policy_id": f"POL{i:03d}",
                "customer_age": 30 + i,
                "customer_gender": "M" if i % 2 == 0 else "F",
                "customer_state": "CA",
                "vehicle_make": "Toyota",
                "vehicle_model": "Sedan",
                "vehicle_year": 2020,
                "claim_date": "2024-01-15T10:30:00",
                "claim_type": "Collision",
                "claim_amount": 1000.00 + i * 500,
                "deductible": 1000,
                "claim_status": "Approved" if i % 2 == 0 else "Denied",
                "annual_premium": 1200.00,
                "is_fraud": i % 3 == 0
            }
            for i in range(5)
        ]

        for claim_data in claims_data:
            test_client.post("/api/v1/claims/", json=claim_data)

        # Test status filtering
        response = test_client.get("/api/v1/claims/?claim_status=Approved")
        assert response.status_code == 200
        approved_claims = response.json()
        assert len(approved_claims) == 3  # Claims 0, 2, 4

        # Test fraud filtering
        response = test_client.get("/api/v1/claims/?is_fraud=true")
        assert response.status_code == 200
        fraud_claims = response.json()
        assert len(fraud_claims) == 2  # Claims 0, 3

        # Test amount filtering
        response = test_client.get("/api/v1/claims/?min_amount=2000&max_amount=3000")
        assert response.status_code == 200
        filtered_claims = response.json()
        assert len(filtered_claims) == 3  # Claims with amounts 2000, 2500, and 3000

    def test_claims_pagination(self, test_client):
        """Test pagination of claims."""
        # Create multiple claims
        for i in range(10):
            claim_data = {
                "claim_id": f"TEST{i:03d}",
                "policy_id": f"POL{i:03d}",
                "customer_age": 30,
                "customer_gender": "M",
                "customer_state": "CA",
                "vehicle_make": "Toyota",
                "vehicle_model": "Sedan",
                "vehicle_year": 2020,
                "claim_date": "2024-01-15T10:30:00",
                "claim_type": "Collision",
                "claim_amount": 1000.00,
                "deductible": 1000,
                "claim_status": "Approved",
                "annual_premium": 1200.00,
                "is_fraud": False
            }
            test_client.post("/api/v1/claims/", json=claim_data)

        # Test pagination
        response = test_client.get("/api/v1/claims/?skip=0&limit=5")
        assert response.status_code == 200
        first_page = response.json()
        assert len(first_page) == 5

        response = test_client.get("/api/v1/claims/?skip=5&limit=5")
        assert response.status_code == 200
        second_page = response.json()
        assert len(second_page) == 5

        # Ensure no overlap
        first_ids = {claim["claim_id"] for claim in first_page}
        second_ids = {claim["claim_id"] for claim in second_page}
        assert first_ids.isdisjoint(second_ids)

    def test_claims_summary_stats(self, test_client):
        """Test the claims summary statistics endpoint."""
        # Test with empty database
        response = test_client.get("/api/v1/claims/stats/summary")
        assert response.status_code == 200
        stats = response.json()
        assert stats["total_claims"] == 0

        # Create some test claims
        claims_data = [
            {
                "claim_id": "TEST001",
                "policy_id": "POL001",
                "customer_age": 30,
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
            },
            {
                "claim_id": "TEST002",
                "policy_id": "POL002",
                "customer_age": 25,
                "customer_gender": "F",
                "customer_state": "NY",
                "vehicle_make": "Honda",
                "vehicle_model": "SUV",
                "vehicle_year": 2021,
                "claim_date": "2024-01-20T14:00:00",
                "claim_type": "Comprehensive",
                "claim_amount": 3000.00,
                "deductible": 500,
                "claim_status": "Denied",
                "annual_premium": 1500.00,
                "is_fraud": True
            }
        ]

        for claim_data in claims_data:
            test_client.post("/api/v1/claims/", json=claim_data)

        # Test stats with data
        response = test_client.get("/api/v1/claims/stats/summary")
        assert response.status_code == 200
        stats = response.json()

        assert stats["total_claims"] == 2
        assert stats["total_amount"] == 8000.00
        assert stats["avg_amount"] == 4000.00
        assert stats["fraud_count"] == 1
        assert stats["fraud_percentage"] == 50.0
        assert stats["status_distribution"]["Approved"] == 1
        assert stats["status_distribution"]["Denied"] == 1
        assert stats["claim_type_distribution"]["Collision"] == 1
        assert stats["claim_type_distribution"]["Comprehensive"] == 1

    def test_duplicate_claim_creation(self, test_client, sample_claim_data):
        """Test that creating duplicate claims fails."""
        # Create first claim
        response = test_client.post("/api/v1/claims/", json=sample_claim_data)
        assert response.status_code == 200

        # Try to create duplicate
        response = test_client.post("/api/v1/claims/", json=sample_claim_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_invalid_claim_data(self, test_client):
        """Test creating claims with invalid data."""
        invalid_claim = {
            "claim_id": "TEST001",
            "policy_id": "POL001",
            "customer_age": -5,  # Invalid age
            "customer_gender": "X",  # Invalid gender
            "customer_state": "CA",
            "vehicle_make": "Toyota",
            "vehicle_model": "Sedan",
            "vehicle_year": 2020,
            "claim_date": "2024-01-15T10:30:00",
            "claim_type": "Collision",
            "claim_amount": -1000.00,  # Invalid amount
            "deductible": 1000,
            "claim_status": "Approved",
            "annual_premium": 1200.00,
            "is_fraud": False
        }

        response = test_client.post("/api/v1/claims/", json=invalid_claim)
        assert response.status_code == 422  # Validation error
