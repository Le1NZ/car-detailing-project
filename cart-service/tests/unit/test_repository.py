"""
Unit tests for LocalCartRepo repository layer

Tests cover:
- get_cart() - retrieving user carts
- add_item() - adding items and quantity accumulation
- remove_item() - removing items from cart
- clear_cart() - clearing all items
- get_all_carts() - retrieving all carts
- Edge cases: non-existent users, duplicate items, empty carts
"""
import pytest
from uuid import UUID

from app.repositories.local_cart_repo import LocalCartRepo
from app.models.cart import CartItem


# Test user IDs
TEST_USER_ID = UUID("12345678-1234-5678-1234-567812345678")
ANOTHER_USER_ID = UUID("87654321-4321-8765-4321-876543218765")


class TestLocalCartRepoGetCart:
    """Test suite for get_cart() method"""

    def test_get_cart_empty_for_new_user(self, clean_cart_repo: LocalCartRepo):
        """Test get_cart returns empty list for user without cart"""
        # Arrange
        repo = clean_cart_repo

        # Act
        cart = repo.get_cart(TEST_USER_ID)

        # Assert
        assert cart == []
        assert isinstance(cart, list)

    def test_get_cart_returns_items(self, clean_cart_repo: LocalCartRepo, sample_cart_item: CartItem):
        """Test get_cart returns items for user with cart"""
        # Arrange
        repo = clean_cart_repo
        repo.add_item(TEST_USER_ID, sample_cart_item)

        # Act
        cart = repo.get_cart(TEST_USER_ID)

        # Assert
        assert len(cart) == 1
        assert cart[0].item_id == sample_cart_item.item_id
        assert cart[0].quantity == sample_cart_item.quantity

    def test_get_cart_multiple_items(self, clean_cart_repo: LocalCartRepo):
        """Test get_cart returns all items for a user"""
        # Arrange
        repo = clean_cart_repo
        item1 = CartItem(
            item_id="item1",
            type="service",
            name="Service 1",
            quantity=1,
            price=100.0
        )
        item2 = CartItem(
            item_id="item2",
            type="product",
            name="Product 1",
            quantity=2,
            price=200.0
        )
        repo.add_item(TEST_USER_ID, item1)
        repo.add_item(TEST_USER_ID, item2)

        # Act
        cart = repo.get_cart(TEST_USER_ID)

        # Assert
        assert len(cart) == 2
        item_ids = [item.item_id for item in cart]
        assert "item1" in item_ids
        assert "item2" in item_ids

    def test_get_cart_isolation_between_users(self, clean_cart_repo: LocalCartRepo):
        """Test that carts are isolated between different users"""
        # Arrange
        repo = clean_cart_repo
        item1 = CartItem(
            item_id="item1",
            type="service",
            name="Service 1",
            quantity=1,
            price=100.0
        )
        item2 = CartItem(
            item_id="item2",
            type="product",
            name="Product 1",
            quantity=2,
            price=200.0
        )
        repo.add_item(TEST_USER_ID, item1)
        repo.add_item(ANOTHER_USER_ID, item2)

        # Act
        cart1 = repo.get_cart(TEST_USER_ID)
        cart2 = repo.get_cart(ANOTHER_USER_ID)

        # Assert
        assert len(cart1) == 1
        assert cart1[0].item_id == "item1"
        assert len(cart2) == 1
        assert cart2[0].item_id == "item2"


