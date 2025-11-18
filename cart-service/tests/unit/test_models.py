"""
Unit tests for Pydantic models in Cart Service

Tests cover:
- CartItem model validation
- CartResponse model validation
- AddItemRequest model validation
- Field validation rules (positive values, required fields)
- Edge cases and error scenarios
"""
import pytest
from uuid import UUID
from pydantic import ValidationError

from app.models.cart import CartItem, CartResponse, AddItemRequest


class TestCartItem:
    """Test suite for CartItem Pydantic model"""

    def test_cart_item_creation_success(self):
        """Test successful creation of CartItem with valid data"""
        # Arrange & Act
        item = CartItem(
            item_id="svc_oil_change",
            type="service",
            name="Замена масла",
            quantity=1,
            price=2500.00
        )

        # Assert
        assert item.item_id == "svc_oil_change"
        assert item.type == "service"
        assert item.name == "Замена масла"
        assert item.quantity == 1
        assert item.price == 2500.00

    def test_cart_item_with_multiple_quantity(self):
        """Test CartItem with quantity greater than 1"""
        # Arrange & Act
        item = CartItem(
            item_id="prod_oil_filter",
            type="product",
            name="Масляный фильтр",
            quantity=5,
            price=1000.00
        )

        # Assert
        assert item.quantity == 5
        assert item.price == 1000.00

    def test_cart_item_validation_zero_quantity(self):
        """Test that CartItem rejects zero quantity"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CartItem(
                item_id="test_item",
                type="service",
                name="Test",
                quantity=0,  # Invalid: must be > 0
                price=100.00
            )

        # Verify error is about quantity
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('quantity',) for error in errors)

    def test_cart_item_validation_negative_quantity(self):
        """Test that CartItem rejects negative quantity"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CartItem(
                item_id="test_item",
                type="service",
                name="Test",
                quantity=-1,  # Invalid: must be > 0
                price=100.00
            )

        # Verify error is about quantity
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('quantity',) for error in errors)

    def test_cart_item_validation_zero_price(self):
        """Test that CartItem rejects zero price"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CartItem(
                item_id="test_item",
                type="service",
                name="Test",
                quantity=1,
                price=0.0  # Invalid: must be > 0
            )

        # Verify error is about price
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('price',) for error in errors)

    def test_cart_item_validation_negative_price(self):
        """Test that CartItem rejects negative price"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CartItem(
                item_id="test_item",
                type="service",
                name="Test",
                quantity=1,
                price=-100.00  # Invalid: must be > 0
            )

        # Verify error is about price
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('price',) for error in errors)

    def test_cart_item_missing_required_fields(self):
        """Test that CartItem requires all fields"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CartItem(
                item_id="test_item",
                type="service"
                # Missing: name, quantity, price
            )

        # Verify multiple required fields are missing
        errors = exc_info.value.errors()
        error_fields = [error['loc'][0] for error in errors]
        assert 'name' in error_fields
        assert 'quantity' in error_fields
        assert 'price' in error_fields

    def test_cart_item_serialization(self):
        """Test CartItem can be serialized to dict"""
        # Arrange
        item = CartItem(
            item_id="svc_diagnostics",
            type="service",
            name="Диагностика",
            quantity=2,
            price=1500.00
        )

        # Act
        item_dict = item.model_dump()

        # Assert
        assert item_dict == {
            "item_id": "svc_diagnostics",
            "type": "service",
            "name": "Диагностика",
            "quantity": 2,
            "price": 1500.00
        }

    def test_cart_item_json_serialization(self):
        """Test CartItem can be serialized to JSON"""
        # Arrange
        item = CartItem(
            item_id="prod_oil_filter",
            type="product",
            name="Масляный фильтр",
            quantity=1,
            price=1000.00
        )

        # Act
        json_str = item.model_dump_json()

        # Assert
        assert '"item_id":"prod_oil_filter"' in json_str
        assert '"type":"product"' in json_str
        assert '"quantity":1' in json_str
        assert '"price":1000.0' in json_str


class TestCartResponse:
    """Test suite for CartResponse Pydantic model"""

    def test_cart_response_creation_success(self):
        """Test successful creation of CartResponse"""
        # Arrange
        user_id = UUID("12345678-1234-5678-1234-567812345678")
        items = [
            CartItem(
                item_id="svc_oil_change",
                type="service",
                name="Замена масла",
                quantity=1,
                price=2500.00
            )
        ]

        # Act
        response = CartResponse(
            user_id=user_id,
            items=items,
            total_price=2500.00
        )

        # Assert
        assert response.user_id == user_id
        assert len(response.items) == 1
        assert response.items[0].item_id == "svc_oil_change"
        assert response.total_price == 2500.00

    def test_cart_response_empty_cart(self):
        """Test CartResponse with empty cart"""
        # Arrange
        user_id = UUID("12345678-1234-5678-1234-567812345678")

        # Act
        response = CartResponse(
            user_id=user_id,
            items=[],
            total_price=0.0
        )

        # Assert
        assert response.user_id == user_id
        assert len(response.items) == 0
        assert response.total_price == 0.0

    def test_cart_response_multiple_items(self):
        """Test CartResponse with multiple items"""
        # Arrange
        user_id = UUID("12345678-1234-5678-1234-567812345678")
        items = [
            CartItem(
                item_id="svc_oil_change",
                type="service",
                name="Замена масла",
                quantity=1,
                price=2500.00
            ),
            CartItem(
                item_id="prod_oil_filter",
                type="product",
                name="Масляный фильтр",
                quantity=2,
                price=1000.00
            ),
            CartItem(
                item_id="svc_diagnostics",
                type="service",
                name="Диагностика",
                quantity=1,
                price=1500.00
            )
        ]

        # Act
        response = CartResponse(
            user_id=user_id,
            items=items,
            total_price=6000.00
        )

        # Assert
        assert len(response.items) == 3
        assert response.total_price == 6000.00

    def test_cart_response_validation_negative_total_price(self):
        """Test that CartResponse rejects negative total_price"""
        # Arrange
        user_id = UUID("12345678-1234-5678-1234-567812345678")

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CartResponse(
                user_id=user_id,
                items=[],
                total_price=-100.0  # Invalid: must be >= 0
            )

        # Verify error is about total_price
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('total_price',) for error in errors)

    def test_cart_response_defaults_to_empty_items(self):
        """Test that CartResponse defaults items to empty list"""
        # Arrange
        user_id = UUID("12345678-1234-5678-1234-567812345678")

        # Act
        response = CartResponse(
            user_id=user_id,
            total_price=0.0
            # items not provided, should default to []
        )

        # Assert
        assert response.items == []

    def test_cart_response_serialization(self):
        """Test CartResponse can be serialized to dict"""
        # Arrange
        user_id = UUID("12345678-1234-5678-1234-567812345678")
        items = [
            CartItem(
                item_id="svc_oil_change",
                type="service",
                name="Замена масла",
                quantity=1,
                price=2500.00
            )
        ]
        response = CartResponse(
            user_id=user_id,
            items=items,
            total_price=2500.00
        )

        # Act
        response_dict = response.model_dump()

        # Assert
        assert response_dict["user_id"] == user_id
        assert len(response_dict["items"]) == 1
        assert response_dict["total_price"] == 2500.00

    def test_cart_response_invalid_user_id(self):
        """Test that CartResponse validates UUID format"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            CartResponse(
                user_id="not-a-valid-uuid",  # Invalid UUID
                items=[],
                total_price=0.0
            )


