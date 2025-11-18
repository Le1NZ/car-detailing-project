"""Unit tests for BonusService business logic"""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, Mock

from app.services.bonus_service import BonusService
from app.repositories.local_bonus_repo import Promocode


@pytest.mark.unit
@pytest.mark.asyncio
class TestApplyPromocode:
    """Test apply_promocode method"""

    async def test_apply_valid_promocode_success(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_order_id: UUID
    ):
        """Test successfully applying a valid promocode"""
        # Arrange
        mock_promo = Mock(spec=Promocode)
        mock_promo.code = "SUMMER24"
        mock_promo.discount_amount = 500.0
        mock_promo.active = True
        mock_repository.find_promocode.return_value = mock_promo

        # Act
        status, discount = await bonus_service.apply_promocode(test_order_id, "SUMMER24")

        # Assert
        assert status == "applied"
        assert discount == 500.0
        mock_repository.find_promocode.assert_called_once_with("SUMMER24")

    async def test_apply_welcome_promocode(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_order_id: UUID
    ):
        """Test applying WELCOME10 promocode"""
        # Arrange
        mock_promo = Mock(spec=Promocode)
        mock_promo.code = "WELCOME10"
        mock_promo.discount_amount = 1000.0
        mock_promo.active = True
        mock_repository.find_promocode.return_value = mock_promo

        # Act
        status, discount = await bonus_service.apply_promocode(test_order_id, "WELCOME10")

        # Assert
        assert status == "applied"
        assert discount == 1000.0

    async def test_apply_invalid_promocode_raises_error(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_order_id: UUID
    ):
        """Test applying invalid promocode raises ValueError"""
        # Arrange
        mock_repository.find_promocode.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await bonus_service.apply_promocode(test_order_id, "INVALID")

        assert "invalid or inactive" in str(exc_info.value).lower()
        assert "INVALID" in str(exc_info.value)

    async def test_apply_inactive_promocode_raises_error(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_order_id: UUID
    ):
        """Test applying inactive promocode raises ValueError"""
        # Arrange - repository returns None for inactive codes
        mock_repository.find_promocode.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await bonus_service.apply_promocode(test_order_id, "EXPIRED")

        assert "invalid or inactive" in str(exc_info.value).lower()

    async def test_apply_promocode_empty_string_raises_error(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_order_id: UUID
    ):
        """Test applying empty promocode raises ValueError"""
        # Arrange
        mock_repository.find_promocode.return_value = None

        # Act & Assert
        with pytest.raises(ValueError):
            await bonus_service.apply_promocode(test_order_id, "")

    async def test_apply_promocode_case_sensitivity(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_order_id: UUID
    ):
        """Test promocode application is case-sensitive"""
        # Arrange - repository returns None for wrong case
        mock_repository.find_promocode.return_value = None

        # Act & Assert
        with pytest.raises(ValueError):
            await bonus_service.apply_promocode(test_order_id, "summer24")

        mock_repository.find_promocode.assert_called_once_with("summer24")

    async def test_apply_promocode_with_zero_discount(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_order_id: UUID
    ):
        """Test applying promocode with zero discount"""
        # Arrange
        mock_promo = Mock(spec=Promocode)
        mock_promo.code = "ZERO"
        mock_promo.discount_amount = 0.0
        mock_promo.active = True
        mock_repository.find_promocode.return_value = mock_promo

        # Act
        status, discount = await bonus_service.apply_promocode(test_order_id, "ZERO")

        # Assert
        assert status == "applied"
        assert discount == 0.0


