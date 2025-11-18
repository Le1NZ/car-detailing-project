"""Integration tests for bonus-service API endpoints"""
import pytest
from uuid import UUID
from fastapi.testclient import TestClient

from app.repositories.local_bonus_repo import bonus_repository


@pytest.mark.integration
class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check_returns_200(self, test_client: TestClient):
        """Test health endpoint returns 200 OK"""
        # Act
        response = test_client.get("/health")

        # Assert
        assert response.status_code == 200

    def test_health_check_response_format(self, test_client: TestClient):
        """Test health endpoint returns correct format"""
        # Act
        response = test_client.get("/health")
        data = response.json()

        # Assert
        assert "status" in data
        assert "service" in data
        assert data["status"] == "healthy"
        assert data["service"] == "bonus-service"


@pytest.mark.integration
class TestRootEndpoint:
    """Test root endpoint"""

    def test_root_returns_200(self, test_client: TestClient):
        """Test root endpoint returns 200 OK"""
        # Act
        response = test_client.get("/")

        # Assert
        assert response.status_code == 200

    def test_root_response_format(self, test_client: TestClient):
        """Test root endpoint returns correct format"""
        # Act
        response = test_client.get("/")
        data = response.json()

        # Assert
        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert data["service"] == "bonus-service"
        assert data["status"] == "running"


