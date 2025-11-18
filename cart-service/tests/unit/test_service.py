"""
Unit tests for CartService business logic layer

Tests cover:
- get_cart() - retrieving cart with calculated total
- add_item() - adding items with catalog validation
- remove_item() - removing items with error handling
- _calculate_total_price() - price calculation logic
- get_catalog() - catalog retrieval
- Error scenarios: invalid item_id, type mismatch, item not found
"""
import pytest
from uuid import UUID
from unittest.mock import Mock
from fastapi import HTTPException

from app.services.cart_service import CartService, CATALOG
from app.models.cart import CartItem, CartResponse, AddItemRequest
from app.repositories.local_cart_repo import LocalCartRepo


# Test user IDs
TEST_USER_ID = UUID("12345678-1234-5678-1234-567812345678")


class TestCartServiceGetCart:
    """Test suite for get_cart() method"""

    def test_get_cart_empty_cart(self, cart_service: CartService):
        """Test get_cart returns empty cart with zero total price"""
        # Arrange
        service = cart_service

        # Act
        response = service.get_cart(TEST_USER_ID)

        # Assert
        assert isinstance(response, CartResponse)
        assert response.user_id == TEST_USER_ID
        assert response.items == []
        assert response.total_price == 0.0

    def test_get_cart_with_single_item(self, cart_service_with_data: CartService):
        """Test get_cart returns cart with calculated total price"""
        # Arrange
        service = cart_service_with_data

        # Act
        response = service.get_cart(TEST_USER_ID)

        # Assert
        assert isinstance(response, CartResponse)
        assert response.user_id == TEST_USER_ID
        assert len(response.items) == 1
        assert response.total_price == 2500.0  # 1 * 2500.0

    def test_get_cart_with_multiple_items(self, cart_service: CartService):
        """Test get_cart calculates total price for multiple items"""
        # Arrange
        service = cart_service
        request1 = AddItemRequest(item_id="svc_oil_change", type="service", quantity=1)
        request2 = AddItemRequest(item_id="prod_oil_filter", type="product", quantity=2)
        request3 = AddItemRequest(item_id="svc_diagnostics", type="service", quantity=1)
        service.add_item(TEST_USER_ID, request1)
        service.add_item(TEST_USER_ID, request2)
        service.add_item(TEST_USER_ID, request3)

        # Act
        response = service.get_cart(TEST_USER_ID)

        # Assert
        assert len(response.items) == 3
        # Expected: 2500.0 + (1000.0 * 2) + 1500.0 = 6000.0
        assert response.total_price == 6000.0

    def test_get_cart_uses_repository(self, mock_cart_repo: Mock):
        """Test get_cart calls repository get_cart method"""
        # Arrange
        service = CartService(mock_cart_repo)
        sample_item = CartItem(
            item_id="test_item",
            type="service",
            name="Test",
            quantity=1,
            price=100.0
        )
        mock_cart_repo.get_cart.return_value = [sample_item]

        # Act
        response = service.get_cart(TEST_USER_ID)

        # Assert
        mock_cart_repo.get_cart.assert_called_once_with(TEST_USER_ID)
        assert len(response.items) == 1
        assert response.total_price == 100.0