@pytest.mark.unit
@pytest.mark.asyncio
class TestSpendBonuses:
    """Test spend_bonuses method"""

    async def test_spend_bonuses_sufficient_balance_success(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_user_id: UUID,
        test_order_id: UUID
    ):
        """Test spending bonuses when user has sufficient balance"""
        # Arrange
        mock_repository.get_user_balance.return_value = 1000.0
        mock_repository.spend_bonuses.return_value = 700.0

        # Act
        bonuses_spent, new_balance = await bonus_service.spend_bonuses(
            user_id=test_user_id,
            order_id=test_order_id,
            amount=300
        )

        # Assert
        assert bonuses_spent == 300
        assert new_balance == 700.0
        mock_repository.get_user_balance.assert_called_once_with(test_user_id)
        mock_repository.spend_bonuses.assert_called_once_with(test_user_id, 300)

    async def test_spend_all_bonuses(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_user_id: UUID,
        test_order_id: UUID
    ):
        """Test spending all available bonuses"""
        # Arrange
        mock_repository.get_user_balance.return_value = 500.0
        mock_repository.spend_bonuses.return_value = 0.0

        # Act
        bonuses_spent, new_balance = await bonus_service.spend_bonuses(
            user_id=test_user_id,
            order_id=test_order_id,
            amount=500
        )

        # Assert
        assert bonuses_spent == 500
        assert new_balance == 0.0

    async def test_spend_bonuses_insufficient_balance_raises_error(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_user_id: UUID,
        test_order_id: UUID
    ):
        """Test spending more bonuses than available raises ValueError"""
        # Arrange
        mock_repository.get_user_balance.return_value = 100.0

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await bonus_service.spend_bonuses(
                user_id=test_user_id,
                order_id=test_order_id,
                amount=200
            )

        assert "Insufficient bonuses" in str(exc_info.value)
        assert "100.0" in str(exc_info.value)
        assert "200" in str(exc_info.value)

    async def test_spend_bonuses_no_balance_raises_error(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_user_id: UUID,
        test_order_id: UUID
    ):
        """Test spending bonuses with zero balance raises ValueError"""
        # Arrange
        mock_repository.get_user_balance.return_value = 0.0

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await bonus_service.spend_bonuses(
                user_id=test_user_id,
                order_id=test_order_id,
                amount=100
            )

        assert "Insufficient bonuses" in str(exc_info.value)

    async def test_spend_bonuses_fractional_balance(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_user_id: UUID,
        test_order_id: UUID
    ):
        """Test spending bonuses with fractional balance"""
        # Arrange
        mock_repository.get_user_balance.return_value = 123.45
        mock_repository.spend_bonuses.return_value = 23.45

        # Act
        bonuses_spent, new_balance = await bonus_service.spend_bonuses(
            user_id=test_user_id,
            order_id=test_order_id,
            amount=100
        )

        # Assert
        assert bonuses_spent == 100
        assert new_balance == 23.45

    async def test_spend_bonuses_exact_balance(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_user_id: UUID,
        test_order_id: UUID
    ):
        """Test spending exact balance amount"""
        # Arrange
        mock_repository.get_user_balance.return_value = 100.0
        mock_repository.spend_bonuses.return_value = 0.0

        # Act
        bonuses_spent, new_balance = await bonus_service.spend_bonuses(
            user_id=test_user_id,
            order_id=test_order_id,
            amount=100
        )

        # Assert
        assert bonuses_spent == 100
        assert new_balance == 0.0

    async def test_spend_bonuses_repository_error_propagates(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_user_id: UUID,
        test_order_id: UUID
    ):
        """Test that repository errors propagate correctly"""
        # Arrange
        mock_repository.get_user_balance.return_value = 1000.0
        mock_repository.spend_bonuses.side_effect = ValueError("Insufficient bonuses. Current balance: 1000.0, requested: 1500")

        # Act & Assert
        with pytest.raises(ValueError):
            await bonus_service.spend_bonuses(
                user_id=test_user_id,
                order_id=test_order_id,
                amount=1500
            )


@pytest.mark.unit
@pytest.mark.asyncio
class TestAccrueBonuses:
    """Test accrue_bonuses method"""

    async def test_accrue_bonuses_standard_rate(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_user_id: UUID,
        test_order_id: UUID
    ):
        """Test accruing bonuses with standard 1% rate"""
        # Arrange
        mock_repository.add_bonuses.return_value = 100.0

        # Act
        bonuses = await bonus_service.accrue_bonuses(
            user_id=test_user_id,
            order_id=test_order_id,
            payment_amount=10000.0,
            rate=0.01
        )

        # Assert
        assert bonuses == 100.0
        mock_repository.add_bonuses.assert_called_once_with(test_user_id, 100.0)

    async def test_accrue_bonuses_different_rate(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_user_id: UUID,
        test_order_id: UUID
    ):
        """Test accruing bonuses with custom rate"""
        # Arrange
        mock_repository.add_bonuses.return_value = 250.0

        # Act
        bonuses = await bonus_service.accrue_bonuses(
            user_id=test_user_id,
            order_id=test_order_id,
            payment_amount=10000.0,
            rate=0.025  # 2.5%
        )

        # Assert
        assert bonuses == 250.0
        mock_repository.add_bonuses.assert_called_once_with(test_user_id, 250.0)

    async def test_accrue_bonuses_small_payment(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_user_id: UUID,
        test_order_id: UUID
    ):
        """Test accruing bonuses for small payment amount"""
        # Arrange
        mock_repository.add_bonuses.return_value = 1.0

        # Act
        bonuses = await bonus_service.accrue_bonuses(
            user_id=test_user_id,
            order_id=test_order_id,
            payment_amount=100.0,
            rate=0.01
        )

        # Assert
        assert bonuses == 1.0

    async def test_accrue_bonuses_large_payment(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_user_id: UUID,
        test_order_id: UUID
    ):
        """Test accruing bonuses for large payment amount"""
        # Arrange
        mock_repository.add_bonuses.return_value = 10000.0

        # Act
        bonuses = await bonus_service.accrue_bonuses(
            user_id=test_user_id,
            order_id=test_order_id,
            payment_amount=1000000.0,
            rate=0.01
        )

        # Assert
        assert bonuses == 10000.0

    async def test_accrue_bonuses_fractional_result(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_user_id: UUID,
        test_order_id: UUID
    ):
        """Test accruing bonuses results in fractional amount"""
        # Arrange
        mock_repository.add_bonuses.return_value = 123.45

        # Act
        bonuses = await bonus_service.accrue_bonuses(
            user_id=test_user_id,
            order_id=test_order_id,
            payment_amount=12345.0,
            rate=0.01
        )

        # Assert
        assert bonuses == 123.45
        mock_repository.add_bonuses.assert_called_once_with(test_user_id, 123.45)

    async def test_accrue_bonuses_zero_rate(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_user_id: UUID,
        test_order_id: UUID
    ):
        """Test accruing bonuses with zero rate"""
        # Arrange
        mock_repository.add_bonuses.return_value = 0.0

        # Act
        bonuses = await bonus_service.accrue_bonuses(
            user_id=test_user_id,
            order_id=test_order_id,
            payment_amount=10000.0,
            rate=0.0
        )

        # Assert
        assert bonuses == 0.0
        mock_repository.add_bonuses.assert_called_once_with(test_user_id, 0.0)

    async def test_accrue_bonuses_zero_payment(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_user_id: UUID,
        test_order_id: UUID
    ):
        """Test accruing bonuses for zero payment amount"""
        # Arrange
        mock_repository.add_bonuses.return_value = 0.0

        # Act
        bonuses = await bonus_service.accrue_bonuses(
            user_id=test_user_id,
            order_id=test_order_id,
            payment_amount=0.0,
            rate=0.01
        )

        # Assert
        assert bonuses == 0.0

    async def test_accrue_bonuses_high_rate(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_user_id: UUID,
        test_order_id: UUID
    ):
        """Test accruing bonuses with high rate"""
        # Arrange
        mock_repository.add_bonuses.return_value = 5000.0

        # Act
        bonuses = await bonus_service.accrue_bonuses(
            user_id=test_user_id,
            order_id=test_order_id,
            payment_amount=10000.0,
            rate=0.5  # 50%
        )

        # Assert
        assert bonuses == 5000.0


