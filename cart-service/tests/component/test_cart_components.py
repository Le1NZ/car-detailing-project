"""
Component tests for Cart Service

Component tests verify the interaction between multiple internal components:
- API endpoints (FastAPI routes)
- Service layer (CartService with business logic)
- Repository layer (LocalCartRepo with data storage)
- CATALOG integration (product/service catalog validation)

These tests use REAL instances of all internal components (NO mocking of internal layers).
Only external dependencies would be mocked (cart-service has no external dependencies).
"""
import pytest
from fastapi.testclient import TestClient


class TestAddItemFromCatalogFlow:
    """
    Component Test 1: Add item from catalog flow

    Tests the complete flow of adding an item from the catalog:
    - API endpoint receives POST /api/cart/items request
    - Service validates item_id exists in CATALOG
    - Service creates CartItem with name and price from CATALOG
    - Repository stores the item in carts dict
    - GET /api/cart returns the added item with correct price

    All components work together WITHOUT mocking.
    """

    def test_add_item_from_catalog_flow(self, test_client: TestClient):
        """
        Test adding a product from catalog through all layers

        Flow:
        1. POST /api/cart/items with item_id from catalog
        2. CartService checks CATALOG and extracts name/price
        3. LocalCartRepo stores CartItem in _storage dict
        4. GET /api/cart retrieves item with correct catalog data

        Validates:
        - API layer accepts request and returns 200
        - Service layer validates against CATALOG
        - Service extracts correct name "Масляный фильтр" and price 1000.00
        - Repository correctly stores the item
        - Total price calculation works: 1000.00 * 2 = 2000.00
        """
        # Step 1: Add item from catalog via API
        add_response = test_client.post(
            "/api/cart/items",
            json={
                "item_id": "prod_oil_filter",
                "type": "product",
                "quantity": 2
            }
        )

        # Verify API accepted request
        assert add_response.status_code == 200
        add_data = add_response.json()

        # Verify Service extracted data from CATALOG
        assert len(add_data["items"]) == 1
        item = add_data["items"][0]
        assert item["item_id"] == "prod_oil_filter"
        assert item["type"] == "product"
        assert item["name"] == "Масляный фильтр"  # From CATALOG
        assert item["price"] == 1000.00  # From CATALOG
        assert item["quantity"] == 2

        # Verify Service calculated total_price correctly
        assert add_data["total_price"] == 2000.00  # 1000.00 * 2

        # Step 2: Verify Repository stored data by fetching cart
        get_response = test_client.get("/api/cart")
        assert get_response.status_code == 200
        get_data = get_response.json()

        # Verify data persisted through Repository
        assert len(get_data["items"]) == 1
        stored_item = get_data["items"][0]
        assert stored_item["item_id"] == "prod_oil_filter"
        assert stored_item["name"] == "Масляный фильтр"
        assert stored_item["price"] == 1000.00
        assert stored_item["quantity"] == 2
        assert get_data["total_price"] == 2000.00


class TestQuantityAccumulationFlow:
    """
    Component Test 2: Quantity accumulation flow

    Tests that adding the same item multiple times accumulates quantity:
    - First POST adds item with quantity=2
    - Second POST adds same item with quantity=3
    - Repository accumulates quantity (total=5)
    - Service recalculates total_price based on accumulated quantity
    - GET /api/cart shows quantity=5

    Validates interaction between Service and Repository for quantity logic.
    """

    def test_quantity_accumulation_flow(self, test_client: TestClient):
        """
        Test that adding same item multiple times accumulates quantity

        Flow:
        1. POST item with quantity=2
        2. Repository stores new item with quantity=2
        3. POST same item with quantity=3
        4. Repository finds existing item and accumulates: 2 + 3 = 5
        5. Service recalculates total_price: 2500.00 * 5 = 12500.00
        6. GET confirms accumulated quantity

        Validates:
        - Repository correctly identifies duplicate item_id
        - Repository accumulates quantity instead of creating duplicate
        - Service recalculates total after each addition
        """
        # Step 1: Add item first time (quantity=2)
        response1 = test_client.post(
            "/api/cart/items",
            json={
                "item_id": "svc_oil_change",
                "type": "service",
                "quantity": 2
            }
        )

        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["items"]) == 1
        assert data1["items"][0]["quantity"] == 2
        assert data1["total_price"] == 5000.00  # 2500.00 * 2

        # Step 2: Add same item again (quantity=3)
        response2 = test_client.post(
            "/api/cart/items",
            json={
                "item_id": "svc_oil_change",
                "type": "service",
                "quantity": 3
            }
        )

        assert response2.status_code == 200
        data2 = response2.json()

        # Verify Repository accumulated quantity (not duplicated)
        assert len(data2["items"]) == 1  # Still only one unique item
        assert data2["items"][0]["quantity"] == 5  # 2 + 3 = 5

        # Verify Service recalculated total_price
        assert data2["total_price"] == 12500.00  # 2500.00 * 5

        # Step 3: Verify persistence via GET
        get_response = test_client.get("/api/cart")
        get_data = get_response.json()

        assert len(get_data["items"]) == 1
        assert get_data["items"][0]["item_id"] == "svc_oil_change"
        assert get_data["items"][0]["quantity"] == 5
        assert get_data["total_price"] == 12500.00


