"""
Component tests for bonus-service

Component testing verifies that multiple INTERNAL components of the service work together correctly.
In bonus-service, components include: API Endpoint + BonusService + LocalBonusRepository.

Component tests:
- Test REAL interactions between API endpoints, service layer, and repository
- Mock ONLY external dependencies (RabbitMQ)
- DO NOT mock internal service or repository layers

Key difference from integration tests:
- Integration tests may mock service layer
- Component tests use REAL service + REAL repository working together
"""

import pytest
import json
from uuid import UUID, uuid4
from unittest.mock import Mock, AsyncMock
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from app.repositories.local_bonus_repo import LocalBonusRepository
from app.services.bonus_service import BonusService
from app.services.rabbitmq_consumer import RabbitMQConsumer
from app.endpoints import bonuses
from app.models.bonus import HealthResponse
from app.config import settings


# ==================== Component Test Fixtures ====================

@pytest.fixture
def component_repository() -> LocalBonusRepository:
    """
    Fresh repository instance for component testing.
    This is the REAL repository, not a mock.
    """
    return LocalBonusRepository()


@pytest.fixture
def component_service(component_repository: LocalBonusRepository) -> BonusService:
    """
    Real BonusService instance using the real repository.
    Tests full service -> repository interaction.
    """
    return BonusService(repository=component_repository)


@pytest.fixture
async def component_test_client(component_repository: LocalBonusRepository):
    """
    Async test client with REAL service and repository for component testing.
    Mocks only external dependencies (JWT auth).
    """
    from app.auth import get_current_user_id

    # Create test app without lifespan (to avoid RabbitMQ connection)
    test_app = FastAPI(title="Test Bonus Service - Component")

    # Mock JWT auth to return test user
    test_user_id = UUID("c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d")

    def mock_get_current_user_id() -> UUID:
        return test_user_id

    test_app.dependency_overrides[get_current_user_id] = mock_get_current_user_id

    # Override the bonus_service with our component service (using real repository)
    component_service = BonusService(repository=component_repository)
    original_service = bonuses.bonus_service
    bonuses.bonus_service = component_service

    test_app.include_router(bonuses.router)

    @test_app.get("/health", response_model=HealthResponse)
    async def health_check():
        return HealthResponse(status="healthy", service=settings.SERVICE_NAME)

    # Use ASGITransport for httpx
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        yield client

    # Restore original service
    bonuses.bonus_service = original_service


@pytest.fixture
def test_user_id() -> UUID:
    """Standard test user ID"""
    return UUID("c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d")


@pytest.fixture
def test_order_id() -> UUID:
    """Standard test order ID"""
    return UUID("123e4567-e89b-12d3-a456-426614174000")


# ==================== Component Test 1: Apply Promocode Flow ====================

@pytest.mark.asyncio
async def test_apply_promocode_flow(
    component_test_client: AsyncClient,
    test_order_id: UUID
):
    """
    Component Test 1: Full flow of applying promocode

    Flow tested:
    1. API endpoint receives request with promocode
    2. BonusService validates promocode
    3. Repository searches for promocode in PROMOCODES list
    4. Repository returns Promocode object with discount
    5. Service returns discount amount
    6. API endpoint returns 200 with correct discount

    Components involved: API Endpoint + BonusService + LocalBonusRepository
    No mocks used (all components are real)
    """
    # Arrange
    payload = {
        "order_id": str(test_order_id),
        "promocode": "SUMMER24"  # This promocode exists in repository with 500 RUB discount
    }

    # Act
    response = await component_test_client.post(
        "/api/bonuses/promocodes/apply",
        json=payload
    )

    # Assert
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()
    assert data["order_id"] == str(test_order_id)
    assert data["promocode"] == "SUMMER24"
    assert data["status"] == "applied"
    assert data["discount_amount"] == 500.0, "SUMMER24 should give 500 RUB discount from repository"

    # Test alternative promocode
    payload2 = {
        "order_id": str(test_order_id),
        "promocode": "WELCOME10"  # This promocode exists with 1000 RUB discount
    }

    response2 = await component_test_client.post(
        "/api/bonuses/promocodes/apply",
        json=payload2
    )

    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["discount_amount"] == 1000.0, "WELCOME10 should give 1000 RUB discount"

    # Test invalid promocode - should return 404
    payload3 = {
        "order_id": str(test_order_id),
        "promocode": "INVALID123"
    }

    response3 = await component_test_client.post(
        "/api/bonuses/promocodes/apply",
        json=payload3
    )

    assert response3.status_code == 404, "Invalid promocode should return 404"
    assert "invalid or inactive" in response3.json()["detail"].lower()