class TestLocalCartRepoAddItem:
    """Test suite for add_item() method"""

    def test_add_item_to_empty_cart(self, clean_cart_repo: LocalCartRepo, sample_cart_item: CartItem):
        """Test adding first item to cart creates new cart"""
        # Arrange
        repo = clean_cart_repo

        # Act
        result = repo.add_item(TEST_USER_ID, sample_cart_item)

        # Assert
        assert len(result) == 1
        assert result[0].item_id == sample_cart_item.item_id
        assert result[0].quantity == sample_cart_item.quantity

    def test_add_item_returns_updated_cart(self, clean_cart_repo: LocalCartRepo):
        """Test add_item returns the updated cart list"""
        # Arrange
        repo = clean_cart_repo
        item = CartItem(
            item_id="test_item",
            type="service",
            name="Test Service",
            quantity=1,
            price=100.0
        )

        # Act
        result = repo.add_item(TEST_USER_ID, item)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1

    def test_add_item_accumulates_quantity_for_existing_item(self, clean_cart_repo: LocalCartRepo):
        """Test that adding existing item increases quantity instead of duplicating"""
        # Arrange
        repo = clean_cart_repo
        item1 = CartItem(
            item_id="svc_oil_change",
            type="service",
            name="Замена масла",
            quantity=1,
            price=2500.0
        )
        item2 = CartItem(
            item_id="svc_oil_change",
            type="service",
            name="Замена масла",
            quantity=2,
            price=2500.0
        )

        # Act
        repo.add_item(TEST_USER_ID, item1)
        result = repo.add_item(TEST_USER_ID, item2)

        # Assert
        assert len(result) == 1  # Should not duplicate
        assert result[0].quantity == 3  # 1 + 2

    def test_add_item_multiple_different_items(self, clean_cart_repo: LocalCartRepo):
        """Test adding multiple different items to cart"""
        # Arrange
        repo = clean_cart_repo
        item1 = CartItem(
            item_id="item1",
            type="service",
            name="Service 1",
            quantity=1,
            price=100.0
        )
        item2 = CartItem(
            item_id="item2",
            type="product",
            name="Product 1",
            quantity=2,
            price=200.0
        )
        item3 = CartItem(
            item_id="item3",
            type="service",
            name="Service 2",
            quantity=1,
            price=150.0
        )

        # Act
        repo.add_item(TEST_USER_ID, item1)
        repo.add_item(TEST_USER_ID, item2)
        result = repo.add_item(TEST_USER_ID, item3)

        # Assert
        assert len(result) == 3
        item_ids = [item.item_id for item in result]
        assert "item1" in item_ids
        assert "item2" in item_ids
        assert "item3" in item_ids

    def test_add_item_preserves_existing_items(self, clean_cart_repo: LocalCartRepo):
        """Test that adding new item preserves existing items in cart"""
        # Arrange
        repo = clean_cart_repo
        item1 = CartItem(
            item_id="item1",
            type="service",
            name="Service 1",
            quantity=1,
            price=100.0
        )
        item2 = CartItem(
            item_id="item2",
            type="product",
            name="Product 1",
            quantity=2,
            price=200.0
        )

        # Act
        repo.add_item(TEST_USER_ID, item1)
        result = repo.add_item(TEST_USER_ID, item2)

        # Assert
        assert len(result) == 2
        # Verify first item still exists with original quantity
        first_item = next(item for item in result if item.item_id == "item1")
        assert first_item.quantity == 1

    def test_add_item_large_quantity(self, clean_cart_repo: LocalCartRepo):
        """Test adding item with large quantity"""
        # Arrange
        repo = clean_cart_repo
        item = CartItem(
            item_id="test_item",
            type="product",
            name="Test Product",
            quantity=1000,
            price=10.0
        )

        # Act
        result = repo.add_item(TEST_USER_ID, item)

        # Assert
        assert result[0].quantity == 1000

    def test_add_item_accumulation_preserves_original_properties(self, clean_cart_repo: LocalCartRepo):
        """Test that quantity accumulation preserves original item properties"""
        # Arrange
        repo = clean_cart_repo
        item1 = CartItem(
            item_id="svc_oil_change",
            type="service",
            name="Замена масла",
            quantity=1,
            price=2500.0
        )
        item2 = CartItem(
            item_id="svc_oil_change",
            type="service",
            name="Замена масла",
            quantity=1,
            price=2500.0
        )

        # Act
        repo.add_item(TEST_USER_ID, item1)
        result = repo.add_item(TEST_USER_ID, item2)

        # Assert
        assert result[0].name == "Замена масла"
        assert result[0].type == "service"
        assert result[0].price == 2500.0
        assert result[0].quantity == 2


