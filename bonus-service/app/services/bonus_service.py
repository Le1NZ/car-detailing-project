"""Business logic for bonus operations"""
from uuid import UUID
from typing import Tuple
import logging
from app.repositories.local_bonus_repo import LocalBonusRepository

logger = logging.getLogger(__name__)


class BonusService:
    """Service layer for bonus operations"""
    
    def __init__(self, repository: LocalBonusRepository):
        self.repository = repository
    
    async def apply_promocode(self, order_id: UUID, promocode: str) -> Tuple[str, float]:
        """
        Apply promocode to order
        
        Args:
            order_id: Order identifier
            promocode: Promocode string
            
        Returns:
            Tuple of (status, discount_amount)
            
        Raises:
            ValueError: If promocode is invalid
        """
        logger.info(f"Attempting to apply promocode '{promocode}' to order {order_id}")
        
        promo = await self.repository.find_promocode(promocode)
        
        if promo is None:
            logger.warning(f"Invalid promocode '{promocode}' for order {order_id}")
            raise ValueError(f"Promocode '{promocode}' is invalid or inactive")
        
        logger.info(f"Successfully applied promocode '{promocode}' to order {order_id}. Discount: {promo.discount_amount}")
        return "applied", promo.discount_amount
    
    async def spend_bonuses(self, user_id: UUID, order_id: UUID, amount: int) -> Tuple[int, float]:
        """
        Spend bonuses from user account
        
        Args:
            user_id: User identifier
            order_id: Order identifier
            amount: Amount of bonuses to spend
            
        Returns:
            Tuple of (bonuses_spent, new_balance)
            
        Raises:
            ValueError: If insufficient bonuses
        """
        logger.info(f"User {user_id} attempting to spend {amount} bonuses for order {order_id}")
        
        # Check if user has sufficient bonuses
        current_balance = await self.repository.get_user_balance(user_id)
        
        if current_balance < amount:
            logger.warning(f"Insufficient bonuses for user {user_id}. Balance: {current_balance}, requested: {amount}")
            raise ValueError(f"Insufficient bonuses. Available: {current_balance}, requested: {amount}")
        
        # Spend bonuses
        new_balance = await self.repository.spend_bonuses(user_id, amount)
        
        logger.info(f"Successfully spent {amount} bonuses for user {user_id}. New balance: {new_balance}")
        return amount, new_balance
    
    async def accrue_bonuses(self, user_id: UUID, order_id: UUID, payment_amount: float, rate: float) -> float:
        """
        Accrue bonuses to user account based on payment amount
        
        Args:
            user_id: User identifier
            order_id: Order identifier
            payment_amount: Payment amount
            rate: Bonus accrual rate (e.g., 0.01 for 1%)
            
        Returns:
            Amount of bonuses accrued
        """
        bonuses = payment_amount * rate
        await self.repository.add_bonuses(user_id, bonuses)
        logger.info(f"Accrued {bonuses} bonuses to user {user_id} for order {order_id}")
        return bonuses
