"""
Unit tests for FineService business logic
"""
import pytest
from uuid import UUID, uuid4
from datetime import date
from unittest.mock import Mock
from app.services.fine_service import FineService
from app.models.fine import Fine, FineResponse, PaymentResponse


class TestFineServiceCheckFines:
    """Test check_fines method"""

    def test_check_fines_returns_unpaid_fines(self, mock_repository, sample_fine):
        """Test that check_fines returns unpaid fines for a license plate"""
        # Arrange
        mock_repository.get_unpaid_fines_by_plate.return_value = [sample_fine]
        service = FineService(mock_repository)

        # Act
        result = service.check_fines("А123БВ799")

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], FineResponse)
        assert result[0].fine_id == sample_fine.fine_id
        assert result[0].amount == sample_fine.amount
        mock_repository.get_unpaid_fines_by_plate.assert_called_once_with("А123БВ799")

    def test_check_fines_returns_empty_list_for_no_fines(self, mock_repository):
        """Test that check_fines returns empty list when no fines exist"""
        # Arrange
        mock_repository.get_unpaid_fines_by_plate.return_value = []
        service = FineService(mock_repository)

        # Act
        result = service.check_fines("NONEXISTENT")

        # Assert
        assert result == []
        assert isinstance(result, list)
        mock_repository.get_unpaid_fines_by_plate.assert_called_once_with("NONEXISTENT")

    def test_check_fines_returns_multiple_fines(self, mock_repository):
        """Test that check_fines returns multiple fines correctly"""
        # Arrange
        fine1 = Fine(
            fine_id=uuid4(),
            license_plate="TEST123",
            amount=500.00,
            description="Нарушение 1",
            date=date(2024, 5, 15),
            paid=False
        )
        fine2 = Fine(
            fine_id=uuid4(),
            license_plate="TEST123",
            amount=1000.00,
            description="Нарушение 2",
            date=date(2024, 6, 1),
            paid=False
        )
        mock_repository.get_unpaid_fines_by_plate.return_value = [fine1, fine2]
        service = FineService(mock_repository)

        # Act
        result = service.check_fines("TEST123")

        # Assert
        assert len(result) == 2
        assert result[0].fine_id == fine1.fine_id
        assert result[1].fine_id == fine2.fine_id

    def test_check_fines_excludes_paid_status_in_response(self, mock_repository, sample_fine):
        """Test that FineResponse does not include paid status"""
        # Arrange
        mock_repository.get_unpaid_fines_by_plate.return_value = [sample_fine]
        service = FineService(mock_repository)

        # Act
        result = service.check_fines("А123БВ799")

        # Assert
        response = result[0]
        assert not hasattr(response, 'paid')
        assert hasattr(response, 'fine_id')
        assert hasattr(response, 'amount')
        assert hasattr(response, 'description')
        assert hasattr(response, 'date')

    def test_check_fines_converts_fine_to_fine_response(self, mock_repository, sample_fine):
        """Test that Fine objects are properly converted to FineResponse"""
        # Arrange
        mock_repository.get_unpaid_fines_by_plate.return_value = [sample_fine]
        service = FineService(mock_repository)

        # Act
        result = service.check_fines("А123БВ799")

        # Assert
        response = result[0]
        assert isinstance(response, FineResponse)
        assert response.fine_id == sample_fine.fine_id
        assert response.amount == sample_fine.amount
        assert response.description == sample_fine.description
        assert response.date == sample_fine.date


