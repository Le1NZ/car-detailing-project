"""Unit tests for LocalBonusRepository"""
import pytest
from uuid import UUID

from app.repositories.local_bonus_repo import LocalBonusRepository, Promocode


@pytest.mark.unit
class TestPromocodeClass:
    """Test Promocode data class"""

    def test_create_promocode(self):
        """Test creating a promocode instance"""
        # Arrange & Act
        promo = Promocode(code="TEST", discount_amount=100.0, active=True)

        # Assert
        assert promo.code == "TEST"
        assert promo.discount_amount == 100.0
        assert promo.active is True

    def test_create_promocode_default_active(self):
        """Test promocode defaults to active"""
        # Arrange & Act
        promo = Promocode(code="TEST", discount_amount=100.0)

        # Assert
        assert promo.active is True

    def test_create_inactive_promocode(self):
        """Test creating inactive promocode"""
        # Arrange & Act
        promo = Promocode(code="EXPIRED", discount_amount=500.0, active=False)

        # Assert
        assert promo.active is False


@pytest.mark.unit
class TestLocalBonusRepositoryInitialization:
    """Test repository initialization"""

    def test_initialization(self, fresh_repository: LocalBonusRepository):
        """Test repository initializes with empty balances and predefined promocodes"""
        # Assert
        assert isinstance(fresh_repository.user_balances, dict)
        assert len(fresh_repository.user_balances) == 0
        assert isinstance(fresh_repository.promocodes, list)
        assert len(fresh_repository.promocodes) >= 2

    def test_predefined_promocodes(self, fresh_repository: LocalBonusRepository):
        """Test that predefined promocodes are loaded"""
        # Arrange
        expected_codes = ["SUMMER24", "WELCOME10"]

        # Act
        actual_codes = [promo.code for promo in fresh_repository.promocodes]

        # Assert
        for code in expected_codes:
            assert code in actual_codes

    def test_promocodes_are_active(self, fresh_repository: LocalBonusRepository):
        """Test that all predefined promocodes are active"""
        # Assert
        for promo in fresh_repository.promocodes:
            assert promo.active is True

    def test_summer24_promocode_values(self, fresh_repository: LocalBonusRepository):
        """Test SUMMER24 promocode has correct discount"""
        # Act
        summer_promo = next(
            (p for p in fresh_repository.promocodes if p.code == "SUMMER24"),
            None
        )

        # Assert
        assert summer_promo is not None
        assert summer_promo.discount_amount == 500.0
        assert summer_promo.active is True

    def test_welcome10_promocode_values(self, fresh_repository: LocalBonusRepository):
        """Test WELCOME10 promocode has correct discount"""
        # Act
        welcome_promo = next(
            (p for p in fresh_repository.promocodes if p.code == "WELCOME10"),
            None
        )

        # Assert
        assert welcome_promo is not None
        assert welcome_promo.discount_amount == 1000.0
        assert welcome_promo.active is True


@pytest.mark.unit
@pytest.mark.asyncio
class TestGetUserBalance:
    """Test get_user_balance method"""

    async def test_get_balance_for_new_user(
        self, fresh_repository: LocalBonusRepository, test_user_id: UUID
    ):
        """Test getting balance for user with no balance returns 0"""
        # Act
        balance = await fresh_repository.get_user_balance(test_user_id)

        # Assert
        assert balance == 0.0

    async def test_get_balance_for_existing_user(
        self, fresh_repository: LocalBonusRepository, test_user_id: UUID
    ):
        """Test getting balance for user with existing balance"""
        # Arrange
        fresh_repository.user_balances[test_user_id] = 1500.0

        # Act
        balance = await fresh_repository.get_user_balance(test_user_id)

        # Assert
        assert balance == 1500.0

    async def test_get_balance_does_not_modify_repository(
        self, fresh_repository: LocalBonusRepository, test_user_id: UUID
    ):
        """Test that getting balance doesn't modify the repository"""
        # Arrange
        initial_size = len(fresh_repository.user_balances)

        # Act
        await fresh_repository.get_user_balance(test_user_id)

        # Assert
        assert len(fresh_repository.user_balances) == initial_size