class TestLocalCartRepoRemoveItem:
    """Test suite for remove_item() method"""

    def test_remove_item_success(self, clean_cart_repo: LocalCartRepo, sample_cart_item: CartItem):
        """Test successful removal of item from cart"""
        # Arrange
        repo = clean_cart_repo
        repo.add_item(TEST_USER_ID, sample_cart_item)

        # Act
        result = repo.remove_item(TEST_USER_ID, sample_cart_item.item_id)

        # Assert
        assert result is True
        cart = repo.get_cart(TEST_USER_ID)
        assert len(cart) == 0

    def test_remove_item_from_empty_cart(self, clean_cart_repo: LocalCartRepo):
        """Test removing item from non-existent cart returns False"""
        # Arrange
        repo = clean_cart_repo

        # Act
        result = repo.remove_item(TEST_USER_ID, "non_existent_item")

        # Assert
        assert result is False

    def test_remove_item_non_existent_item(self, clean_cart_repo: LocalCartRepo, sample_cart_item: CartItem):
        """Test removing non-existent item from populated cart returns False"""
        # Arrange
        repo = clean_cart_repo
        repo.add_item(TEST_USER_ID, sample_cart_item)

        # Act
        result = repo.remove_item(TEST_USER_ID, "non_existent_item")

        # Assert
        assert result is False
        # Verify original item still in cart
        cart = repo.get_cart(TEST_USER_ID)
        assert len(cart) == 1

    def test_remove_item_preserves_other_items(self, clean_cart_repo: LocalCartRepo):
        """Test that removing one item preserves other items in cart"""
        # Arrange
        repo = clean_cart_repo
        item1 = CartItem(
            item_id="item1",
            type="service",
            name="Service 1",
            quantity=1,
            price=100.0
        )
        item2 = CartItem(
            item_id="item2",
            type="product",
            name="Product 1",
            quantity=2,
            price=200.0
        )
        item3 = CartItem(
            item_id="item3",
            type="service",
            name="Service 2",
            quantity=1,
            price=150.0
        )
        repo.add_item(TEST_USER_ID, item1)
        repo.add_item(TEST_USER_ID, item2)
        repo.add_item(TEST_USER_ID, item3)

        # Act
        result = repo.remove_item(TEST_USER_ID, "item2")

        # Assert
        assert result is True
        cart = repo.get_cart(TEST_USER_ID)
        assert len(cart) == 2
        item_ids = [item.item_id for item in cart]
        assert "item1" in item_ids
        assert "item3" in item_ids
        assert "item2" not in item_ids

    def test_remove_item_multiple_times(self, clean_cart_repo: LocalCartRepo, sample_cart_item: CartItem):
        """Test removing same item multiple times"""
        # Arrange
        repo = clean_cart_repo
        repo.add_item(TEST_USER_ID, sample_cart_item)

        # Act
        result1 = repo.remove_item(TEST_USER_ID, sample_cart_item.item_id)
        result2 = repo.remove_item(TEST_USER_ID, sample_cart_item.item_id)

        # Assert
        assert result1 is True  # First removal succeeds
        assert result2 is False  # Second removal fails (item already removed)

    def test_remove_item_isolation_between_users(self, clean_cart_repo: LocalCartRepo):
        """Test that removing item from one user's cart doesn't affect other users"""
        # Arrange
        repo = clean_cart_repo
        item = CartItem(
            item_id="shared_item",
            type="service",
            name="Shared Service",
            quantity=1,
            price=100.0
        )
        repo.add_item(TEST_USER_ID, item)
        repo.add_item(ANOTHER_USER_ID, item)

        # Act
        result = repo.remove_item(TEST_USER_ID, "shared_item")

        # Assert
        assert result is True
        cart1 = repo.get_cart(TEST_USER_ID)
        cart2 = repo.get_cart(ANOTHER_USER_ID)
        assert len(cart1) == 0  # Item removed from TEST_USER_ID
        assert len(cart2) == 1  # Item still in ANOTHER_USER_ID cart


