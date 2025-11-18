"""Repository для работы с платежами (in-memory storage)."""

from datetime import datetime
from typing import Dict, List, Optional


class PaymentRepository:
    """Репозиторий для управления платежами в памяти."""

    def __init__(self):
        """Инициализация хранилища."""
        self.payments_storage: List[Dict] = []

        # Заглушка для данных заказов (для проверки существования)
        self.orders_mock: Dict[str, Dict] = {
            "ord_a1b2c3d4": {
                "user_id": "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d",
                "amount": 4500.00
            },
            "ord_test123": {
                "user_id": "test-user-id-123",
                "amount": 2500.00
            }
        }

    def create_payment(self, payment_data: Dict) -> Dict:
        """
        Создать новый платеж.

        Args:
            payment_data: Данные платежа

        Returns:
            Созданный платеж
        """
        self.payments_storage.append(payment_data)
        return payment_data

    def get_payment_by_id(self, payment_id: str) -> Optional[Dict]:
        """
        Получить платеж по ID.

        Args:
            payment_id: Идентификатор платежа

        Returns:
            Данные платежа или None
        """
        for payment in self.payments_storage:
            if payment["payment_id"] == payment_id:
                return payment
        return None

    def update_payment_status(
        self,
        payment_id: str,
        new_status: str,
        paid_at: Optional[datetime] = None
    ) -> bool:
        """
        Обновить статус платежа.

        Args:
            payment_id: Идентификатор платежа
            new_status: Новый статус
            paid_at: Время оплаты (для succeeded статуса)

        Returns:
            True если успешно, False если платеж не найден
        """
        for payment in self.payments_storage:
            if payment["payment_id"] == payment_id:
                payment["status"] = new_status
                if paid_at:
                    payment["paid_at"] = paid_at
                return True
        return False

    def check_order_paid(self, order_id: str) -> bool:
        """
        Проверить, оплачен ли заказ.

        Args:
            order_id: Идентификатор заказа

        Returns:
            True если заказ уже оплачен
        """
        for payment in self.payments_storage:
            if payment["order_id"] == order_id and payment["status"] == "succeeded":
                return True
        return False

    def get_order_data(self, order_id: str) -> Optional[Dict]:
        """
        Получить данные заказа из заглушки.

        Args:
            order_id: Идентификатор заказа

        Returns:
            Данные заказа или None
        """
        return self.orders_mock.get(order_id)


# Singleton instance
payment_repository = PaymentRepository()
