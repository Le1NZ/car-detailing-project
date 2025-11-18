"""RabbitMQ Publisher для публикации событий об успешных платежах."""

import json
import logging
from typing import Optional

import aio_pika
from aio_pika import Message

from app.config import settings

logger = logging.getLogger(__name__)


class RabbitMQPublisher:
    """Publisher для отправки событий в RabbitMQ."""

    def __init__(self):
        """Инициализация publisher."""
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue_name = "payment_succeeded_queue"

    async def connect(self) -> None:
        """
        Установить соединение с RabbitMQ и объявить очередь.
        """
        try:
            logger.info(f"Connecting to RabbitMQ at {settings.amqp_url}")
            self.connection = await aio_pika.connect_robust(settings.amqp_url)
            self.channel = await self.connection.channel()

            # Объявляем очередь как durable (переживет перезапуск RabbitMQ)
            await self.channel.declare_queue(self.queue_name, durable=True)

            logger.info(f"Successfully connected to RabbitMQ and declared queue '{self.queue_name}'")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def publish_payment_success(
        self,
        order_id: str,
        user_id: str,
        amount: float
    ) -> None:
        """
        Опубликовать событие об успешной оплате.

        Args:
            order_id: Идентификатор заказа
            user_id: Идентификатор пользователя
            amount: Сумма платежа
        """
        if not self.channel:
            logger.error("RabbitMQ channel is not initialized")
            raise RuntimeError("RabbitMQ channel is not initialized")

        # Формируем тело сообщения
        message_body = {
            "order_id": order_id,
            "user_id": user_id,
            "amount": amount
        }

        try:
            # Создаем сообщение с persistent delivery mode
            message = Message(
                body=json.dumps(message_body).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )

            # Публикуем в очередь через default exchange
            await self.channel.default_exchange.publish(
                message,
                routing_key=self.queue_name
            )

            logger.info(
                f"Published payment success event: order_id={order_id}, "
                f"user_id={user_id}, amount={amount}"
            )
        except Exception as e:
            logger.error(f"Failed to publish message to RabbitMQ: {e}")
            raise

    async def close(self) -> None:
        """Закрыть соединение с RabbitMQ."""
        if self.connection:
            try:
                await self.connection.close()
                logger.info("RabbitMQ connection closed")
            except Exception as e:
                logger.error(f"Error closing RabbitMQ connection: {e}")


# Singleton instance
rabbitmq_publisher = RabbitMQPublisher()