class TestLocalCartRepoClearCart:
    """Test suite for clear_cart() method"""

    def test_clear_cart_success(self, clean_cart_repo: LocalCartRepo):
        """Test clearing cart removes all items"""
        # Arrange
        repo = clean_cart_repo
        item1 = CartItem(
            item_id="item1",
            type="service",
            name="Service 1",
            quantity=1,
            price=100.0
        )
        item2 = CartItem(
            item_id="item2",
            type="product",
            name="Product 1",
            quantity=2,
            price=200.0
        )
        repo.add_item(TEST_USER_ID, item1)
        repo.add_item(TEST_USER_ID, item2)

        # Act
        repo.clear_cart(TEST_USER_ID)

        # Assert
        cart = repo.get_cart(TEST_USER_ID)
        assert len(cart) == 0

    def test_clear_cart_non_existent_user(self, clean_cart_repo: LocalCartRepo):
        """Test clearing cart for non-existent user doesn't raise error"""
        # Arrange
        repo = clean_cart_repo

        # Act & Assert - Should not raise exception
        repo.clear_cart(TEST_USER_ID)

    def test_clear_cart_isolation_between_users(self, clean_cart_repo: LocalCartRepo):
        """Test that clearing one user's cart doesn't affect other users"""
        # Arrange
        repo = clean_cart_repo
        item = CartItem(
            item_id="test_item",
            type="service",
            name="Test Service",
            quantity=1,
            price=100.0
        )
        repo.add_item(TEST_USER_ID, item)
        repo.add_item(ANOTHER_USER_ID, item)

        # Act
        repo.clear_cart(TEST_USER_ID)

        # Assert
        cart1 = repo.get_cart(TEST_USER_ID)
        cart2 = repo.get_cart(ANOTHER_USER_ID)
        assert len(cart1) == 0  # Cleared
        assert len(cart2) == 1  # Not affected

    def test_clear_cart_allows_adding_after_clear(self, clean_cart_repo: LocalCartRepo):
        """Test that items can be added after cart is cleared"""
        # Arrange
        repo = clean_cart_repo
        item = CartItem(
            item_id="test_item",
            type="service",
            name="Test Service",
            quantity=1,
            price=100.0
        )
        repo.add_item(TEST_USER_ID, item)
        repo.clear_cart(TEST_USER_ID)

        # Act
        result = repo.add_item(TEST_USER_ID, item)

        # Assert
        assert len(result) == 1
        assert result[0].item_id == "test_item"


class TestLocalCartRepoGetAllCarts:
    """Test suite for get_all_carts() method"""

    def test_get_all_carts_empty(self, clean_cart_repo: LocalCartRepo):
        """Test get_all_carts returns empty dict when no carts exist"""
        # Arrange
        repo = clean_cart_repo

        # Act
        all_carts = repo.get_all_carts()

        # Assert
        assert all_carts == {}
        assert isinstance(all_carts, dict)

    def test_get_all_carts_single_user(self, clean_cart_repo: LocalCartRepo, sample_cart_item: CartItem):
        """Test get_all_carts returns single user's cart"""
        # Arrange
        repo = clean_cart_repo
        repo.add_item(TEST_USER_ID, sample_cart_item)

        # Act
        all_carts = repo.get_all_carts()

        # Assert
        assert len(all_carts) == 1
        assert TEST_USER_ID in all_carts
        assert len(all_carts[TEST_USER_ID]) == 1

    def test_get_all_carts_multiple_users(self, clean_cart_repo: LocalCartRepo):
        """Test get_all_carts returns all users' carts"""
        # Arrange
        repo = clean_cart_repo
        item1 = CartItem(
            item_id="item1",
            type="service",
            name="Service 1",
            quantity=1,
            price=100.0
        )
        item2 = CartItem(
            item_id="item2",
            type="product",
            name="Product 1",
            quantity=2,
            price=200.0
        )
        repo.add_item(TEST_USER_ID, item1)
        repo.add_item(ANOTHER_USER_ID, item2)

        # Act
        all_carts = repo.get_all_carts()

        # Assert
        assert len(all_carts) == 2
        assert TEST_USER_ID in all_carts
        assert ANOTHER_USER_ID in all_carts
        assert len(all_carts[TEST_USER_ID]) == 1
        assert len(all_carts[ANOTHER_USER_ID]) == 1

    def test_get_all_carts_returns_reference(self, clean_cart_repo: LocalCartRepo):
        """Test that get_all_carts returns reference to internal storage (be aware!)"""
        # Arrange
        repo = clean_cart_repo
        item = CartItem(
            item_id="test_item",
            type="service",
            name="Test Service",
            quantity=1,
            price=100.0
        )
        repo.add_item(TEST_USER_ID, item)

        # Act
        all_carts = repo.get_all_carts()

        # Verify it's the actual internal storage (not a copy)
        assert all_carts is repo._storage
