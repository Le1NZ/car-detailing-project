"""RabbitMQ consumer for payment_succeeded events"""
import json
import logging
from uuid import UUID
import aio_pika
from aio_pika import IncomingMessage
from app.config import settings
from app.services.bonus_service import BonusService

logger = logging.getLogger(__name__)


class RabbitMQConsumer:
    """RabbitMQ consumer for payment success events"""
    
    def __init__(self, bonus_service: BonusService):
        self.bonus_service = bonus_service
        self.connection = None
        self.channel = None
    
    async def start(self):
        """Start consuming messages from RabbitMQ"""
        try:
            logger.info(f"Connecting to RabbitMQ at {settings.AMQP_URL}")
            self.connection = await aio_pika.connect_robust(settings.AMQP_URL)
            self.channel = await self.connection.channel()
            
            # Set QoS to process one message at a time
            await self.channel.set_qos(prefetch_count=1)
            
            # Declare queue (idempotent operation)
            queue = await self.channel.declare_queue(
                settings.PAYMENT_QUEUE,
                durable=True
            )
            
            logger.info(f"Successfully connected to RabbitMQ. Listening on queue: {settings.PAYMENT_QUEUE}")
            
            # Start consuming messages
            await queue.consume(self.on_message)
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}", exc_info=True)
            raise
    
    async def on_message(self, message: IncomingMessage):
        """
        Handle incoming payment_succeeded message
        
        Expected message format:
        {
            "order_id": "uuid",
            "user_id": "uuid",
            "amount": float
        }
        """
        async with message.process():
            try:
                # Parse message body
                body = json.loads(message.body.decode())
                logger.info(f"Received payment_succeeded message: {body}")
                
                # Extract data
                order_id = UUID(body["order_id"])
                user_id = UUID(body["user_id"])
                amount = float(body["amount"])
                
                # Accrue bonuses (1% of payment amount)
                bonuses = await self.bonus_service.accrue_bonuses(
                    user_id=user_id,
                    order_id=order_id,
                    payment_amount=amount,
                    rate=settings.BONUS_ACCRUAL_RATE
                )
                
                logger.info(f"Successfully accrued {bonuses} bonuses to user {user_id} for order {order_id}")
                
            except KeyError as e:
                logger.error(f"Missing required field in message: {e}", exc_info=True)
            except ValueError as e:
                logger.error(f"Invalid data format in message: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
    
    async def stop(self):
        """Stop consuming and close connections"""
        try:
            if self.channel:
                await self.channel.close()
            if self.connection:
                await self.connection.close()
            logger.info("RabbitMQ consumer stopped")
        except Exception as e:
            logger.error(f"Error stopping RabbitMQ consumer: {e}", exc_info=True)
