"""
Unit tests for LocalFineRepository
"""
import pytest
from datetime import date
from uuid import UUID, uuid4
from app.repositories.local_fine_repo import LocalFineRepository
from app.models.fine import Fine


class TestLocalFineRepositoryInitialization:
    """Test repository initialization"""

    def test_repository_initializes_with_test_data(self):
        """Test that repository is initialized with predefined test data"""
        repo = LocalFineRepository()

        # Check that test data exists
        assert len(repo._fines) > 0
        assert len(repo._fines_by_id) > 0

    def test_repository_has_test_license_plates(self):
        """Test that repository contains expected test license plates"""
        repo = LocalFineRepository()

        # Check for specific test plates
        assert "А123БВ799" in repo._fines
        assert "М456КЛ177" in repo._fines

    def test_repository_test_fines_are_unpaid(self):
        """Test that initial test fines are unpaid"""
        repo = LocalFineRepository()

        for fine_id, fine in repo._fines_by_id.items():
            assert fine.paid is False

    def test_repository_has_correct_test_amounts(self):
        """Test that test fines have expected amounts"""
        repo = LocalFineRepository()

        fine_799 = repo._fines["А123БВ799"][0]
        fine_177 = repo._fines["М456КЛ177"][0]

        assert fine_799.amount == 500.00
        assert fine_177.amount == 1000.00

    def test_repository_indexes_are_synchronized(self):
        """Test that both indexes contain the same fines"""
        repo = LocalFineRepository()

        # Count fines in plate index
        plate_index_count = sum(len(fines) for fines in repo._fines.values())

        # Count fines in ID index
        id_index_count = len(repo._fines_by_id)

        assert plate_index_count == id_index_count


class TestGetFinesByPlate:
    """Test get_fines_by_plate method"""

    def test_get_fines_for_existing_plate(self, real_repository):
        """Test retrieving fines for existing license plate"""
        fines = real_repository.get_fines_by_plate("А123БВ799")

        assert len(fines) > 0
        assert all(fine.license_plate == "А123БВ799" for fine in fines)

    def test_get_fines_for_nonexistent_plate(self, real_repository):
        """Test retrieving fines for non-existent license plate"""
        fines = real_repository.get_fines_by_plate("NONEXISTENT")

        assert fines == []
        assert isinstance(fines, list)

    def test_get_fines_returns_all_fines_for_plate(self, real_repository):
        """Test that all fines for a plate are returned"""
        # Add another fine for the same plate
        test_plate = "А123БВ799"
        new_fine = Fine(
            fine_id=uuid4(),
            license_plate=test_plate,
            amount=300.00,
            description="Парковка в неположенном месте",
            date=date(2024, 7, 1),
            paid=False
        )

        # Manually add to repository
        real_repository._fines[test_plate].append(new_fine)
        real_repository._fines_by_id[new_fine.fine_id] = new_fine

        fines = real_repository.get_fines_by_plate(test_plate)

        assert len(fines) >= 2

    def test_get_fines_preserves_fine_objects(self, real_repository):
        """Test that returned fines are proper Fine objects"""
        fines = real_repository.get_fines_by_plate("А123БВ799")

        for fine in fines:
            assert isinstance(fine, Fine)
            assert hasattr(fine, 'fine_id')
            assert hasattr(fine, 'amount')
            assert hasattr(fine, 'paid')


class TestGetUnpaidFinesByPlate:
    """Test get_unpaid_fines_by_plate method"""

    def test_get_unpaid_fines_for_existing_plate(self, real_repository):
        """Test retrieving unpaid fines for existing license plate"""
        unpaid = real_repository.get_unpaid_fines_by_plate("А123БВ799")

        assert len(unpaid) > 0
        assert all(not fine.paid for fine in unpaid)

    def test_get_unpaid_fines_excludes_paid_fines(self, real_repository):
        """Test that paid fines are excluded from results"""
        test_plate = "М456КЛ177"

        # Get a fine and mark it as paid
        all_fines = real_repository.get_fines_by_plate(test_plate)
        if all_fines:
            fine_to_pay = all_fines[0]
            real_repository.mark_fine_as_paid(fine_to_pay.fine_id)

        # Get unpaid fines
        unpaid = real_repository.get_unpaid_fines_by_plate(test_plate)

        # Should not include the paid fine
        if all_fines:
            assert fine_to_pay not in unpaid

    def test_get_unpaid_fines_for_nonexistent_plate(self, real_repository):
        """Test retrieving unpaid fines for non-existent plate"""
        unpaid = real_repository.get_unpaid_fines_by_plate("NONEXISTENT")

        assert unpaid == []

    def test_get_unpaid_fines_when_all_paid(self, real_repository):
        """Test retrieving unpaid fines when all fines are paid"""
        test_plate = "А123БВ799"

        # Mark all fines as paid
        all_fines = real_repository.get_fines_by_plate(test_plate)
        for fine in all_fines:
            real_repository.mark_fine_as_paid(fine.fine_id)

        # Get unpaid fines
        unpaid = real_repository.get_unpaid_fines_by_plate(test_plate)

        assert unpaid == []


