"""In-memory repository for bonus and promocode data"""
from uuid import UUID
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class Promocode:
    """Promocode data structure"""
    def __init__(self, code: str, discount_amount: float, active: bool = True):
        self.code = code
        self.discount_amount = discount_amount
        self.active = active


class LocalBonusRepository:
    """In-memory storage for bonuses and promocodes"""
    
    def __init__(self):
        """Initialize repository with empty balances and predefined promocodes"""
        self.user_balances: Dict[UUID, float] = {}
        self.promocodes: List[Promocode] = self._initialize_promocodes()
        logger.info(f"Initialized LocalBonusRepository with {len(self.promocodes)} promocodes")
    
    def _initialize_promocodes(self) -> List[Promocode]:
        """Initialize predefined promocodes"""
        return [
            Promocode(code="SUMMER24", discount_amount=500.00, active=True),
            Promocode(code="WELCOME10", discount_amount=1000.00, active=True),
        ]
    
    async def get_user_balance(self, user_id: UUID) -> float:
        """Get user bonus balance"""
        balance = self.user_balances.get(user_id, 0.0)
        logger.debug(f"Retrieved balance for user {user_id}: {balance}")
        return balance
    
    async def add_bonuses(self, user_id: UUID, amount: float) -> float:
        """Add bonuses to user balance"""
        current_balance = self.user_balances.get(user_id, 0.0)
        new_balance = current_balance + amount
        self.user_balances[user_id] = new_balance
        logger.info(f"Added {amount} bonuses to user {user_id}. New balance: {new_balance}")
        return new_balance
    
    async def spend_bonuses(self, user_id: UUID, amount: int) -> float:
        """Spend bonuses from user balance"""
        current_balance = self.user_balances.get(user_id, 0.0)
        
        if current_balance < amount:
            logger.warning(f"Insufficient bonuses for user {user_id}. Current: {current_balance}, requested: {amount}")
            raise ValueError(f"Insufficient bonuses. Current balance: {current_balance}, requested: {amount}")
        
        new_balance = current_balance - amount
        self.user_balances[user_id] = new_balance
        logger.info(f"Spent {amount} bonuses for user {user_id}. New balance: {new_balance}")
        return new_balance
    
    async def find_promocode(self, code: str) -> Optional[Promocode]:
        """Find promocode by code"""
        for promo in self.promocodes:
            if promo.code == code and promo.active:
                logger.debug(f"Found active promocode: {code}")
                return promo
        logger.warning(f"Promocode not found or inactive: {code}")
        return None


# Global repository instance
bonus_repository = LocalBonusRepository()
