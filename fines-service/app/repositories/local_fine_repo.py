"""
In-memory repository for fines
"""
from datetime import date
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from app.models.fine import Fine


class LocalFineRepository:
    """In-memory repository for storing fines"""
    
    def __init__(self):
        """Initialize repository with test data"""
        self._fines: Dict[str, List[Fine]] = {}
        self._fines_by_id: Dict[UUID, Fine] = {}
        self._initialize_test_data()
    
    def _initialize_test_data(self):
        """Preload test fines"""
        # Clear existing data first
        self._fines = {}
        self._fines_by_id = {}

        test_fines = [
            {
                "license_plate": "А123БВ799",
                "amount": 500.00,
                "description": "Превышение скорости на 20-40 км/ч",
                "date": date(2024, 5, 15)
            },
            {
                "license_plate": "М456КЛ177",
                "amount": 1000.00,
                "description": "Проезд на красный свет",
                "date": date(2024, 6, 1)
            }
        ]

        for fine_data in test_fines:
            fine = Fine(
                fine_id=uuid4(),
                license_plate=fine_data["license_plate"],
                amount=fine_data["amount"],
                description=fine_data["description"],
                date=fine_data["date"],
                paid=False
            )

            # Add to plate index
            if fine.license_plate not in self._fines:
                self._fines[fine.license_plate] = []
            self._fines[fine.license_plate].append(fine)

            # Add to ID index
            self._fines_by_id[fine.fine_id] = fine
    
    def get_fines_by_plate(self, license_plate: str) -> List[Fine]:
        """Get all fines for a license plate"""
        return self._fines.get(license_plate, [])
    
    def get_unpaid_fines_by_plate(self, license_plate: str) -> List[Fine]:
        """Get unpaid fines for a license plate"""
        all_fines = self.get_fines_by_plate(license_plate)
        return [fine for fine in all_fines if not fine.paid]
    
    def get_fine_by_id(self, fine_id: UUID) -> Optional[Fine]:
        """Get a fine by its ID"""
        return self._fines_by_id.get(fine_id)
    
    def mark_fine_as_paid(self, fine_id: UUID) -> bool:
        """Mark a fine as paid"""
        fine = self.get_fine_by_id(fine_id)
        if fine:
            fine.paid = True
            return True
        return False
    
    def is_fine_paid(self, fine_id: UUID) -> Optional[bool]:
        """Check if a fine is paid. Returns None if fine not found."""
        fine = self.get_fine_by_id(fine_id)
        if fine:
            return fine.paid
        return None


# Global repository instance
fine_repository = LocalFineRepository()