@pytest.mark.unit
@pytest.mark.asyncio
class TestServiceIntegration:
    """Test service integration scenarios"""

    async def test_complete_bonus_workflow(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_user_id: UUID,
        test_order_id: UUID
    ):
        """Test complete workflow: accrue, check, spend"""
        # Accrue bonuses
        mock_repository.add_bonuses.return_value = 100.0
        bonuses = await bonus_service.accrue_bonuses(
            user_id=test_user_id,
            order_id=test_order_id,
            payment_amount=10000.0,
            rate=0.01
        )
        assert bonuses == 100.0

        # Spend bonuses
        mock_repository.get_user_balance.return_value = 100.0
        mock_repository.spend_bonuses.return_value = 50.0
        spent, new_balance = await bonus_service.spend_bonuses(
            user_id=test_user_id,
            order_id=test_order_id,
            amount=50
        )
        assert spent == 50
        assert new_balance == 50.0

    async def test_multiple_operations_same_order(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_user_id: UUID,
        test_order_id: UUID
    ):
        """Test multiple operations for same order"""
        # Apply promocode
        mock_promo = Mock(spec=Promocode)
        mock_promo.code = "SUMMER24"
        mock_promo.discount_amount = 500.0
        mock_promo.active = True
        mock_repository.find_promocode.return_value = mock_promo

        status, discount = await bonus_service.apply_promocode(test_order_id, "SUMMER24")
        assert status == "applied"
        assert discount == 500.0

        # Spend bonuses for same order
        mock_repository.get_user_balance.return_value = 1000.0
        mock_repository.spend_bonuses.return_value = 800.0

        spent, new_balance = await bonus_service.spend_bonuses(
            user_id=test_user_id,
            order_id=test_order_id,
            amount=200
        )
        assert spent == 200
        assert new_balance == 800.0

    async def test_service_with_multiple_users(
        self,
        bonus_service: BonusService,
        mock_repository: AsyncMock,
        test_user_id: UUID,
        different_user_id: UUID,
        test_order_id: UUID
    ):
        """Test service operations for multiple users"""
        # User 1: accrue bonuses
        mock_repository.add_bonuses.return_value = 100.0
        bonuses1 = await bonus_service.accrue_bonuses(
            user_id=test_user_id,
            order_id=test_order_id,
            payment_amount=10000.0,
            rate=0.01
        )
        assert bonuses1 == 100.0

        # User 2: accrue bonuses
        mock_repository.add_bonuses.return_value = 200.0
        bonuses2 = await bonus_service.accrue_bonuses(
            user_id=different_user_id,
            order_id=test_order_id,
            payment_amount=20000.0,
            rate=0.01
        )
        assert bonuses2 == 200.0

        # Verify repository was called with correct user IDs
        assert mock_repository.add_bonuses.call_count == 2