class TestFineServicePayFine:
    """Test pay_fine method"""

    def test_pay_fine_success(self, mock_repository, sample_fine):
        """Test successful fine payment"""
        # Arrange
        mock_repository.get_fine_by_id.return_value = sample_fine
        mock_repository.mark_fine_as_paid.return_value = True
        service = FineService(mock_repository)

        # Act
        result = service.pay_fine(sample_fine.fine_id, "card_123")

        # Assert
        assert isinstance(result, PaymentResponse)
        assert result.fine_id == sample_fine.fine_id
        assert result.status == "paid"
        assert isinstance(result.payment_id, UUID)
        mock_repository.get_fine_by_id.assert_called_once_with(sample_fine.fine_id)
        mock_repository.mark_fine_as_paid.assert_called_once_with(sample_fine.fine_id)

    def test_pay_fine_raises_value_error_when_fine_not_found(self, mock_repository):
        """Test that ValueError is raised when fine doesn't exist"""
        # Arrange
        mock_repository.get_fine_by_id.return_value = None
        service = FineService(mock_repository)
        nonexistent_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.pay_fine(nonexistent_id, "card_123")

        assert f"Fine with ID {nonexistent_id} not found" in str(exc_info.value)
        mock_repository.get_fine_by_id.assert_called_once_with(nonexistent_id)
        mock_repository.mark_fine_as_paid.assert_not_called()

    def test_pay_fine_raises_runtime_error_when_already_paid(self, mock_repository, sample_paid_fine):
        """Test that RuntimeError is raised when fine is already paid"""
        # Arrange
        mock_repository.get_fine_by_id.return_value = sample_paid_fine
        service = FineService(mock_repository)

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            service.pay_fine(sample_paid_fine.fine_id, "card_123")

        assert f"Fine with ID {sample_paid_fine.fine_id} is already paid" in str(exc_info.value)
        mock_repository.get_fine_by_id.assert_called_once_with(sample_paid_fine.fine_id)
        mock_repository.mark_fine_as_paid.assert_not_called()

    def test_pay_fine_generates_unique_payment_id(self, mock_repository, sample_fine):
        """Test that unique payment IDs are generated"""
        # Arrange
        mock_repository.get_fine_by_id.return_value = sample_fine
        mock_repository.mark_fine_as_paid.return_value = True
        service = FineService(mock_repository)

        # Act
        result1 = service.pay_fine(sample_fine.fine_id, "card_123")

        # Reset mock to simulate different fine
        mock_repository.reset_mock()
        sample_fine.paid = False  # Reset paid status for test
        mock_repository.get_fine_by_id.return_value = sample_fine
        mock_repository.mark_fine_as_paid.return_value = True

        result2 = service.pay_fine(sample_fine.fine_id, "card_123")

        # Assert
        assert result1.payment_id != result2.payment_id

    def test_pay_fine_accepts_various_payment_methods(self, mock_repository, sample_fine):
        """Test that various payment method IDs are accepted"""
        # Arrange
        mock_repository.get_fine_by_id.return_value = sample_fine
        mock_repository.mark_fine_as_paid.return_value = True
        service = FineService(mock_repository)

        payment_methods = [
            "card_123",
            "bank_account_456",
            "wallet_789",
            "cash"
        ]

        # Act & Assert
        for payment_method in payment_methods:
            sample_fine.paid = False  # Reset for each iteration
            result = service.pay_fine(sample_fine.fine_id, payment_method)
            assert result.status == "paid"

    def test_pay_fine_calls_repository_methods_in_order(self, mock_repository, sample_fine):
        """Test that repository methods are called in correct order"""
        # Arrange
        mock_repository.get_fine_by_id.return_value = sample_fine
        mock_repository.mark_fine_as_paid.return_value = True
        service = FineService(mock_repository)

        # Act
        service.pay_fine(sample_fine.fine_id, "card_123")

        # Assert
        assert mock_repository.get_fine_by_id.call_count == 1
        assert mock_repository.mark_fine_as_paid.call_count == 1


class TestFineServiceWithRealRepository:
    """Test FineService with real repository for integration validation"""

    def test_check_fines_with_real_repository(self, real_fine_service):
        """Test check_fines with actual repository"""
        # Act
        result = real_fine_service.check_fines("А123БВ799")

        # Assert
        assert len(result) > 0
        assert isinstance(result[0], FineResponse)
        assert result[0].amount == 500.00

    def test_pay_fine_with_real_repository(self, real_fine_service):
        """Test pay_fine with actual repository"""
        # Arrange - get a real fine ID
        fines = real_fine_service.check_fines("А123БВ799")
        fine_id = fines[0].fine_id

        # Act
        result = real_fine_service.pay_fine(fine_id, "card_123")

        # Assert
        assert isinstance(result, PaymentResponse)
        assert result.fine_id == fine_id
        assert result.status == "paid"

        # Verify fine is now marked as paid
        unpaid_fines = real_fine_service.check_fines("А123БВ799")
        assert fine_id not in [f.fine_id for f in unpaid_fines]

    def test_pay_same_fine_twice_raises_error(self, real_fine_service):
        """Test that paying the same fine twice raises RuntimeError"""
        # Arrange - get a real fine ID and pay it
        fines = real_fine_service.check_fines("М456КЛ177")
        fine_id = fines[0].fine_id
        real_fine_service.pay_fine(fine_id, "card_123")

        # Act & Assert - try to pay again
        with pytest.raises(RuntimeError) as exc_info:
            real_fine_service.pay_fine(fine_id, "card_123")

        assert "already paid" in str(exc_info.value)


class TestFineServiceEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_check_fines_with_empty_string_license_plate(self, mock_repository):
        """Test checking fines with empty license plate"""
        # Arrange
        mock_repository.get_unpaid_fines_by_plate.return_value = []
        service = FineService(mock_repository)

        # Act
        result = service.check_fines("")

        # Assert
        assert result == []
        mock_repository.get_unpaid_fines_by_plate.assert_called_once_with("")

    def test_check_fines_with_special_characters(self, mock_repository):
        """Test checking fines with special characters in license plate"""
        # Arrange
        special_plate = "А-123/БВ*799"
        mock_repository.get_unpaid_fines_by_plate.return_value = []
        service = FineService(mock_repository)

        # Act
        result = service.check_fines(special_plate)

        # Assert
        assert result == []
        mock_repository.get_unpaid_fines_by_plate.assert_called_once_with(special_plate)

    def test_pay_fine_with_empty_payment_method_id(self, mock_repository, sample_fine):
        """Test paying fine with empty payment method ID"""
        # Arrange
        mock_repository.get_fine_by_id.return_value = sample_fine
        mock_repository.mark_fine_as_paid.return_value = True
        service = FineService(mock_repository)

        # Act - should still work as payment_method_id is just a string
        result = service.pay_fine(sample_fine.fine_id, "")

        # Assert
        assert result.status == "paid"

    def test_service_with_none_repository_raises_error(self):
        """Test that service requires a repository"""
        # This will raise AttributeError when methods are called
        service = FineService(None)

        with pytest.raises(AttributeError):
            service.check_fines("TEST123")

    def test_check_fines_preserves_fine_order(self, mock_repository):
        """Test that order of fines is preserved"""
        # Arrange
        fines = [
            Fine(
                fine_id=uuid4(),
                license_plate="TEST",
                amount=100.00,
                description="First",
                date=date(2024, 1, 1),
                paid=False
            ),
            Fine(
                fine_id=uuid4(),
                license_plate="TEST",
                amount=200.00,
                description="Second",
                date=date(2024, 2, 1),
                paid=False
            ),
            Fine(
                fine_id=uuid4(),
                license_plate="TEST",
                amount=300.00,
                description="Third",
                date=date(2024, 3, 1),
                paid=False
            )
        ]
        mock_repository.get_unpaid_fines_by_plate.return_value = fines
        service = FineService(mock_repository)

        # Act
        result = service.check_fines("TEST")

        # Assert
        assert len(result) == 3
        assert result[0].description == "First"
        assert result[1].description == "Second"
        assert result[2].description == "Third"


class TestFineServiceErrorMessages:
    """Test error message formatting"""

    def test_fine_not_found_error_includes_id(self, mock_repository):
        """Test that fine not found error includes the fine ID"""
        # Arrange
        mock_repository.get_fine_by_id.return_value = None
        service = FineService(mock_repository)
        test_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.pay_fine(test_id, "card_123")

        error_message = str(exc_info.value)
        assert str(test_id) in error_message
        assert "not found" in error_message.lower()

    def test_already_paid_error_includes_id(self, mock_repository):
        """Test that already paid error includes the fine ID"""
        # Arrange
        paid_fine = Fine(
            fine_id=uuid4(),
            license_plate="TEST",
            amount=500.00,
            description="Test",
            date=date(2024, 5, 15),
            paid=True
        )
        mock_repository.get_fine_by_id.return_value = paid_fine
        service = FineService(mock_repository)

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            service.pay_fine(paid_fine.fine_id, "card_123")

        error_message = str(exc_info.value)
        assert str(paid_fine.fine_id) in error_message
        assert "already paid" in error_message.lower()