class TestAddItemRequest:
    """Test suite for AddItemRequest Pydantic model"""

    def test_add_item_request_creation_success(self):
        """Test successful creation of AddItemRequest"""
        # Arrange & Act
        request = AddItemRequest(
            item_id="svc_oil_change",
            type="service",
            quantity=1
        )

        # Assert
        assert request.item_id == "svc_oil_change"
        assert request.type == "service"
        assert request.quantity == 1

    def test_add_item_request_product_type(self):
        """Test AddItemRequest with product type"""
        # Arrange & Act
        request = AddItemRequest(
            item_id="prod_oil_filter",
            type="product",
            quantity=3
        )

        # Assert
        assert request.item_id == "prod_oil_filter"
        assert request.type == "product"
        assert request.quantity == 3

    def test_add_item_request_validation_zero_quantity(self):
        """Test that AddItemRequest rejects zero quantity"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AddItemRequest(
                item_id="test_item",
                type="service",
                quantity=0  # Invalid: must be > 0
            )

        # Verify error is about quantity
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('quantity',) for error in errors)

    def test_add_item_request_validation_negative_quantity(self):
        """Test that AddItemRequest rejects negative quantity"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AddItemRequest(
                item_id="test_item",
                type="service",
                quantity=-5  # Invalid: must be > 0
            )

        # Verify error is about quantity
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('quantity',) for error in errors)

    def test_add_item_request_missing_required_fields(self):
        """Test that AddItemRequest requires all fields"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AddItemRequest(
                item_id="test_item"
                # Missing: type, quantity
            )

        # Verify multiple required fields are missing
        errors = exc_info.value.errors()
        error_fields = [error['loc'][0] for error in errors]
        assert 'type' in error_fields
        assert 'quantity' in error_fields

    def test_add_item_request_serialization(self):
        """Test AddItemRequest can be serialized to dict"""
        # Arrange
        request = AddItemRequest(
            item_id="svc_diagnostics",
            type="service",
            quantity=2
        )

        # Act
        request_dict = request.model_dump()

        # Assert
        assert request_dict == {
            "item_id": "svc_diagnostics",
            "type": "service",
            "quantity": 2
        }

    def test_add_item_request_large_quantity(self):
        """Test AddItemRequest with large quantity value"""
        # Arrange & Act
        request = AddItemRequest(
            item_id="prod_oil_filter",
            type="product",
            quantity=1000
        )

        # Assert
        assert request.quantity == 1000

    def test_add_item_request_empty_item_id(self):
        """Test AddItemRequest with empty item_id (should be allowed by Pydantic but may fail at service layer)"""
        # Arrange & Act
        request = AddItemRequest(
            item_id="",
            type="service",
            quantity=1
        )

        # Assert - Pydantic allows empty strings, business logic should handle this
        assert request.item_id == ""

    def test_add_item_request_empty_type(self):
        """Test AddItemRequest with empty type (should be allowed by Pydantic but may fail at service layer)"""
        # Arrange & Act
        request = AddItemRequest(
            item_id="test_item",
            type="",
            quantity=1
        )

        # Assert - Pydantic allows empty strings, business logic should handle this
        assert request.type == ""