@pytest.mark.unit
@pytest.mark.asyncio
class TestAddBonuses:
    """Test add_bonuses method"""

    async def test_add_bonuses_to_new_user(
        self, fresh_repository: LocalBonusRepository, test_user_id: UUID
    ):
        """Test adding bonuses to user with no existing balance"""
        # Act
        new_balance = await fresh_repository.add_bonuses(test_user_id, 100.0)

        # Assert
        assert new_balance == 100.0
        assert fresh_repository.user_balances[test_user_id] == 100.0

    async def test_add_bonuses_to_existing_user(
        self, fresh_repository: LocalBonusRepository, test_user_id: UUID
    ):
        """Test adding bonuses to user with existing balance"""
        # Arrange
        fresh_repository.user_balances[test_user_id] = 500.0

        # Act
        new_balance = await fresh_repository.add_bonuses(test_user_id, 250.0)

        # Assert
        assert new_balance == 750.0
        assert fresh_repository.user_balances[test_user_id] == 750.0

    async def test_add_zero_bonuses(
        self, fresh_repository: LocalBonusRepository, test_user_id: UUID
    ):
        """Test adding zero bonuses"""
        # Arrange
        fresh_repository.user_balances[test_user_id] = 100.0

        # Act
        new_balance = await fresh_repository.add_bonuses(test_user_id, 0.0)

        # Assert
        assert new_balance == 100.0

    async def test_add_fractional_bonuses(
        self, fresh_repository: LocalBonusRepository, test_user_id: UUID
    ):
        """Test adding fractional bonus amounts"""
        # Act
        new_balance = await fresh_repository.add_bonuses(test_user_id, 123.45)

        # Assert
        assert new_balance == 123.45

    async def test_add_bonuses_multiple_users(
        self,
        fresh_repository: LocalBonusRepository,
        test_user_id: UUID,
        different_user_id: UUID
    ):
        """Test adding bonuses to multiple users independently"""
        # Act
        balance1 = await fresh_repository.add_bonuses(test_user_id, 100.0)
        balance2 = await fresh_repository.add_bonuses(different_user_id, 200.0)

        # Assert
        assert balance1 == 100.0
        assert balance2 == 200.0
        assert fresh_repository.user_balances[test_user_id] == 100.0
        assert fresh_repository.user_balances[different_user_id] == 200.0

    async def test_add_large_amount(
        self, fresh_repository: LocalBonusRepository, test_user_id: UUID
    ):
        """Test adding large bonus amounts"""
        # Act
        new_balance = await fresh_repository.add_bonuses(test_user_id, 1000000.0)

        # Assert
        assert new_balance == 1000000.0


@pytest.mark.unit
@pytest.mark.asyncio
class TestSpendBonuses:
    """Test spend_bonuses method"""

    async def test_spend_bonuses_sufficient_balance(
        self, fresh_repository: LocalBonusRepository, test_user_id: UUID
    ):
        """Test spending bonuses when user has sufficient balance"""
        # Arrange
        fresh_repository.user_balances[test_user_id] = 1000.0

        # Act
        new_balance = await fresh_repository.spend_bonuses(test_user_id, 300)

        # Assert
        assert new_balance == 700.0
        assert fresh_repository.user_balances[test_user_id] == 700.0

    async def test_spend_all_bonuses(
        self, fresh_repository: LocalBonusRepository, test_user_id: UUID
    ):
        """Test spending all available bonuses"""
        # Arrange
        fresh_repository.user_balances[test_user_id] = 500.0

        # Act
        new_balance = await fresh_repository.spend_bonuses(test_user_id, 500)

        # Assert
        assert new_balance == 0.0

    async def test_spend_bonuses_insufficient_balance_raises_error(
        self, fresh_repository: LocalBonusRepository, test_user_id: UUID
    ):
        """Test spending more bonuses than available raises ValueError"""
        # Arrange
        fresh_repository.user_balances[test_user_id] = 100.0

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await fresh_repository.spend_bonuses(test_user_id, 200)

        assert "Insufficient bonuses" in str(exc_info.value)
        assert "100.0" in str(exc_info.value)
        assert "200" in str(exc_info.value)

    async def test_spend_bonuses_no_balance_raises_error(
        self, fresh_repository: LocalBonusRepository, test_user_id: UUID
    ):
        """Test spending bonuses with no balance raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await fresh_repository.spend_bonuses(test_user_id, 100)

        assert "Insufficient bonuses" in str(exc_info.value)

    async def test_spend_bonuses_does_not_affect_other_users(
        self,
        fresh_repository: LocalBonusRepository,
        test_user_id: UUID,
        different_user_id: UUID
    ):
        """Test spending bonuses for one user doesn't affect others"""
        # Arrange
        fresh_repository.user_balances[test_user_id] = 1000.0
        fresh_repository.user_balances[different_user_id] = 2000.0

        # Act
        await fresh_repository.spend_bonuses(test_user_id, 500)

        # Assert
        assert fresh_repository.user_balances[test_user_id] == 500.0
        assert fresh_repository.user_balances[different_user_id] == 2000.0

    async def test_spend_bonuses_error_does_not_modify_balance(
        self, fresh_repository: LocalBonusRepository, test_user_id: UUID
    ):
        """Test that failed spending doesn't modify balance"""
        # Arrange
        fresh_repository.user_balances[test_user_id] = 100.0

        # Act
        with pytest.raises(ValueError):
            await fresh_repository.spend_bonuses(test_user_id, 200)

        # Assert - balance unchanged
        assert fresh_repository.user_balances[test_user_id] == 100.0


