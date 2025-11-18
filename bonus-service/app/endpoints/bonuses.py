"""API endpoints for bonus operations"""
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
import logging
from app.models.bonus import (
    ApplyPromocodeRequest,
    PromocodeResponse,
    SpendBonusesRequest,
    SpendBonusesResponse
)
from app.services.bonus_service import BonusService
from app.repositories.local_bonus_repo import bonus_repository
from app.auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bonuses", tags=["bonuses"])

# Initialize service
bonus_service = BonusService(repository=bonus_repository)


@router.post("/promocodes/apply", response_model=PromocodeResponse, status_code=status.HTTP_200_OK)
async def apply_promocode(
    request: ApplyPromocodeRequest,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Apply promocode to order
    
    - **order_id**: Order identifier
    - **promocode**: Promocode string
    
    Returns promocode application result with discount amount
    """
    logger.info(f"POST /api/bonuses/promocodes/apply - order_id: {request.order_id}, promocode: {request.promocode}")
    
    try:
        status_str, discount_amount = await bonus_service.apply_promocode(
            order_id=request.order_id,
            promocode=request.promocode
        )
        
        return PromocodeResponse(
            order_id=request.order_id,
            promocode=request.promocode,
            status=status_str,
            discount_amount=discount_amount
        )
    
    except ValueError as e:
        logger.warning(f"Promocode application failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error applying promocode: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/spend", response_model=SpendBonusesResponse, status_code=status.HTTP_200_OK)
async def spend_bonuses(
    request: SpendBonusesRequest,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Spend bonuses from user account
    
    - **order_id**: Order identifier
    - **amount**: Amount of bonuses to spend
    
    Returns amount spent and new balance
    """
    logger.info(f"POST /api/bonuses/spend - order_id: {request.order_id}, amount: {request.amount}")
    
    try:
        bonuses_spent, new_balance = await bonus_service.spend_bonuses(
            user_id=user_id,
            order_id=request.order_id,
            amount=request.amount
        )
        
        return SpendBonusesResponse(
            order_id=request.order_id,
            bonuses_spent=bonuses_spent,
            new_balance=new_balance
        )
    
    except ValueError as e:
        logger.warning(f"Bonus spending failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error spending bonuses: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
