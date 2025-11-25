"""
Component tests for Order Service

Component tests verify the interaction between multiple internal components:
- API endpoints
- Service layer
- Repository layer

External dependencies (CarClient) are mocked.
"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from uuid import UUID
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.repositories.local_order_repo import LocalOrderRepository


@pytest.fixture
async def test_client():
    """
    Fixture providing test HTTP client for API endpoint testing

    Uses a fresh repository instance to ensure test isolation
    """
    # Create fresh repository for each test
    from app.services.order_service import order_service
    order_service.repository = LocalOrderRepository()

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_jwt_token():
    """Fixture providing a mock JWT token for authentication"""
    return "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjNlNDU2Ny1lODliLTEyZDMtYTQ1Ni00MjY2MTQxNzQwMDAiLCJleHAiOjk5OTk5OTk5OTl9.abc123"


@pytest.fixture
def valid_auth_headers(mock_jwt_token):
    """Fixture providing valid authorization headers"""
    return {"Authorization": mock_jwt_token}


# Component Test 1: Create order with car verification flow
@pytest.mark.asyncio
@patch("app.services.order_service.order_service.car_client.verify_car_exists")
@patch("app.auth.jwt.decode")
async def test_create_order_with_car_verification_flow(
    mock_jwt_decode,
    mock_verify_car,
    test_client,
    valid_auth_headers
):
    """
    Component test: Create order with car verification

    Tests the full flow:
    1. API endpoint receives POST /api/orders
    2. Service layer calls CarClient to verify car exists
    3. Service layer creates order in Repository with status "created"
    4. API returns order with generated order_id

    Components tested: API endpoint + OrderService + Repository (WITHOUT mocks)
    External dependency mocked: CarClient.verify_car_exists()
    """
    # Arrange: Mock external car service to return True
    mock_verify_car.return_value = True

    # Mock JWT authentication
    mock_jwt_decode.return_value = {
        "sub": "123e4567-e89b-12d3-a456-426614174000"
    }

    order_payload = {
        "car_id": "550e8400-e29b-41d4-a716-446655440000",
        "desired_time": "2025-11-20T10:00:00",
        "description": "Engine oil change and filter replacement"
    }

    # Act: Create order through API
    response = await test_client.post(
        "/api/orders",
        json=order_payload,
        headers=valid_auth_headers
    )

    # Assert: Order created successfully
    assert response.status_code == status.HTTP_201_CREATED

    response_data = response.json()
    assert "order_id" in response_data
    assert response_data["car_id"] == order_payload["car_id"]
    assert response_data["status"] == "created"
    assert response_data["description"] == order_payload["description"]
    assert "created_at" in response_data

    # Verify CarClient was called to verify car existence
    mock_verify_car.assert_called_once_with(order_payload["car_id"])

    # Verify order was saved in repository (can retrieve it)
    order_id = UUID(response_data["order_id"])
    from app.services.order_service import order_service
    saved_order = await order_service.repository.get_order_by_id(order_id)
    assert saved_order is not None
    assert saved_order.status == "created"


# Component Test 2: Order status transition flow
@pytest.mark.asyncio
@patch("app.services.order_service.order_service.car_client.verify_car_exists")
@patch("app.auth.jwt.decode")
async def test_order_status_transition_flow(
    mock_jwt_decode,
    mock_verify_car,
    test_client,
    valid_auth_headers
):
    """
    Component test: Order status transition

    Tests the full flow:
    1. Create order through API (status: "created")
    2. Service saves order in Repository
    3. PATCH /api/orders/{order_id}/status to "in_progress"
    4. Service validates transition and updates Repository
    5. GET order shows updated status

    Components tested: API endpoint + OrderService + Repository
    External dependency mocked: CarClient.verify_car_exists()
    """
    # Arrange: Mock external dependencies
    mock_verify_car.return_value = True
    mock_jwt_decode.return_value = {
        "sub": "123e4567-e89b-12d3-a456-426614174000"
    }

    # Act: Create order
    order_payload = {
        "car_id": "550e8400-e29b-41d4-a716-446655440000",
        "desired_time": "2025-11-20T10:00:00",
        "description": "Brake pad replacement"
    }

    create_response = await test_client.post(
        "/api/orders",
        json=order_payload,
        headers=valid_auth_headers
    )
    assert create_response.status_code == status.HTTP_201_CREATED

    order_id = create_response.json()["order_id"]
    assert create_response.json()["status"] == "created"

    # Act: Update status to "in_progress"
    status_payload = {"status": "in_progress"}

    update_response = await test_client.patch(
        f"/api/orders/{order_id}/status",
        json=status_payload,
        headers=valid_auth_headers
    )

    # Assert: Status updated successfully
    assert update_response.status_code == status.HTTP_200_OK

    updated_order = update_response.json()
    assert updated_order["order_id"] == order_id
    assert updated_order["status"] == "in_progress"

    # Verify status was persisted in repository
    from app.services.order_service import order_service
    saved_order = await order_service.repository.get_order_by_id(UUID(order_id))
    assert saved_order.status == "in_progress"


# Component Test 3: Invalid status transition validation
@pytest.mark.asyncio
@patch("app.services.order_service.order_service.car_client.verify_car_exists")
@patch("app.auth.jwt.decode")
async def test_invalid_status_transition_validation(
    mock_jwt_decode,
    mock_verify_car,
    test_client,
    valid_auth_headers
):
    """
    Component test: Invalid status transition validation

    Tests the full flow:
    1. Create order through API (status: "created")
    2. Attempt to PATCH status to "car_issued" (skipping intermediate states)
    3. Service validates STATE_TRANSITIONS and rejects
    4. Repository is NOT modified
    5. API returns 400 Bad Request

    Components tested: API endpoint + OrderService + Repository
    External dependency mocked: CarClient.verify_car_exists()
    """
    # Arrange: Mock external dependencies
    mock_verify_car.return_value = True
    mock_jwt_decode.return_value = {
        "sub": "123e4567-e89b-12d3-a456-426614174000"
    }

    # Act: Create order with status "created"
    order_payload = {
        "car_id": "550e8400-e29b-41d4-a716-446655440000",
        "desired_time": "2025-11-20T10:00:00",
        "description": "Transmission repair"
    }

    create_response = await test_client.post(
        "/api/orders",
        json=order_payload,
        headers=valid_auth_headers
    )
    assert create_response.status_code == status.HTTP_201_CREATED

    order_id = create_response.json()["order_id"]
    initial_status = create_response.json()["status"]
    assert initial_status == "created"

    # Act: Attempt invalid status transition (created -> car_issued, skipping intermediate states)
    invalid_status_payload = {"status": "car_issued"}

    update_response = await test_client.patch(
        f"/api/orders/{order_id}/status",
        json=invalid_status_payload,
        headers=valid_auth_headers
    )

    # Assert: Request rejected with 400 Bad Request
    assert update_response.status_code == status.HTTP_400_BAD_REQUEST

    error_data = update_response.json()
    assert "detail" in error_data
    assert "invalid" in error_data["detail"].lower()
    assert "transition" in error_data["detail"].lower()

    # Verify repository was NOT modified (status remains "created")
    from app.services.order_service import order_service
    saved_order = await order_service.repository.get_order_by_id(UUID(order_id))
    assert saved_order.status == initial_status  # Still "created"


# Component Test 4: Add review to order flow
@pytest.mark.asyncio
@patch("app.services.order_service.order_service.car_client.verify_car_exists")
@patch("app.auth.jwt.decode")
async def test_add_review_to_order_flow(
    mock_jwt_decode,
    mock_verify_car,
    test_client,
    valid_auth_headers
):
    """
    Component test: Add review to order

    Tests the full flow:
    1. Create order through API
    2. POST /api/orders/review adds review
    3. Service saves review in Repository
    4. Review is linked to order in repository

    Components tested: API endpoint + OrderService + Repository
    External dependency mocked: CarClient.verify_car_exists()
    """
    # Arrange: Mock external dependencies
    mock_verify_car.return_value = True
    mock_jwt_decode.return_value = {
        "sub": "123e4567-e89b-12d3-a456-426614174000"
    }

    # Act: Create order first
    order_payload = {
        "car_id": "550e8400-e29b-41d4-a716-446655440000",
        "desired_time": "2025-11-20T10:00:00",
        "description": "Tire rotation and alignment"
    }

    create_response = await test_client.post(
        "/api/orders",
        json=order_payload,
        headers=valid_auth_headers
    )
    assert create_response.status_code == status.HTTP_201_CREATED

    order_id = create_response.json()["order_id"]

    # Act: Add review to order
    review_payload = {
        "rating": 5,
        "comment": "Excellent service, highly recommend!"
    }

    review_response = await test_client.post(
        f"/api/orders/review?order_id={order_id}",
        json=review_payload,
        headers=valid_auth_headers
    )

    # Assert: Review created successfully
    assert review_response.status_code == status.HTTP_201_CREATED

    review_data = review_response.json()
    assert "review_id" in review_data
    assert review_data["order_id"] == order_id
    assert review_data["rating"] == review_payload["rating"]
    assert review_data["comment"] == review_payload["comment"]
    assert review_data["status"] == "published"
    assert "created_at" in review_data

    # Verify review was saved in repository and linked to order
    from app.services.order_service import order_service
    has_review = await order_service.repository.has_review(UUID(order_id))
    assert has_review is True

    saved_review = await order_service.repository.get_review_by_order_id(UUID(order_id))
    assert saved_review is not None
    assert saved_review.rating == review_payload["rating"]
    assert saved_review.comment == review_payload["comment"]


# Component Test 5: Car service failure handling
@pytest.mark.asyncio
@patch("app.services.order_service.order_service.car_client.verify_car_exists")
@patch("app.auth.jwt.decode")
async def test_car_service_failure_handling(
    mock_jwt_decode,
    mock_verify_car,
    test_client,
    valid_auth_headers
):
    """
    Component test: Car service failure handling

    Tests the full flow:
    1. Mock CarClient.verify_car_exists() to return False (car not found)
    2. Attempt to create order through API
    3. Service receives False from CarClient
    4. Service does NOT save order in Repository
    5. API returns 404 Not Found

    Components tested: API endpoint + OrderService + Repository
    External dependency mocked: CarClient.verify_car_exists() -> False
    """
    # Arrange: Mock car service to return False (car not found)
    mock_verify_car.return_value = False

    # Mock JWT authentication
    mock_jwt_decode.return_value = {
        "sub": "123e4567-e89b-12d3-a456-426614174000"
    }

    order_payload = {
        "car_id": "999e9999-e99b-99d9-a999-999999999999",
        "desired_time": "2025-11-20T10:00:00",
        "description": "Full inspection"
    }

    # Act: Attempt to create order for non-existent car
    response = await test_client.post(
        "/api/orders",
        json=order_payload,
        headers=valid_auth_headers
    )

    # Assert: Request rejected with 404 Not Found
    assert response.status_code == status.HTTP_404_NOT_FOUND

    error_data = response.json()
    assert "detail" in error_data
    assert "car" in error_data["detail"].lower()
    assert "not found" in error_data["detail"].lower()

    # Verify CarClient was called
    mock_verify_car.assert_called_once_with(order_payload["car_id"])

    # Verify NO order was created in repository
    from app.services.order_service import order_service
    # Repository should be empty (no orders created)
    assert len(order_service.repository._orders) == 0