class TestTotalPriceCalculationAcrossLayers:
    """
    Component Test 3: Total price calculation across all layers

    Tests that total_price is correctly calculated when multiple different items
    are added:
    - Add multiple different items via API
    - Service calculates price * quantity for each item
    - Repository stores all items
    - GET /api/cart returns correct sum of all (price * quantity)

    Validates the complete data flow for price calculation.
    """

    def test_total_price_calculation_across_layers(self, test_client: TestClient):
        """
        Test total_price calculation with multiple items through all layers

        Flow:
        1. POST first item: svc_oil_change (qty=2, price=2500.00)
        2. POST second item: prod_oil_filter (qty=3, price=1000.00)
        3. POST third item: svc_diagnostics (qty=1, price=1500.00)
        4. Repository stores all 3 items separately
        5. Service calculates: (2500*2) + (1000*3) + (1500*1) = 9500.00
        6. GET returns all items with correct total

        Validates:
        - Repository maintains multiple distinct items
        - Service correctly sums price*quantity for all items
        - API returns complete cart state
        """
        # Add first item: Oil Change (2x @ 2500.00 = 5000.00)
        response1 = test_client.post(
            "/api/cart/items",
            json={
                "item_id": "svc_oil_change",
                "type": "service",
                "quantity": 2
            }
        )
        assert response1.status_code == 200
        assert response1.json()["total_price"] == 5000.00

        # Add second item: Oil Filter (3x @ 1000.00 = 3000.00)
        response2 = test_client.post(
            "/api/cart/items",
            json={
                "item_id": "prod_oil_filter",
                "type": "product",
                "quantity": 3
            }
        )
        assert response2.status_code == 200
        assert response2.json()["total_price"] == 8000.00  # 5000 + 3000

        # Add third item: Diagnostics (1x @ 1500.00 = 1500.00)
        response3 = test_client.post(
            "/api/cart/items",
            json={
                "item_id": "svc_diagnostics",
                "type": "service",
                "quantity": 1
            }
        )
        assert response3.status_code == 200
        data3 = response3.json()

        # Verify Repository stored all 3 items
        assert len(data3["items"]) == 3

        # Verify Service calculated correct total: 5000 + 3000 + 1500 = 9500
        assert data3["total_price"] == 9500.00

        # Verify all items have correct data from CATALOG
        items_by_id = {item["item_id"]: item for item in data3["items"]}

        assert items_by_id["svc_oil_change"]["name"] == "Замена масла"
        assert items_by_id["svc_oil_change"]["price"] == 2500.00
        assert items_by_id["svc_oil_change"]["quantity"] == 2

        assert items_by_id["prod_oil_filter"]["name"] == "Масляный фильтр"
        assert items_by_id["prod_oil_filter"]["price"] == 1000.00
        assert items_by_id["prod_oil_filter"]["quantity"] == 3

        assert items_by_id["svc_diagnostics"]["name"] == "Диагностика"
        assert items_by_id["svc_diagnostics"]["price"] == 1500.00
        assert items_by_id["svc_diagnostics"]["quantity"] == 1

        # Final verification via GET
        get_response = test_client.get("/api/cart")
        get_data = get_response.json()

        assert len(get_data["items"]) == 3
        assert get_data["total_price"] == 9500.00