@pytest.mark.integration
class TestApplyPromocodeEndpoint:
    """Test POST /api/bonuses/promocodes/apply endpoint"""

    def test_apply_valid_promocode_summer24(
        self, test_client: TestClient, test_order_id: UUID
    ):
        """Test applying valid SUMMER24 promocode"""
        # Arrange
        payload = {
            "order_id": str(test_order_id),
            "promocode": "SUMMER24"
        }

        # Act
        response = test_client.post("/api/bonuses/promocodes/apply", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == str(test_order_id)
        assert data["promocode"] == "SUMMER24"
        assert data["status"] == "applied"
        assert data["discount_amount"] == 500.0

    def test_apply_valid_promocode_welcome10(
        self, test_client: TestClient, test_order_id: UUID
    ):
        """Test applying valid WELCOME10 promocode"""
        # Arrange
        payload = {
            "order_id": str(test_order_id),
            "promocode": "WELCOME10"
        }

        # Act
        response = test_client.post("/api/bonuses/promocodes/apply", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["promocode"] == "WELCOME10"
        assert data["discount_amount"] == 1000.0

    def test_apply_invalid_promocode_returns_404(
        self, test_client: TestClient, test_order_id: UUID
    ):
        """Test applying invalid promocode returns 404"""
        # Arrange
        payload = {
            "order_id": str(test_order_id),
            "promocode": "INVALID"
        }

        # Act
        response = test_client.post("/api/bonuses/promocodes/apply", json=payload)

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "invalid" in data["detail"].lower()

    def test_apply_promocode_missing_order_id_returns_422(
        self, test_client: TestClient
    ):
        """Test applying promocode without order_id returns 422"""
        # Arrange
        payload = {
            "promocode": "SUMMER24"
        }

        # Act
        response = test_client.post("/api/bonuses/promocodes/apply", json=payload)

        # Assert
        assert response.status_code == 422

    def test_apply_promocode_missing_promocode_returns_422(
        self, test_client: TestClient, test_order_id: UUID
    ):
        """Test applying promocode without promocode field returns 422"""
        # Arrange
        payload = {
            "order_id": str(test_order_id)
        }

        # Act
        response = test_client.post("/api/bonuses/promocodes/apply", json=payload)

        # Assert
        assert response.status_code == 422

    def test_apply_promocode_invalid_uuid_returns_422(self, test_client: TestClient):
        """Test applying promocode with invalid UUID returns 422"""
        # Arrange
        payload = {
            "order_id": "not-a-uuid",
            "promocode": "SUMMER24"
        }

        # Act
        response = test_client.post("/api/bonuses/promocodes/apply", json=payload)

        # Assert
        assert response.status_code == 422

    def test_apply_promocode_empty_string_returns_422(
        self, test_client: TestClient, test_order_id: UUID
    ):
        """Test applying empty promocode returns 422"""
        # Arrange
        payload = {
            "order_id": str(test_order_id),
            "promocode": ""
        }

        # Act
        response = test_client.post("/api/bonuses/promocodes/apply", json=payload)

        # Assert
        assert response.status_code == 422

    def test_apply_promocode_case_sensitive(
        self, test_client: TestClient, test_order_id: UUID
    ):
        """Test promocode application is case-sensitive"""
        # Arrange
        payload = {
            "order_id": str(test_order_id),
            "promocode": "summer24"
        }

        # Act
        response = test_client.post("/api/bonuses/promocodes/apply", json=payload)

        # Assert
        assert response.status_code == 404

    def test_apply_promocode_multiple_times_same_order(
        self, test_client: TestClient, test_order_id: UUID
    ):
        """Test applying promocode multiple times to same order"""
        # Arrange
        payload = {
            "order_id": str(test_order_id),
            "promocode": "SUMMER24"
        }

        # Act - apply twice
        response1 = test_client.post("/api/bonuses/promocodes/apply", json=payload)
        response2 = test_client.post("/api/bonuses/promocodes/apply", json=payload)

        # Assert - both should succeed (no idempotency check in current implementation)
        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_apply_different_promocodes_same_order(
        self, test_client: TestClient, test_order_id: UUID
    ):
        """Test applying different promocodes to same order"""
        # Arrange
        payload1 = {"order_id": str(test_order_id), "promocode": "SUMMER24"}
        payload2 = {"order_id": str(test_order_id), "promocode": "WELCOME10"}

        # Act
        response1 = test_client.post("/api/bonuses/promocodes/apply", json=payload1)
        response2 = test_client.post("/api/bonuses/promocodes/apply", json=payload2)

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json()["discount_amount"] == 500.0
        assert response2.json()["discount_amount"] == 1000.0


@pytest.mark.integration
class TestSpendBonusesEndpoint:
    """Test POST /api/bonuses/spend endpoint"""

    def test_spend_bonuses_sufficient_balance_success(
        self, test_client: TestClient, test_order_id: UUID, test_user_id: UUID
    ):
        """Test spending bonuses when user has sufficient balance"""
        # Arrange - add bonuses to user first
        bonus_repository.user_balances[test_user_id] = 1000.0

        payload = {
            "order_id": str(test_order_id),
            "amount": 300
        }

        # Act
        response = test_client.post("/api/bonuses/spend", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == str(test_order_id)
        assert data["bonuses_spent"] == 300
        assert data["new_balance"] == 700.0

        # Cleanup
        bonus_repository.user_balances.clear()

    def test_spend_all_bonuses(
        self, test_client: TestClient, test_order_id: UUID, test_user_id: UUID
    ):
        """Test spending all available bonuses"""
        # Arrange
        bonus_repository.user_balances[test_user_id] = 500.0

        payload = {
            "order_id": str(test_order_id),
            "amount": 500
        }

        # Act
        response = test_client.post("/api/bonuses/spend", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["bonuses_spent"] == 500
        assert data["new_balance"] == 0.0

        # Cleanup
        bonus_repository.user_balances.clear()

    def test_spend_bonuses_insufficient_balance_returns_400(
        self, test_client: TestClient, test_order_id: UUID, test_user_id: UUID
    ):
        """Test spending more bonuses than available returns 400"""
        # Arrange
        bonus_repository.user_balances[test_user_id] = 100.0

        payload = {
            "order_id": str(test_order_id),
            "amount": 200
        }

        # Act
        response = test_client.post("/api/bonuses/spend", json=payload)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "insufficient" in data["detail"].lower()

        # Cleanup
        bonus_repository.user_balances.clear()

    def test_spend_bonuses_no_balance_returns_400(
        self, test_client: TestClient, test_order_id: UUID
    ):
        """Test spending bonuses with no balance returns 400"""
        # Arrange
        payload = {
            "order_id": str(test_order_id),
            "amount": 100
        }

        # Act
        response = test_client.post("/api/bonuses/spend", json=payload)

        # Assert
        assert response.status_code == 400

    def test_spend_bonuses_zero_amount_returns_422(
        self, test_client: TestClient, test_order_id: UUID
    ):
        """Test spending zero bonuses returns 422"""
        # Arrange
        payload = {
            "order_id": str(test_order_id),
            "amount": 0
        }

        # Act
        response = test_client.post("/api/bonuses/spend", json=payload)

        # Assert
        assert response.status_code == 422

    def test_spend_bonuses_negative_amount_returns_422(
        self, test_client: TestClient, test_order_id: UUID
    ):
        """Test spending negative bonuses returns 422"""
        # Arrange
        payload = {
            "order_id": str(test_order_id),
            "amount": -100
        }

        # Act
        response = test_client.post("/api/bonuses/spend", json=payload)

        # Assert
        assert response.status_code == 422

    def test_spend_bonuses_missing_order_id_returns_422(self, test_client: TestClient):
        """Test spending bonuses without order_id returns 422"""
        # Arrange
        payload = {
            "amount": 100
        }

        # Act
        response = test_client.post("/api/bonuses/spend", json=payload)

        # Assert
        assert response.status_code == 422

    def test_spend_bonuses_missing_amount_returns_422(
        self, test_client: TestClient, test_order_id: UUID
    ):
        """Test spending bonuses without amount returns 422"""
        # Arrange
        payload = {
            "order_id": str(test_order_id)
        }

        # Act
        response = test_client.post("/api/bonuses/spend", json=payload)

        # Assert
        assert response.status_code == 422

    def test_spend_bonuses_invalid_uuid_returns_422(self, test_client: TestClient):
        """Test spending bonuses with invalid UUID returns 422"""
        # Arrange
        payload = {
            "order_id": "not-a-uuid",
            "amount": 100
        }

        # Act
        response = test_client.post("/api/bonuses/spend", json=payload)

        # Assert
        assert response.status_code == 422

    def test_spend_bonuses_large_amount(
        self, test_client: TestClient, test_order_id: UUID, test_user_id: UUID
    ):
        """Test spending large amount of bonuses"""
        # Arrange
        bonus_repository.user_balances[test_user_id] = 1000000.0

        payload = {
            "order_id": str(test_order_id),
            "amount": 500000
        }

        # Act
        response = test_client.post("/api/bonuses/spend", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["bonuses_spent"] == 500000
        assert data["new_balance"] == 500000.0

        # Cleanup
        bonus_repository.user_balances.clear()


@pytest.mark.integration
class TestEndpointIntegration:
    """Test integration scenarios across endpoints"""

    def test_complete_workflow_promocode_and_spend(
        self, test_client: TestClient, test_order_id: UUID, test_user_id: UUID
    ):
        """Test complete workflow: apply promocode, accrue bonuses, spend bonuses"""
        # Step 1: Apply promocode
        promocode_payload = {
            "order_id": str(test_order_id),
            "promocode": "SUMMER24"
        }
        response1 = test_client.post("/api/bonuses/promocodes/apply", json=promocode_payload)
        assert response1.status_code == 200

        # Step 2: Manually add bonuses (simulating payment processing)
        bonus_repository.user_balances[test_user_id] = 500.0

        # Step 3: Spend bonuses
        spend_payload = {
            "order_id": str(test_order_id),
            "amount": 200
        }
        response2 = test_client.post("/api/bonuses/spend", json=spend_payload)
        assert response2.status_code == 200
        assert response2.json()["new_balance"] == 300.0

        # Cleanup
        bonus_repository.user_balances.clear()

    def test_health_check_always_available(self, test_client: TestClient):
        """Test health check is always available"""
        # Act - multiple health checks
        responses = [test_client.get("/health") for _ in range(5)]

        # Assert
        for response in responses:
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

    def test_apply_both_promocodes_sequentially(
        self, test_client: TestClient, test_order_id: UUID, different_user_id: UUID
    ):
        """Test applying both promocodes to different orders"""
        # Arrange
        order_id_2 = different_user_id  # Reuse as second order ID

        payload1 = {"order_id": str(test_order_id), "promocode": "SUMMER24"}
        payload2 = {"order_id": str(order_id_2), "promocode": "WELCOME10"}

        # Act
        response1 = test_client.post("/api/bonuses/promocodes/apply", json=payload1)
        response2 = test_client.post("/api/bonuses/promocodes/apply", json=payload2)

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json()["discount_amount"] == 500.0
        assert response2.json()["discount_amount"] == 1000.0

    def test_multiple_users_spending_bonuses(
        self,
        test_client: TestClient,
        test_order_id: UUID,
        test_user_id: UUID,
        different_user_id: UUID
    ):
        """Test multiple users spending bonuses independently"""
        # Arrange - add bonuses to both users
        bonus_repository.user_balances[test_user_id] = 1000.0
        bonus_repository.user_balances[different_user_id] = 2000.0

        order_id_2 = different_user_id  # Reuse as second order ID

        # Act - Note: current implementation uses mock user_id, so both will affect same user
        # This test demonstrates the expected behavior once proper auth is implemented
        payload1 = {"order_id": str(test_order_id), "amount": 500}
        response1 = test_client.post("/api/bonuses/spend", json=payload1)

        # Assert - first spend succeeds
        assert response1.status_code == 200

        # Cleanup
        bonus_repository.user_balances.clear()

    def test_error_response_format(self, test_client: TestClient, test_order_id: UUID):
        """Test error responses follow FastAPI standard format"""
        # Arrange - invalid promocode
        payload = {
            "order_id": str(test_order_id),
            "promocode": "INVALID"
        }

        # Act
        response = test_client.post("/api/bonuses/promocodes/apply", json=payload)

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)


@pytest.mark.integration
class TestCORSHeaders:
    """Test CORS configuration (if applicable in test client)"""

    def test_options_request_handled(self, test_client: TestClient):
        """Test OPTIONS request for CORS preflight"""
        # Act
        response = test_client.options("/api/bonuses/promocodes/apply")

        # Assert - TestClient may not fully simulate CORS, but endpoint should exist
        # Status might be 405 (Method Not Allowed) or 200 depending on CORS middleware
        assert response.status_code in [200, 405]


@pytest.mark.integration
class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_concurrent_promocode_applications(
        self, test_client: TestClient, test_order_id: UUID, different_user_id: UUID
    ):
        """Test applying promocodes concurrently (simulated)"""
        # Arrange
        order_id_2 = different_user_id

        # Act - Sequential calls (simulating concurrent requests)
        responses = []
        for i in range(10):
            order_id = test_order_id if i % 2 == 0 else order_id_2
            promocode = "SUMMER24" if i % 3 == 0 else "WELCOME10"
            payload = {"order_id": str(order_id), "promocode": promocode}
            responses.append(test_client.post("/api/bonuses/promocodes/apply", json=payload))

        # Assert - all should succeed
        for response in responses:
            assert response.status_code == 200

    def test_spending_fractional_bonuses_as_int(
        self, test_client: TestClient, test_order_id: UUID, test_user_id: UUID
    ):
        """Test spending when balance is fractional but amount is integer"""
        # Arrange
        bonus_repository.user_balances[test_user_id] = 123.45

        payload = {
            "order_id": str(test_order_id),
            "amount": 100
        }

        # Act
        response = test_client.post("/api/bonuses/spend", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["bonuses_spent"] == 100
        assert data["new_balance"] == pytest.approx(23.45, rel=1e-9)

        # Cleanup
        bonus_repository.user_balances.clear()