# ==================== Component Test 2: Spend Bonuses Flow ====================

@pytest.mark.asyncio
async def test_spend_bonuses_flow(
    component_test_client: AsyncClient,
    component_repository: LocalBonusRepository,
    test_user_id: UUID,
    test_order_id: UUID
):
    """
    Component Test 2: Full flow of spending bonuses

    Flow tested:
    1. Populate user balance in repository (simulate prior accrual)
    2. API endpoint receives spend request
    3. BonusService checks balance via repository
    4. Repository validates sufficient balance
    5. Repository updates user balance (subtract amount)
    6. Service returns new balance
    7. API endpoint returns 200 with bonuses_spent and new_balance

    Components involved: API Endpoint + BonusService + LocalBonusRepository
    Repository state is modified and persisted
    """
    # Arrange: Add initial balance to user
    initial_balance = 1000.0
    await component_repository.add_bonuses(test_user_id, initial_balance)

    # Verify initial balance
    balance = await component_repository.get_user_balance(test_user_id)
    assert balance == initial_balance

    # Act: Spend bonuses via API
    spend_amount = 300
    payload = {
        "order_id": str(test_order_id),
        "amount": spend_amount
    }

    response = await component_test_client.post(
        "/api/bonuses/spend",
        json=payload
    )

    # Assert
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()
    assert data["order_id"] == str(test_order_id)
    assert data["bonuses_spent"] == spend_amount
    assert data["new_balance"] == 700.0, "Balance should be 1000 - 300 = 700"

    # Verify repository state changed
    final_balance = await component_repository.get_user_balance(test_user_id)
    assert final_balance == 700.0, "Repository should reflect the updated balance"

    # Test spending more bonuses
    payload2 = {
        "order_id": str(uuid4()),
        "amount": 200
    }

    response2 = await component_test_client.post(
        "/api/bonuses/spend",
        json=payload2
    )

    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["new_balance"] == 500.0, "Balance should be 700 - 200 = 500"


# ==================== Component Test 3: Accrue Bonuses Through Service Layer ====================

@pytest.mark.asyncio
async def test_accrue_bonuses_through_service_layer(
    component_test_client: AsyncClient,
    component_service: BonusService,
    component_repository: LocalBonusRepository,
    test_user_id: UUID
):
    """
    Component Test 3: Accrue bonuses through service and verify via API

    Flow tested:
    1. Directly call BonusService.accrue_bonuses() (simulates RabbitMQ consumer call)
    2. Service calculates bonus amount (payment_amount * rate)
    3. Repository stores bonuses in user_balances dict
    4. Verify balance persisted by calling repository directly
    5. Verify balance can be queried through API (future enhancement)

    Components involved: BonusService + LocalBonusRepository + API verification
    This simulates what happens when RabbitMQ consumer calls the service
    """
    # Arrange
    payment_amount = 10000.0  # 10,000 RUB payment
    rate = 0.01  # 1% bonus rate
    expected_bonuses = 100.0  # 10,000 * 0.01 = 100 bonuses
    order_id = uuid4()

    # Act: Accrue bonuses via service (simulates RabbitMQ consumer behavior)
    accrued_amount = await component_service.accrue_bonuses(
        user_id=test_user_id,
        order_id=order_id,
        payment_amount=payment_amount,
        rate=rate
    )

    # Assert: Verify service returned correct amount
    assert accrued_amount == expected_bonuses, f"Expected {expected_bonuses}, got {accrued_amount}"

    # Verify repository stored the bonuses
    balance = await component_repository.get_user_balance(test_user_id)
    assert balance == expected_bonuses, f"Repository should have {expected_bonuses} bonuses"

    # Accrue more bonuses for the same user
    accrued_amount2 = await component_service.accrue_bonuses(
        user_id=test_user_id,
        order_id=uuid4(),
        payment_amount=5000.0,
        rate=0.01
    )

    assert accrued_amount2 == 50.0

    # Verify cumulative balance
    balance_after_second = await component_repository.get_user_balance(test_user_id)
    assert balance_after_second == 150.0, "Balance should accumulate: 100 + 50 = 150"

    # Now verify we can spend these accrued bonuses via API
    spend_payload = {
        "order_id": str(uuid4()),
        "amount": 75
    }

    spend_response = await component_test_client.post(
        "/api/bonuses/spend",
        json=spend_payload
    )

    assert spend_response.status_code == 200
    spend_data = spend_response.json()
    assert spend_data["new_balance"] == 75.0, "Should be able to spend accrued bonuses: 150 - 75 = 75"


