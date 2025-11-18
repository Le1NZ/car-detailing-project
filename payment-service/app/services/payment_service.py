"""Сервис для обработки платежей."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional

from app.repositories import payment_repository
from app.services.rabbitmq_publisher import rabbitmq_publisher

logger = logging.getLogger(__name__)


class PaymentService:
    """Сервис для управления платежами."""

    def __init__(self):
        """Инициализация сервиса."""
        self.repository = payment_repository

    async def initiate_payment(self, order_id: str, payment_method: str, user_id: str, amount: float = 5000.0) -> Dict:
        """
        Инициировать платеж и запустить фоновую обработку.

        Args:
            order_id: Идентификатор заказа
            payment_method: Метод оплаты
            user_id: Идентификатор пользователя (из JWT токена)
            amount: Сумма платежа (опционально, по умолчанию 5000.0)

        Returns:
            Данные созданного платежа

        Raises:
            ValueError: Если заказ уже оплачен
        """
        # Проверяем, не оплачен ли уже заказ
        if self.repository.check_order_paid(order_id):
            raise ValueError(f"Order {order_id} already paid")

        # Генерируем уникальный ID платежа
        payment_id = f"pay_{uuid.uuid4().hex[:8]}"

        # Создаем платеж со статусом pending
        payment_data = {
            "payment_id": payment_id,
            "order_id": order_id,
            "status": "pending",
            "amount": amount,
            "currency": "RUB",
            "confirmation_url": f"https://payment.gateway/confirm?token={payment_id}",
            "payment_method": payment_method,
            "created_at": datetime.utcnow(),
            "paid_at": None,
            "user_id": user_id
        }

        # Сохраняем платеж в репозитории
        created_payment = self.repository.create_payment(payment_data)

        logger.info(f"Payment {payment_id} created for order {order_id} with status 'pending'")

        # Запускаем фоновую задачу для обработки платежа
        asyncio.create_task(
            self._process_payment_async(
                payment_id=payment_id,
                order_id=order_id,
                user_id=user_id,
                amount=amount
            )
        )

        return created_payment

    async def _process_payment_async(
        self,
        payment_id: str,
        order_id: str,
        user_id: str,
        amount: float
    ) -> None:
        """
        Фоновая задача для обработки платежа.

        Симулирует обработку платежа (5 секунд), затем:
        1. Обновляет статус платежа на "succeeded"
        2. Публикует событие в RabbitMQ

        Args:
            payment_id: Идентификатор платежа
            order_id: Идентификатор заказа
            user_id: Идентификатор пользователя
            amount: Сумма платежа
        """
        try:
            logger.info(f"Starting async payment processing for payment_id={payment_id}")

            # Симуляция обработки платежа (проверка карты, связь с банком и т.д.)
            await asyncio.sleep(5)

            # Обновляем статус платежа на "succeeded"
            paid_at = datetime.utcnow()
            success = self.repository.update_payment_status(
                payment_id=payment_id,
                new_status="succeeded",
                paid_at=paid_at
            )

            if not success:
                logger.error(f"Failed to update payment status for payment_id={payment_id}")
                return

            logger.info(f"Payment {payment_id} status updated to 'succeeded'")

            # Публикуем событие в RabbitMQ
            await rabbitmq_publisher.publish_payment_success(
                order_id=order_id,
                user_id=user_id,
                amount=amount
            )

            logger.info(f"Payment success event published for payment_id={payment_id}")

        except Exception as e:
            logger.error(f"Error processing payment {payment_id}: {e}")
            # В реальном приложении здесь можно установить статус "failed"
            try:
                self.repository.update_payment_status(
                    payment_id=payment_id,
                    new_status="failed"
                )
            except Exception as update_error:
                logger.error(f"Failed to update payment status to failed: {update_error}")

    def get_payment(self, payment_id: str) -> Optional[Dict]:
        """
        Получить данные платежа по ID.

        Args:
            payment_id: Идентификатор платежа

        Returns:
            Данные платежа или None
        """
        return self.repository.get_payment_by_id(payment_id)


# Singleton instance
payment_service = PaymentService()