class TestCartServiceAddItem:
    """Test suite for add_item() method"""

    def test_add_item_from_catalog_success(self, cart_service: CartService):
        """Test adding valid item from catalog"""
        # Arrange
        service = cart_service
        request = AddItemRequest(
            item_id="svc_oil_change",
            type="service",
            quantity=1
        )

        # Act
        response = service.add_item(TEST_USER_ID, request)

        # Assert
        assert isinstance(response, CartResponse)
        assert len(response.items) == 1
        assert response.items[0].item_id == "svc_oil_change"
        assert response.items[0].name == "Замена масла"
        assert response.items[0].price == 2500.0
        assert response.items[0].quantity == 1
        assert response.total_price == 2500.0

    def test_add_item_product_from_catalog(self, cart_service: CartService):
        """Test adding product from catalog"""
        # Arrange
        service = cart_service
        request = AddItemRequest(
            item_id="prod_oil_filter",
            type="product",
            quantity=3
        )

        # Act
        response = service.add_item(TEST_USER_ID, request)

        # Assert
        assert len(response.items) == 1
        assert response.items[0].item_id == "prod_oil_filter"
        assert response.items[0].type == "product"
        assert response.items[0].quantity == 3
        assert response.total_price == 3000.0  # 3 * 1000.0

    def test_add_item_not_in_catalog(self, cart_service: CartService):
        """Test adding item not in catalog raises 404 HTTPException"""
        # Arrange
        service = cart_service
        request = AddItemRequest(
            item_id="non_existent_item",
            type="service",
            quantity=1
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.add_item(TEST_USER_ID, request)

        assert exc_info.value.status_code == 404
        assert "not found in catalog" in exc_info.value.detail

    def test_add_item_type_mismatch(self, cart_service: CartService):
        """Test adding item with wrong type raises 400 HTTPException"""
        # Arrange
        service = cart_service
        request = AddItemRequest(
            item_id="svc_oil_change",  # This is a service
            type="product",  # Wrong type
            quantity=1
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.add_item(TEST_USER_ID, request)

        assert exc_info.value.status_code == 400
        assert "type mismatch" in exc_info.value.detail

    def test_add_item_accumulates_quantity(self, cart_service: CartService):
        """Test adding same item multiple times accumulates quantity"""
        # Arrange
        service = cart_service
        request1 = AddItemRequest(item_id="svc_oil_change", type="service", quantity=1)
        request2 = AddItemRequest(item_id="svc_oil_change", type="service", quantity=2)

        # Act
        service.add_item(TEST_USER_ID, request1)
        response = service.add_item(TEST_USER_ID, request2)

        # Assert
        assert len(response.items) == 1  # No duplicate
        assert response.items[0].quantity == 3  # 1 + 2
        assert response.total_price == 7500.0  # 3 * 2500.0

    def test_add_item_multiple_different_items(self, cart_service: CartService):
        """Test adding multiple different items"""
        # Arrange
        service = cart_service
        request1 = AddItemRequest(item_id="svc_oil_change", type="service", quantity=1)
        request2 = AddItemRequest(item_id="prod_oil_filter", type="product", quantity=2)

        # Act
        service.add_item(TEST_USER_ID, request1)
        response = service.add_item(TEST_USER_ID, request2)

        # Assert
        assert len(response.items) == 2
        assert response.total_price == 4500.0  # 2500.0 + (1000.0 * 2)

    def test_add_item_uses_catalog_data(self, cart_service: CartService):
        """Test that add_item uses name and price from catalog, not request"""
        # Arrange
        service = cart_service
        request = AddItemRequest(
            item_id="svc_diagnostics",
            type="service",
            quantity=2
        )

        # Act
        response = service.add_item(TEST_USER_ID, request)

        # Assert
        assert response.items[0].name == "Диагностика"  # From catalog
        assert response.items[0].price == 1500.0  # From catalog
        assert response.total_price == 3000.0  # 2 * 1500.0

    def test_add_item_calls_repository(self, mock_cart_repo: Mock):
        """Test add_item calls repository add_item method"""
        # Arrange
        service = CartService(mock_cart_repo)
        request = AddItemRequest(
            item_id="svc_oil_change",
            type="service",
            quantity=1
        )
        mock_cart_repo.add_item.return_value = []

        # Act
        service.add_item(TEST_USER_ID, request)

        # Assert
        mock_cart_repo.add_item.assert_called_once()
        call_args = mock_cart_repo.add_item.call_args
        assert call_args[0][0] == TEST_USER_ID  # First positional arg is user_id
        assert isinstance(call_args[0][1], CartItem)  # Second arg is CartItem

    def test_add_item_validates_before_repository_call(self, mock_cart_repo: Mock):
        """Test add_item validates item before calling repository"""
        # Arrange
        service = CartService(mock_cart_repo)
        request = AddItemRequest(
            item_id="invalid_item",
            type="service",
            quantity=1
        )

        # Act & Assert
        with pytest.raises(HTTPException):
            service.add_item(TEST_USER_ID, request)

        # Repository should not be called if validation fails
        mock_cart_repo.add_item.assert_not_called()


class TestCartServiceRemoveItem:
    """Test suite for remove_item() method"""

    def test_remove_item_success(self, cart_service: CartService):
        """Test successful removal of item from cart"""
        # Arrange
        service = cart_service
        request = AddItemRequest(item_id="svc_oil_change", type="service", quantity=1)
        service.add_item(TEST_USER_ID, request)

        # Act - Should not raise exception
        service.remove_item(TEST_USER_ID, "svc_oil_change")

        # Assert - Verify item was removed
        response = service.get_cart(TEST_USER_ID)
        assert len(response.items) == 0

    def test_remove_item_not_found(self, cart_service: CartService):
        """Test removing non-existent item raises 404 HTTPException"""
        # Arrange
        service = cart_service

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.remove_item(TEST_USER_ID, "non_existent_item")

        assert exc_info.value.status_code == 404
        assert "not found in cart" in exc_info.value.detail

    def test_remove_item_from_populated_cart(self, cart_service: CartService):
        """Test removing one item preserves other items"""
        # Arrange
        service = cart_service
        request1 = AddItemRequest(item_id="svc_oil_change", type="service", quantity=1)
        request2 = AddItemRequest(item_id="prod_oil_filter", type="product", quantity=2)
        service.add_item(TEST_USER_ID, request1)
        service.add_item(TEST_USER_ID, request2)

        # Act
        service.remove_item(TEST_USER_ID, "svc_oil_change")

        # Assert
        response = service.get_cart(TEST_USER_ID)
        assert len(response.items) == 1
        assert response.items[0].item_id == "prod_oil_filter"

    def test_remove_item_calls_repository(self, mock_cart_repo: Mock):
        """Test remove_item calls repository remove_item method"""
        # Arrange
        service = CartService(mock_cart_repo)
        mock_cart_repo.remove_item.return_value = True

        # Act
        service.remove_item(TEST_USER_ID, "test_item")

        # Assert
        mock_cart_repo.remove_item.assert_called_once_with(TEST_USER_ID, "test_item")

    def test_remove_item_repository_returns_false(self, mock_cart_repo: Mock):
        """Test remove_item raises exception when repository returns False"""
        # Arrange
        service = CartService(mock_cart_repo)
        mock_cart_repo.remove_item.return_value = False

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.remove_item(TEST_USER_ID, "non_existent_item")

        assert exc_info.value.status_code == 404


class TestCartServiceCalculateTotalPrice:
    """Test suite for _calculate_total_price() static method"""

    def test_calculate_total_price_empty_list(self):
        """Test calculate total price for empty cart"""
        # Arrange
        items = []

        # Act
        total = CartService._calculate_total_price(items)

        # Assert
        assert total == 0.0

    def test_calculate_total_price_single_item(self):
        """Test calculate total price for single item"""
        # Arrange
        items = [
            CartItem(
                item_id="test_item",
                type="service",
                name="Test",
                quantity=1,
                price=100.0
            )
        ]

        # Act
        total = CartService._calculate_total_price(items)

        # Assert
        assert total == 100.0

    def test_calculate_total_price_multiple_quantities(self):
        """Test calculate total price with quantity > 1"""
        # Arrange
        items = [
            CartItem(
                item_id="test_item",
                type="product",
                name="Test",
                quantity=5,
                price=200.0
            )
        ]

        # Act
        total = CartService._calculate_total_price(items)

        # Assert
        assert total == 1000.0  # 5 * 200.0

    def test_calculate_total_price_multiple_items(self):
        """Test calculate total price for multiple different items"""
        # Arrange
        items = [
            CartItem(
                item_id="item1",
                type="service",
                name="Service 1",
                quantity=1,
                price=2500.0
            ),
            CartItem(
                item_id="item2",
                type="product",
                name="Product 1",
                quantity=2,
                price=1000.0
            ),
            CartItem(
                item_id="item3",
                type="service",
                name="Service 2",
                quantity=1,
                price=1500.0
            )
        ]

        # Act
        total = CartService._calculate_total_price(items)

        # Assert
        # Expected: 2500.0 + (1000.0 * 2) + 1500.0 = 6000.0
        assert total == 6000.0

    def test_calculate_total_price_rounding(self):
        """Test calculate total price rounds to 2 decimal places"""
        # Arrange
        items = [
            CartItem(
                item_id="test_item",
                type="product",
                name="Test",
                quantity=3,
                price=10.333333
            )
        ]

        # Act
        total = CartService._calculate_total_price(items)

        # Assert
        assert total == 31.0  # 3 * 10.333333 = 30.999999 -> 31.0 (rounded)

    def test_calculate_total_price_large_numbers(self):
        """Test calculate total price with large quantities and prices"""
        # Arrange
        items = [
            CartItem(
                item_id="test_item",
                type="product",
                name="Test",
                quantity=1000,
                price=50.99
            )
        ]

        # Act
        total = CartService._calculate_total_price(items)

        # Assert
        assert total == 50990.0  # 1000 * 50.99

    def test_calculate_total_price_decimal_precision(self):
        """Test calculate total price maintains decimal precision"""
        # Arrange
        items = [
            CartItem(
                item_id="item1",
                type="product",
                name="Product 1",
                quantity=1,
                price=10.99
            ),
            CartItem(
                item_id="item2",
                type="product",
                name="Product 2",
                quantity=2,
                price=5.49
            )
        ]

        # Act
        total = CartService._calculate_total_price(items)

        # Assert
        # Expected: 10.99 + (5.49 * 2) = 10.99 + 10.98 = 21.97
        assert total == 21.97


class TestCartServiceGetCatalog:
    """Test suite for get_catalog() method"""

    def test_get_catalog_returns_catalog(self, cart_service: CartService):
        """Test get_catalog returns the CATALOG dictionary"""
        # Arrange
        service = cart_service

        # Act
        catalog = service.get_catalog()

        # Assert
        assert catalog == CATALOG
        assert isinstance(catalog, dict)

    def test_get_catalog_contains_expected_items(self, cart_service: CartService):
        """Test catalog contains all expected items"""
        # Arrange
        service = cart_service

        # Act
        catalog = service.get_catalog()

        # Assert
        assert "svc_oil_change" in catalog
        assert "prod_oil_filter" in catalog
        assert "svc_diagnostics" in catalog

    def test_get_catalog_item_structure(self, cart_service: CartService):
        """Test catalog items have correct structure"""
        # Arrange
        service = cart_service

        # Act
        catalog = service.get_catalog()

        # Assert
        for item_id, item_data in catalog.items():
            assert "type" in item_data
            assert "name" in item_data
            assert "price" in item_data
            assert item_data["type"] in ["service", "product"]
            assert isinstance(item_data["name"], str)
            assert isinstance(item_data["price"], float)


class TestCartServiceIntegration:
    """Integration tests for CartService with real repository"""

    def test_full_cart_workflow(self, cart_service: CartService):
        """Test complete cart workflow: add multiple items, get cart, remove item"""
        # Arrange
        service = cart_service

        # Act - Add items
        request1 = AddItemRequest(item_id="svc_oil_change", type="service", quantity=1)
        request2 = AddItemRequest(item_id="prod_oil_filter", type="product", quantity=2)
        request3 = AddItemRequest(item_id="svc_diagnostics", type="service", quantity=1)
        service.add_item(TEST_USER_ID, request1)
        service.add_item(TEST_USER_ID, request2)
        service.add_item(TEST_USER_ID, request3)

        # Assert - Get cart
        response = service.get_cart(TEST_USER_ID)
        assert len(response.items) == 3
        assert response.total_price == 6000.0

        # Act - Remove item
        service.remove_item(TEST_USER_ID, "prod_oil_filter")

        # Assert - Verify removal
        response = service.get_cart(TEST_USER_ID)
        assert len(response.items) == 2
        assert response.total_price == 4000.0  # 2500.0 + 1500.0

    def test_add_same_item_multiple_times(self, cart_service: CartService):
        """Test adding same item multiple times accumulates correctly"""
        # Arrange
        service = cart_service

        # Act
        for _ in range(3):
            request = AddItemRequest(item_id="svc_oil_change", type="service", quantity=1)
            service.add_item(TEST_USER_ID, request)

        # Assert
        response = service.get_cart(TEST_USER_ID)
        assert len(response.items) == 1
        assert response.items[0].quantity == 3
        assert response.total_price == 7500.0  # 3 * 2500.0

    def test_error_handling_preserves_cart_state(self, cart_service: CartService):
        """Test that failed operations don't corrupt cart state"""
        # Arrange
        service = cart_service
        request = AddItemRequest(item_id="svc_oil_change", type="service", quantity=1)
        service.add_item(TEST_USER_ID, request)

        # Act - Try to add invalid item
        try:
            invalid_request = AddItemRequest(
                item_id="invalid_item",
                type="service",
                quantity=1
            )
            service.add_item(TEST_USER_ID, invalid_request)
        except HTTPException:
            pass

        # Assert - Original cart should be unchanged
        response = service.get_cart(TEST_USER_ID)
        assert len(response.items) == 1
        assert response.items[0].item_id == "svc_oil_change"