# ==================== Component Test 4: Insufficient Balance Error Propagation ====================

@pytest.mark.asyncio
async def test_insufficient_balance_error_propagation(
    component_test_client: AsyncClient,
    component_repository: LocalBonusRepository,
    test_user_id: UUID,
    test_order_id: UUID
):
    """
    Component Test 4: Error propagation through all layers

    Flow tested:
    1. API endpoint receives spend request for amount > balance
    2. BonusService calls repository.get_user_balance()
    3. Service detects insufficient balance
    4. Service raises ValueError
    5. API endpoint catches ValueError
    6. API endpoint returns HTTP 400 with error message
    7. Repository state remains unchanged (no balance deduction)

    Components involved: API Endpoint + BonusService + LocalBonusRepository
    Tests error handling across all layers
    """
    # Arrange: User has only 50 bonuses
    await component_repository.add_bonuses(test_user_id, 50.0)

    initial_balance = await component_repository.get_user_balance(test_user_id)
    assert initial_balance == 50.0

    # Act: Try to spend 200 bonuses (more than available)
    payload = {
        "order_id": str(test_order_id),
        "amount": 200
    }

    response = await component_test_client.post(
        "/api/bonuses/spend",
        json=payload
    )

    # Assert: Should return 400 BAD_REQUEST
    assert response.status_code == 400, f"Expected 400 for insufficient balance, got {response.status_code}"

    error_detail = response.json()["detail"]
    assert "insufficient" in error_detail.lower(), "Error message should mention insufficient balance"
    assert "50" in error_detail or "50.0" in error_detail, "Error should show current balance"
    assert "200" in error_detail, "Error should show requested amount"

    # Verify repository state unchanged
    balance_after_error = await component_repository.get_user_balance(test_user_id)
    assert balance_after_error == 50.0, "Balance should remain unchanged after failed spend"

    # Test edge case: spend exactly 0 bonuses (user has 0 balance)
    user2_id = uuid4()
    payload2 = {
        "order_id": str(uuid4()),
        "amount": 1
    }

    # Temporarily override auth to return user2_id
    from app.auth import get_current_user_id

    def mock_user2() -> UUID:
        return user2_id

    # Note: This test uses test_user_id from fixture, so we test with that user trying to spend more
    payload3 = {
        "order_id": str(uuid4()),
        "amount": 51  # One more than balance
    }

    response3 = await component_test_client.post(
        "/api/bonuses/spend",
        json=payload3
    )

    assert response3.status_code == 400, "Should fail when spending 51 with balance of 50"


# ==================== Component Test 5: Complete Bonus Lifecycle ====================

