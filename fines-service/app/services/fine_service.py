"""
Business logic for fines management
"""
from uuid import UUID, uuid4
from typing import List
from app.models.fine import FineResponse, PaymentResponse
from app.repositories.local_fine_repo import LocalFineRepository


class FineService:
    """Service layer for fines business logic"""
    
    def __init__(self, repository: LocalFineRepository):
        self.repository = repository
    
    def check_fines(self, license_plate: str) -> List[FineResponse]:
        """
        Check unpaid fines for a license plate
        
        Args:
            license_plate: Vehicle license plate number
            
        Returns:
            List of unpaid fines
        """
        unpaid_fines = self.repository.get_unpaid_fines_by_plate(license_plate)
        
        return [
            FineResponse(
                fine_id=fine.fine_id,
                amount=fine.amount,
                description=fine.description,
                date=fine.date
            )
            for fine in unpaid_fines
        ]
    
    def pay_fine(self, fine_id: UUID, payment_method_id: str) -> PaymentResponse:
        """
        Process fine payment
        
        Args:
            fine_id: ID of the fine to pay
            payment_method_id: Payment method identifier
            
        Returns:
            Payment confirmation response
            
        Raises:
            ValueError: If fine not found
            RuntimeError: If fine already paid
        """
        # Check if fine exists
        fine = self.repository.get_fine_by_id(fine_id)
        if not fine:
            raise ValueError(f"Fine with ID {fine_id} not found")
        
        # Check if already paid
        if fine.paid:
            raise RuntimeError(f"Fine with ID {fine_id} is already paid")
        
        # Mark as paid
        self.repository.mark_fine_as_paid(fine_id)
        
        # Generate payment confirmation
        payment_id = uuid4()
        
        return PaymentResponse(
            payment_id=payment_id,
            fine_id=fine_id,
            status="paid"
        )