class TestRemoveItemFlow:
    """
    Component Test 4: Remove item flow

    Tests the complete flow of removing an item:
    - Add 3 items via API
    - DELETE one item via API
    - Service calls Repository.remove_item()
    - Repository removes item from _storage dict
    - GET /api/cart shows only 2 remaining items

    Validates coordination between all layers for delete operations.
    """

    def test_remove_item_flow(self, test_client: TestClient):
        """
        Test removing item from cart through all layers

        Flow:
        1. POST 3 different items to cart
        2. Verify all 3 stored in Repository
        3. DELETE middle item via API
        4. Service calls Repository.remove_item()
        5. Repository filters out item from list
        6. GET shows only 2 items remain
        7. Service recalculates total_price for remaining items

        Validates:
        - API DELETE endpoint works
        - Service validates item exists before removal
        - Repository correctly removes specific item
        - Repository preserves other items
        - Service recalculates total after removal
        """
        # Step 1: Add 3 items
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

        # Verify all 3 items added
        get_response1 = test_client.get("/api/cart")
        data1 = get_response1.json()
        assert len(data1["items"]) == 3
        # Total: 2500 + (1000*2) + 1500 = 6000
        assert data1["total_price"] == 6000.00

        # Step 2: Remove middle item (oil filter)
        delete_response = test_client.delete("/api/cart/items/prod_oil_filter")

        # Verify API returned 204 No Content
        assert delete_response.status_code == 204
        assert delete_response.text == ""

        # Step 3: Verify Repository removed item and Service recalculated total
        get_response2 = test_client.get("/api/cart")
        data2 = get_response2.json()

        # Only 2 items remain
        assert len(data2["items"]) == 2

        # Verify correct items remain (oil filter removed)
        item_ids = {item["item_id"] for item in data2["items"]}
        assert "svc_oil_change" in item_ids
        assert "svc_diagnostics" in item_ids
        assert "prod_oil_filter" not in item_ids

        # Verify Service recalculated total: 2500 + 1500 = 4000
        assert data2["total_price"] == 4000.00


class TestCatalogValidationThroughService:
    """
    Component Test 5: Catalog validation through service layer

    Tests catalog validation when attempting to add non-existent item:
    - Attempt to POST item with invalid item_id
    - Service checks CATALOG and raises HTTPException
    - Repository is NOT modified
    - API returns 404 error
    - GET confirms cart remains unchanged

    Validates error handling across all layers.
    """

    def test_catalog_validation_through_service(self, test_client: TestClient):
        """
        Test that invalid item_id is rejected by Service layer

        Flow:
        1. Attempt POST with non-existent item_id
        2. Service validates against CATALOG
        3. Service raises HTTPException(404)
        4. Repository.add_item() is NOT called
        5. API returns 404 error response
        6. GET confirms Repository unchanged (empty cart)

        Validates:
        - Service layer properly validates catalog
        - Error propagates correctly to API layer
        - Repository remains unchanged after validation error
        - API returns appropriate error response
        """
        # Step 1: Verify cart starts empty
        get_response1 = test_client.get("/api/cart")
        data1 = get_response1.json()
        assert len(data1["items"]) == 0
        assert data1["total_price"] == 0.0

        # Step 2: Attempt to add item not in CATALOG
        add_response = test_client.post(
            "/api/cart/items",
            json={
                "item_id": "non_existent_item_xyz",
                "type": "service",
                "quantity": 1
            }
        )

        # Verify Service caught invalid item_id and API returned 404
        assert add_response.status_code == 404
        error_data = add_response.json()
        assert "detail" in error_data
        assert "not found in catalog" in error_data["detail"].lower()
        assert "non_existent_item_xyz" in error_data["detail"]

        # Step 3: Verify Repository was NOT modified
        get_response2 = test_client.get("/api/cart")
        data2 = get_response2.json()

        # Cart still empty - Repository unchanged
        assert len(data2["items"]) == 0
        assert data2["total_price"] == 0.0

        # Step 4: Add valid item to ensure system still works
        valid_response = test_client.post(
            "/api/cart/items",
            json={
                "item_id": "svc_oil_change",
                "type": "service",
                "quantity": 1
            }
        )

        assert valid_response.status_code == 200
        valid_data = valid_response.json()
        assert len(valid_data["items"]) == 1
        assert valid_data["items"][0]["item_id"] == "svc_oil_change"

        # Step 5: Now try invalid type mismatch (another validation scenario)
        type_mismatch_response = test_client.post(
            "/api/cart/items",
            json={
                "item_id": "svc_oil_change",  # This is a service
                "type": "product",  # Wrong type!
                "quantity": 1
            }
        )

        # Verify Service caught type mismatch
        assert type_mismatch_response.status_code == 400
        error_data2 = type_mismatch_response.json()
        assert "detail" in error_data2
        assert "type mismatch" in error_data2["detail"].lower()

        # Step 6: Verify Repository unchanged (still has only 1 item)
        get_response3 = test_client.get("/api/cart")
        data3 = get_response3.json()

        assert len(data3["items"]) == 1  # Still only the valid item
        assert data3["items"][0]["item_id"] == "svc_oil_change"
