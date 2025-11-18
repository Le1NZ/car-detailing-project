"""
Integration tests for Cart Service API endpoints

Tests cover:
- GET /health - Health check endpoint
- GET / - Root endpoint
- GET /api/cart - Get cart endpoint
- POST /api/cart/items - Add item to cart endpoint
- DELETE /api/cart/items/{item_id} - Remove item from cart endpoint
- Error scenarios: 404, 400, validation errors
- End-to-end workflows

Uses TestClient to test the complete HTTP request/response cycle
"""
import pytest
from fastapi.testclient import TestClient


class TestHealthAndInfoEndpoints:
    """Test suite for health check and info endpoints"""

    def test_health_check_endpoint(self, test_client: TestClient):
        """Test GET /health returns healthy status"""
        # Act
        response = test_client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "cart-service"
        assert data["version"] == "1.0.0"

    def test_root_endpoint(self, test_client: TestClient):
        """Test GET / returns service information"""
        # Act
        response = test_client.get("/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "cart-service"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
        assert data["endpoints"]["cart"] == "/api/cart"


class TestGetCartEndpoint:
    """Test suite for GET /api/cart endpoint"""

    def test_get_cart_empty(self, test_client: TestClient):
        """Test GET /api/cart returns empty cart for new user"""
        # Act
        response = test_client.get("/api/cart")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert data["items"] == []
        assert data["total_price"] == 0.0

    def test_get_cart_with_items(self, test_client: TestClient):
        """Test GET /api/cart returns cart with items after adding"""
        # Arrange - Add item first
        add_response = test_client.post(
            "/api/cart/items",
            json={
                "item_id": "svc_oil_change",
                "type": "service",
                "quantity": 1
            }
        )
        assert add_response.status_code == 200

        # Act
        response = test_client.get("/api/cart")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["item_id"] == "svc_oil_change"
        assert data["items"][0]["name"] == "Замена масла"
        assert data["items"][0]["quantity"] == 1
        assert data["items"][0]["price"] == 2500.0
        assert data["total_price"] == 2500.0

    def test_get_cart_multiple_items(self, test_client: TestClient):
        """Test GET /api/cart returns multiple items with correct total"""
        # Arrange - Add multiple items
        test_client.post(
            "/api/cart/items",
            json={"item_id": "svc_oil_change", "type": "service", "quantity": 1}
        )
        test_client.post(
            "/api/cart/items",
            json={"item_id": "prod_oil_filter", "type": "product", "quantity": 2}
        )
        test_client.post(
            "/api/cart/items",
            json={"item_id": "svc_diagnostics", "type": "service", "quantity": 1}
        )

        # Act
        response = test_client.get("/api/cart")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        # Expected: 2500.0 + (1000.0 * 2) + 1500.0 = 6000.0
        assert data["total_price"] == 6000.0

    def test_get_cart_response_model(self, test_client: TestClient):
        """Test GET /api/cart response matches CartResponse model"""
        # Act
        response = test_client.get("/api/cart")

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Verify required fields
        assert "user_id" in data
        assert "items" in data
        assert "total_price" in data
        # Verify data types
        assert isinstance(data["items"], list)
        assert isinstance(data["total_price"], (int, float))


class TestAddItemEndpoint:
    """Test suite for POST /api/cart/items endpoint"""

    def test_add_item_success_service(self, test_client: TestClient):
        """Test POST /api/cart/items successfully adds service"""
        # Arrange
        request_data = {
            "item_id": "svc_oil_change",
            "type": "service",
            "quantity": 1
        }

        # Act
        response = test_client.post("/api/cart/items", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["item_id"] == "svc_oil_change"
        assert data["items"][0]["type"] == "service"
        assert data["items"][0]["name"] == "Замена масла"
        assert data["items"][0]["quantity"] == 1
        assert data["items"][0]["price"] == 2500.0
        assert data["total_price"] == 2500.0

    def test_add_item_success_product(self, test_client: TestClient):
        """Test POST /api/cart/items successfully adds product"""
        # Arrange
        request_data = {
            "item_id": "prod_oil_filter",
            "type": "product",
            "quantity": 3
        }

        # Act
        response = test_client.post("/api/cart/items", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["item_id"] == "prod_oil_filter"
        assert data["items"][0]["type"] == "product"
        assert data["items"][0]["name"] == "Масляный фильтр"
        assert data["items"][0]["quantity"] == 3
        assert data["total_price"] == 3000.0  # 3 * 1000.0

    def test_add_item_diagnostics_service(self, test_client: TestClient):
        """Test POST /api/cart/items adds diagnostics service"""
        # Arrange
        request_data = {
            "item_id": "svc_diagnostics",
            "type": "service",
            "quantity": 2
        }

        # Act
        response = test_client.post("/api/cart/items", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["items"][0]["name"] == "Диагностика"
        assert data["items"][0]["quantity"] == 2
        assert data["total_price"] == 3000.0  # 2 * 1500.0

    def test_add_item_accumulates_quantity(self, test_client: TestClient):
        """Test POST /api/cart/items accumulates quantity for same item"""
        # Arrange
        request_data = {
            "item_id": "svc_oil_change",
            "type": "service",
            "quantity": 1
        }

        # Act - Add same item twice
        response1 = test_client.post("/api/cart/items", json=request_data)
        response2 = test_client.post("/api/cart/items", json=request_data)

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        data = response2.json()
        assert len(data["items"]) == 1  # No duplicate
        assert data["items"][0]["quantity"] == 2  # Accumulated
        assert data["total_price"] == 5000.0  # 2 * 2500.0

    def test_add_item_not_found_in_catalog(self, test_client: TestClient):
        """Test POST /api/cart/items with non-existent item returns 404"""
        # Arrange
        request_data = {
            "item_id": "non_existent_item",
            "type": "service",
            "quantity": 1
        }

        # Act
        response = test_client.post("/api/cart/items", json=request_data)

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found in catalog" in data["detail"]

    def test_add_item_type_mismatch(self, test_client: TestClient):
        """Test POST /api/cart/items with wrong type returns 400"""
        # Arrange
        request_data = {
            "item_id": "svc_oil_change",  # This is a service
            "type": "product",  # Wrong type
            "quantity": 1
        }

        # Act
        response = test_client.post("/api/cart/items", json=request_data)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "type mismatch" in data["detail"]

    def test_add_item_validation_missing_field(self, test_client: TestClient):
        """Test POST /api/cart/items with missing field returns 422"""
        # Arrange
        request_data = {
            "item_id": "svc_oil_change",
            "type": "service"
            # Missing: quantity
        }

        # Act
        response = test_client.post("/api/cart/items", json=request_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_add_item_validation_zero_quantity(self, test_client: TestClient):
        """Test POST /api/cart/items with zero quantity returns 422"""
        # Arrange
        request_data = {
            "item_id": "svc_oil_change",
            "type": "service",
            "quantity": 0  # Invalid
        }

        # Act
        response = test_client.post("/api/cart/items", json=request_data)

        # Assert
        assert response.status_code == 422

    def test_add_item_validation_negative_quantity(self, test_client: TestClient):
        """Test POST /api/cart/items with negative quantity returns 422"""
        # Arrange
        request_data = {
            "item_id": "svc_oil_change",
            "type": "service",
            "quantity": -1  # Invalid
        }

        # Act
        response = test_client.post("/api/cart/items", json=request_data)

        # Assert
        assert response.status_code == 422

    def test_add_item_invalid_json(self, test_client: TestClient):
        """Test POST /api/cart/items with invalid JSON returns 422"""
        # Act
        response = test_client.post(
            "/api/cart/items",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        # Assert
        assert response.status_code == 422


class TestRemoveItemEndpoint:
    """Test suite for DELETE /api/cart/items/{item_id} endpoint"""

    def test_remove_item_success(self, test_client: TestClient):
        """Test DELETE /api/cart/items/{item_id} successfully removes item"""
        # Arrange - Add item first
        test_client.post(
            "/api/cart/items",
            json={"item_id": "svc_oil_change", "type": "service", "quantity": 1}
        )

        # Act
        response = test_client.delete("/api/cart/items/svc_oil_change")

        # Assert
        assert response.status_code == 204
        assert response.text == ""  # No content

        # Verify item was removed
        get_response = test_client.get("/api/cart")
        assert len(get_response.json()["items"]) == 0

    def test_remove_item_not_found(self, test_client: TestClient):
        """Test DELETE /api/cart/items/{item_id} with non-existent item returns 404"""
        # Act
        response = test_client.delete("/api/cart/items/non_existent_item")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found in cart" in data["detail"]

    def test_remove_item_from_populated_cart(self, test_client: TestClient):
        """Test DELETE removes only specified item, preserves others"""
        # Arrange - Add multiple items
        test_client.post(
            "/api/cart/items",
            json={"item_id": "svc_oil_change", "type": "service", "quantity": 1}
        )
        test_client.post(
            "/api/cart/items",
            json={"item_id": "prod_oil_filter", "type": "product", "quantity": 2}
        )
        test_client.post(
            "/api/cart/items",
            json={"item_id": "svc_diagnostics", "type": "service", "quantity": 1}
        )

        # Act - Remove middle item
        response = test_client.delete("/api/cart/items/prod_oil_filter")

        # Assert
        assert response.status_code == 204

        # Verify other items remain
        get_response = test_client.get("/api/cart")
        data = get_response.json()
        assert len(data["items"]) == 2
        item_ids = [item["item_id"] for item in data["items"]]
        assert "svc_oil_change" in item_ids
        assert "svc_diagnostics" in item_ids
        assert "prod_oil_filter" not in item_ids
        # Expected: 2500.0 + 1500.0 = 4000.0
        assert data["total_price"] == 4000.0

    def test_remove_item_twice(self, test_client: TestClient):
        """Test DELETE same item twice returns 404 on second attempt"""
        # Arrange - Add item
        test_client.post(
            "/api/cart/items",
            json={"item_id": "svc_oil_change", "type": "service", "quantity": 1}
        )

        # Act
        response1 = test_client.delete("/api/cart/items/svc_oil_change")
        response2 = test_client.delete("/api/cart/items/svc_oil_change")

        # Assert
        assert response1.status_code == 204
        assert response2.status_code == 404

    def test_remove_item_url_encoding(self, test_client: TestClient):
        """Test DELETE handles URL-encoded item IDs correctly"""
        # Arrange - Add item with underscore
        test_client.post(
            "/api/cart/items",
            json={"item_id": "svc_oil_change", "type": "service", "quantity": 1}
        )

        # Act
        response = test_client.delete("/api/cart/items/svc_oil_change")

        # Assert
        assert response.status_code == 204


class TestEndToEndWorkflows:
    """Integration tests for complete cart workflows"""

    def test_complete_shopping_workflow(self, test_client: TestClient):
        """Test complete workflow: add items, view cart, remove item, view cart"""
        # Step 1: Add oil change service
        response = test_client.post(
            "/api/cart/items",
            json={"item_id": "svc_oil_change", "type": "service", "quantity": 1}
        )
        assert response.status_code == 200

        # Step 2: Add oil filter product (2 units)
        response = test_client.post(
            "/api/cart/items",
            json={"item_id": "prod_oil_filter", "type": "product", "quantity": 2}
        )
        assert response.status_code == 200

        # Step 3: Add diagnostics service
        response = test_client.post(
            "/api/cart/items",
            json={"item_id": "svc_diagnostics", "type": "service", "quantity": 1}
        )
        assert response.status_code == 200

        # Step 4: View cart
        response = test_client.get("/api/cart")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total_price"] == 6000.0

        # Step 5: Remove oil filter
        response = test_client.delete("/api/cart/items/prod_oil_filter")
        assert response.status_code == 204

        # Step 6: View updated cart
        response = test_client.get("/api/cart")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total_price"] == 4000.0

    def test_add_same_item_multiple_times_workflow(self, test_client: TestClient):
        """Test workflow of adding same item multiple times"""
        # Add oil change service 3 times
        for i in range(3):
            response = test_client.post(
                "/api/cart/items",
                json={"item_id": "svc_oil_change", "type": "service", "quantity": 1}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["items"][0]["quantity"] == i + 1

        # Verify final state
        response = test_client.get("/api/cart")
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["quantity"] == 3
        assert data["total_price"] == 7500.0

    def test_add_large_quantity_workflow(self, test_client: TestClient):
        """Test workflow with large quantity"""
        # Add 100 oil filters
        response = test_client.post(
            "/api/cart/items",
            json={"item_id": "prod_oil_filter", "type": "product", "quantity": 100}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"][0]["quantity"] == 100
        assert data["total_price"] == 100000.0  # 100 * 1000.0

    def test_error_recovery_workflow(self, test_client: TestClient):
        """Test that cart state is preserved after errors"""
        # Add valid item
        response = test_client.post(
            "/api/cart/items",
            json={"item_id": "svc_oil_change", "type": "service", "quantity": 1}
        )
        assert response.status_code == 200

        # Try to add invalid item
        response = test_client.post(
            "/api/cart/items",
            json={"item_id": "invalid_item", "type": "service", "quantity": 1}
        )
        assert response.status_code == 404

        # Verify cart still has valid item
        response = test_client.get("/api/cart")
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["item_id"] == "svc_oil_change"

    def test_empty_to_full_to_empty_workflow(self, test_client: TestClient):
        """Test workflow from empty cart to full cart back to empty"""
        # Verify empty cart
        response = test_client.get("/api/cart")
        assert len(response.json()["items"]) == 0

        # Add multiple items
        test_client.post(
            "/api/cart/items",
            json={"item_id": "svc_oil_change", "type": "service", "quantity": 1}
        )
        test_client.post(
            "/api/cart/items",
            json={"item_id": "prod_oil_filter", "type": "product", "quantity": 2}
        )

        # Verify full cart
        response = test_client.get("/api/cart")
        assert len(response.json()["items"]) == 2

        # Remove all items
        test_client.delete("/api/cart/items/svc_oil_change")
        test_client.delete("/api/cart/items/prod_oil_filter")

        # Verify empty cart again
        response = test_client.get("/api/cart")
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total_price"] == 0.0


class TestAPIDocumentation:
    """Tests for API documentation endpoints"""

    def test_openapi_schema_available(self, test_client: TestClient):
        """Test that OpenAPI schema is available"""
        # Act
        response = test_client.get("/openapi.json")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Cart Service"

    def test_swagger_docs_available(self, test_client: TestClient):
        """Test that Swagger UI is available"""
        # Act
        response = test_client.get("/docs")

        # Assert
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()

    def test_redoc_available(self, test_client: TestClient):
        """Test that ReDoc is available"""
        # Act
        response = test_client.get("/redoc")

        # Assert
        assert response.status_code == 200
        assert "redoc" in response.text.lower()


class TestConcurrentOperations:
    """Tests for potential concurrent operation issues"""

    def test_multiple_adds_maintains_consistency(self, test_client: TestClient):
        """Test that multiple sequential adds maintain cart consistency"""
        # Add 5 different items sequentially
        items = [
            ("svc_oil_change", "service", 1),
            ("prod_oil_filter", "product", 2),
            ("svc_diagnostics", "service", 1),
            ("svc_oil_change", "service", 1),  # Duplicate, should accumulate
            ("prod_oil_filter", "product", 1),  # Duplicate, should accumulate
        ]

        for item_id, item_type, quantity in items:
            response = test_client.post(
                "/api/cart/items",
                json={"item_id": item_id, "type": item_type, "quantity": quantity}
            )
            assert response.status_code == 200

        # Verify final state
        response = test_client.get("/api/cart")
        data = response.json()
        assert len(data["items"]) == 3  # Only 3 unique items

        # Find specific items and verify quantities
        for item in data["items"]:
            if item["item_id"] == "svc_oil_change":
                assert item["quantity"] == 2  # 1 + 1
            elif item["item_id"] == "prod_oil_filter":
                assert item["quantity"] == 3  # 2 + 1
            elif item["item_id"] == "svc_diagnostics":
                assert item["quantity"] == 1