@pytest.mark.unit
@pytest.mark.asyncio
class TestFindPromocode:
    """Test find_promocode method"""

    async def test_find_valid_promocode(self, fresh_repository: LocalBonusRepository):
        """Test finding a valid active promocode"""
        # Act
        promo = await fresh_repository.find_promocode("SUMMER24")

        # Assert
        assert promo is not None
        assert promo.code == "SUMMER24"
        assert promo.discount_amount == 500.0
        assert promo.active is True

    async def test_find_another_valid_promocode(self, fresh_repository: LocalBonusRepository):
        """Test finding another valid promocode"""
        # Act
        promo = await fresh_repository.find_promocode("WELCOME10")

        # Assert
        assert promo is not None
        assert promo.code == "WELCOME10"
        assert promo.discount_amount == 1000.0

    async def test_find_invalid_promocode_returns_none(
        self, fresh_repository: LocalBonusRepository
    ):
        """Test finding non-existent promocode returns None"""
        # Act
        promo = await fresh_repository.find_promocode("INVALID")

        # Assert
        assert promo is None

    async def test_find_inactive_promocode_returns_none(
        self, fresh_repository: LocalBonusRepository
    ):
        """Test finding inactive promocode returns None"""
        # Arrange - add inactive promocode
        fresh_repository.promocodes.append(
            Promocode(code="EXPIRED", discount_amount=1000.0, active=False)
        )

        # Act
        promo = await fresh_repository.find_promocode("EXPIRED")

        # Assert
        assert promo is None

    async def test_find_promocode_case_sensitive(
        self, fresh_repository: LocalBonusRepository
    ):
        """Test promocode search is case-sensitive"""
        # Act
        promo = await fresh_repository.find_promocode("summer24")

        # Assert
        assert promo is None

    async def test_find_promocode_empty_string(
        self, fresh_repository: LocalBonusRepository
    ):
        """Test finding promocode with empty string"""
        # Act
        promo = await fresh_repository.find_promocode("")

        # Assert
        assert promo is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestRepositoryIntegration:
    """Test repository integration scenarios"""

    async def test_complete_bonus_lifecycle(
        self, fresh_repository: LocalBonusRepository, test_user_id: UUID
    ):
        """Test complete lifecycle: add, check, spend bonuses"""
        # Add bonuses
        balance1 = await fresh_repository.add_bonuses(test_user_id, 1000.0)
        assert balance1 == 1000.0

        # Check balance
        current_balance = await fresh_repository.get_user_balance(test_user_id)
        assert current_balance == 1000.0

        # Spend some bonuses
        balance2 = await fresh_repository.spend_bonuses(test_user_id, 300)
        assert balance2 == 700.0

        # Add more bonuses
        balance3 = await fresh_repository.add_bonuses(test_user_id, 200.0)
        assert balance3 == 900.0

        # Final check
        final_balance = await fresh_repository.get_user_balance(test_user_id)
        assert final_balance == 900.0

    async def test_multiple_operations_different_users(
        self,
        fresh_repository: LocalBonusRepository,
        test_user_id: UUID,
        different_user_id: UUID
    ):
        """Test multiple operations across different users"""
        # User 1 operations
        await fresh_repository.add_bonuses(test_user_id, 500.0)
        await fresh_repository.spend_bonuses(test_user_id, 100)

        # User 2 operations
        await fresh_repository.add_bonuses(different_user_id, 1000.0)
        await fresh_repository.spend_bonuses(different_user_id, 200)

        # Verify final balances
        balance1 = await fresh_repository.get_user_balance(test_user_id)
        balance2 = await fresh_repository.get_user_balance(different_user_id)

        assert balance1 == 400.0
        assert balance2 == 800.0

    async def test_promocode_operations_dont_affect_balances(
        self, fresh_repository: LocalBonusRepository, test_user_id: UUID
    ):
        """Test that finding promocodes doesn't affect user balances"""
        # Arrange
        await fresh_repository.add_bonuses(test_user_id, 500.0)
        initial_balance = await fresh_repository.get_user_balance(test_user_id)

        # Act - find promocodes
        await fresh_repository.find_promocode("SUMMER24")
        await fresh_repository.find_promocode("INVALID")

        # Assert - balance unchanged
        final_balance = await fresh_repository.get_user_balance(test_user_id)
        assert final_balance == initial_balance