@pytest.mark.asyncio
async def test_complete_bonus_lifecycle(
    component_test_client: AsyncClient,
    component_service: BonusService,
    component_repository: LocalBonusRepository,
    test_user_id: UUID
):
    """
    Component Test 5: Complete user journey through the bonus system

    Scenario:
    1. User makes payment -> bonuses accrued (via service call)
    2. Check balance increased in repository
    3. User makes another payment -> more bonuses accrued
    4. User spends some bonuses via API
    5. Check balance decreased
    6. User spends remaining bonuses via API
    7. Verify final balance is 0

    Flow tested:
    - Accrue bonuses (Service + Repository)
    - Query balance (Repository)
    - Spend bonuses (API + Service + Repository)
    - Multiple operations maintain state consistency

    Components involved: ALL components working together across multiple operations
    """
    # Step 1: Accrue bonuses from first payment
    payment1_amount = 8000.0  # 8,000 RUB
    order1_id = uuid4()

    bonuses1 = await component_service.accrue_bonuses(
        user_id=test_user_id,
        order_id=order1_id,
        payment_amount=payment1_amount,
        rate=0.01
    )

    assert bonuses1 == 80.0, "First payment should accrue 80 bonuses"

    # Step 2: Verify balance in repository
    balance_after_first = await component_repository.get_user_balance(test_user_id)
    assert balance_after_first == 80.0, "Repository should show 80 bonuses"

    # Step 3: Accrue bonuses from second payment
    payment2_amount = 12000.0  # 12,000 RUB
    order2_id = uuid4()

    bonuses2 = await component_service.accrue_bonuses(
        user_id=test_user_id,
        order_id=order2_id,
        payment_amount=payment2_amount,
        rate=0.01
    )

    assert bonuses2 == 120.0, "Second payment should accrue 120 bonuses"

    # Step 4: Verify cumulative balance
    balance_after_second = await component_repository.get_user_balance(test_user_id)
    assert balance_after_second == 200.0, "Total should be 80 + 120 = 200 bonuses"

    # Step 5: Spend some bonuses via API
    spend1_payload = {
        "order_id": str(uuid4()),
        "amount": 70
    }

    spend1_response = await component_test_client.post(
        "/api/bonuses/spend",
        json=spend1_payload
    )

    assert spend1_response.status_code == 200, "Should successfully spend 70 bonuses"
    spend1_data = spend1_response.json()
    assert spend1_data["bonuses_spent"] == 70
    assert spend1_data["new_balance"] == 130.0, "Balance should be 200 - 70 = 130"

    # Step 6: Verify balance after first spend
    balance_after_spend1 = await component_repository.get_user_balance(test_user_id)
    assert balance_after_spend1 == 130.0, "Repository should reflect spent bonuses"

    # Step 7: Spend more bonuses via API
    spend2_payload = {
        "order_id": str(uuid4()),
        "amount": 80
    }

    spend2_response = await component_test_client.post(
        "/api/bonuses/spend",
        json=spend2_payload
    )

    assert spend2_response.status_code == 200
    spend2_data = spend2_response.json()
    assert spend2_data["new_balance"] == 50.0, "Balance should be 130 - 80 = 50"

    # Step 8: Spend remaining bonuses
    spend3_payload = {
        "order_id": str(uuid4()),
        "amount": 50
    }

    spend3_response = await component_test_client.post(
        "/api/bonuses/spend",
        json=spend3_payload
    )

    assert spend3_response.status_code == 200
    spend3_data = spend3_response.json()
    assert spend3_data["new_balance"] == 0.0, "Balance should be 50 - 50 = 0"

    # Step 9: Verify final balance is 0
    final_balance = await component_repository.get_user_balance(test_user_id)
    assert final_balance == 0.0, "User should have 0 bonuses remaining"

    # Step 10: Try to spend when balance is 0 (should fail)
    spend4_payload = {
        "order_id": str(uuid4()),
        "amount": 1
    }

    spend4_response = await component_test_client.post(
        "/api/bonuses/spend",
        json=spend4_payload
    )

    assert spend4_response.status_code == 400, "Should fail when trying to spend with 0 balance"
    assert "insufficient" in spend4_response.json()["detail"].lower()
