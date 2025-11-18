"""
API endpoints for fines management
"""
from uuid import UUID
from typing import List
from fastapi import APIRouter, HTTPException, Query, Depends
from app.models.fine import FineResponse, PayFineRequest, PaymentResponse
from app.services.fine_service import FineService
from app.repositories.local_fine_repo import fine_repository
from app.auth import get_current_user_id


router = APIRouter(prefix="/api/fines", tags=["fines"])

# Initialize service with repository
fine_service = FineService(fine_repository)


@router.get("/check", response_model=List[FineResponse])
async def check_fines(
    license_plate: str = Query(..., description="Vehicle license plate number"),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Check unpaid fines for a license plate
    
    Args:
        license_plate: Vehicle license plate number
        
    Returns:
        List of unpaid fines (empty list if no fines found)
    """
    fines = fine_service.check_fines(license_plate)
    return fines


@router.post("/{fine_id}/pay", response_model=PaymentResponse)
async def pay_fine(
    fine_id: UUID,
    request: PayFineRequest,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Pay a fine
    
    Args:
        fine_id: ID of the fine to pay
        request: Payment request with payment method ID
        
    Returns:
        Payment confirmation
        
    Raises:
        404: Fine not found
        409: Fine already paid
    """
    try:
        payment = fine_service.pay_fine(fine_id, request.payment_method_id)
        return payment
    except ValueError as e:
        # Fine not found
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        # Fine already paid
        raise HTTPException(status_code=409, detail=str(e))