class TestGetFineById:
    """Test get_fine_by_id method"""

    def test_get_fine_by_existing_id(self, real_repository):
        """Test retrieving a fine by existing ID"""
        # Get an existing fine ID
        all_fines = real_repository.get_fines_by_plate("А123БВ799")
        test_fine = all_fines[0]

        retrieved_fine = real_repository.get_fine_by_id(test_fine.fine_id)

        assert retrieved_fine is not None
        assert retrieved_fine.fine_id == test_fine.fine_id
        assert retrieved_fine.license_plate == test_fine.license_plate

    def test_get_fine_by_nonexistent_id(self, real_repository):
        """Test retrieving a fine by non-existent ID"""
        nonexistent_id = uuid4()

        retrieved_fine = real_repository.get_fine_by_id(nonexistent_id)

        assert retrieved_fine is None

    def test_get_fine_returns_correct_fine_object(self, real_repository):
        """Test that correct fine object is returned"""
        # Get an existing fine
        all_fines = real_repository.get_fines_by_plate("М456КЛ177")
        test_fine = all_fines[0]

        retrieved_fine = real_repository.get_fine_by_id(test_fine.fine_id)

        assert retrieved_fine.amount == test_fine.amount
        assert retrieved_fine.description == test_fine.description
        assert retrieved_fine.date == test_fine.date


class TestMarkFineAsPaid:
    """Test mark_fine_as_paid method"""

    def test_mark_existing_fine_as_paid(self, real_repository):
        """Test marking an existing unpaid fine as paid"""
        # Get an unpaid fine
        all_fines = real_repository.get_fines_by_plate("А123БВ799")
        test_fine = all_fines[0]

        assert test_fine.paid is False

        result = real_repository.mark_fine_as_paid(test_fine.fine_id)

        assert result is True
        assert test_fine.paid is True

    def test_mark_nonexistent_fine_as_paid(self, real_repository):
        """Test marking a non-existent fine as paid"""
        nonexistent_id = uuid4()

        result = real_repository.mark_fine_as_paid(nonexistent_id)

        assert result is False

    def test_mark_already_paid_fine_as_paid(self, real_repository):
        """Test marking an already paid fine as paid again"""
        # Get a fine and mark it as paid
        all_fines = real_repository.get_fines_by_plate("М456КЛ177")
        test_fine = all_fines[0]

        real_repository.mark_fine_as_paid(test_fine.fine_id)
        assert test_fine.paid is True

        # Mark it again
        result = real_repository.mark_fine_as_paid(test_fine.fine_id)

        assert result is True
        assert test_fine.paid is True

    def test_mark_as_paid_updates_both_indexes(self, real_repository):
        """Test that marking as paid updates fine in both indexes"""
        # Get a fine from one index
        all_fines = real_repository.get_fines_by_plate("А123БВ799")
        test_fine = all_fines[0]

        # Mark as paid
        real_repository.mark_fine_as_paid(test_fine.fine_id)

        # Verify in both indexes
        fine_by_plate = real_repository.get_fines_by_plate("А123БВ799")[0]
        fine_by_id = real_repository.get_fine_by_id(test_fine.fine_id)

        assert fine_by_plate.paid is True
        assert fine_by_id.paid is True


class TestIsFinesPaid:
    """Test is_fine_paid method"""

    def test_is_fine_paid_for_unpaid_fine(self, real_repository):
        """Test checking if unpaid fine is paid"""
        all_fines = real_repository.get_fines_by_plate("А123БВ799")
        test_fine = all_fines[0]

        result = real_repository.is_fine_paid(test_fine.fine_id)

        assert result is False

    def test_is_fine_paid_for_paid_fine(self, real_repository):
        """Test checking if paid fine is paid"""
        all_fines = real_repository.get_fines_by_plate("М456КЛ177")
        test_fine = all_fines[0]

        # Mark as paid
        real_repository.mark_fine_as_paid(test_fine.fine_id)

        result = real_repository.is_fine_paid(test_fine.fine_id)

        assert result is True

    def test_is_fine_paid_for_nonexistent_fine(self, real_repository):
        """Test checking if non-existent fine is paid"""
        nonexistent_id = uuid4()

        result = real_repository.is_fine_paid(nonexistent_id)

        assert result is None


class TestRepositoryEdgeCases:
    """Test edge cases and error scenarios"""

    def test_empty_license_plate_string(self, real_repository):
        """Test handling empty license plate string"""
        fines = real_repository.get_fines_by_plate("")

        assert fines == []

    def test_multiple_fines_same_plate(self):
        """Test handling multiple fines for the same plate"""
        repo = LocalFineRepository()

        # Add multiple fines for same plate
        test_plate = "TEST123"
        for i in range(3):
            fine = Fine(
                fine_id=uuid4(),
                license_plate=test_plate,
                amount=500.00 * (i + 1),
                description=f"Нарушение {i + 1}",
                date=date(2024, 5, i + 1),
                paid=False
            )
            if test_plate not in repo._fines:
                repo._fines[test_plate] = []
            repo._fines[test_plate].append(fine)
            repo._fines_by_id[fine.fine_id] = fine

        fines = repo.get_fines_by_plate(test_plate)

        assert len(fines) == 3

    def test_repository_isolation(self):
        """Test that multiple repository instances are independent"""
        repo1 = LocalFineRepository()
        repo2 = LocalFineRepository()

        # Modify repo1
        all_fines_1 = repo1.get_fines_by_plate("А123БВ799")
        if all_fines_1:
            repo1.mark_fine_as_paid(all_fines_1[0].fine_id)

        # Check repo2 is unaffected
        all_fines_2 = repo2.get_fines_by_plate("А123БВ799")
        if all_fines_2:
            assert all_fines_2[0].paid is False
