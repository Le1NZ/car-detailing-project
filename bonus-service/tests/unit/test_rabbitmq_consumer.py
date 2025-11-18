"""Unit tests for RabbitMQ consumer"""
import pytest
import json
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from uuid import UUID
from contextlib import asynccontextmanager

from app.services.rabbitmq_consumer import RabbitMQConsumer
from app.services.bonus_service import BonusService
from app.config import settings


@pytest.mark.unit
class TestRabbitMQConsumerInitialization:
    """Test RabbitMQ consumer initialization"""

    def test_consumer_initialization(self, mock_bonus_service: AsyncMock):
        """Test consumer initializes with bonus service"""
        # Act
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)

        # Assert
        assert consumer.bonus_service == mock_bonus_service
        assert consumer.connection is None
        assert consumer.channel is None

    def test_consumer_requires_bonus_service(self):
        """Test consumer requires bonus service parameter"""
        # This test verifies the constructor signature
        with pytest.raises(TypeError):
            RabbitMQConsumer()


@pytest.mark.unit
@pytest.mark.asyncio
class TestConsumerStart:
    """Test consumer start method"""

    @patch('app.services.rabbitmq_consumer.aio_pika.connect_robust')
    async def test_start_connects_to_rabbitmq(
        self,
        mock_connect: AsyncMock,
        mock_bonus_service: AsyncMock,
        mock_rabbitmq_connection: AsyncMock
    ):
        """Test start method connects to RabbitMQ successfully"""
        # Arrange
        mock_connect.return_value = mock_rabbitmq_connection
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)

        # Act
        await consumer.start()

        # Assert
        mock_connect.assert_called_once_with(settings.AMQP_URL)
        assert consumer.connection == mock_rabbitmq_connection

    @patch('app.services.rabbitmq_consumer.aio_pika.connect_robust')
    async def test_start_creates_channel(
        self,
        mock_connect: AsyncMock,
        mock_bonus_service: AsyncMock,
        mock_rabbitmq_connection: AsyncMock
    ):
        """Test start method creates channel"""
        # Arrange
        mock_connect.return_value = mock_rabbitmq_connection
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)

        # Act
        await consumer.start()

        # Assert
        mock_rabbitmq_connection.channel.assert_called_once()
        assert consumer.channel is not None

    @patch('app.services.rabbitmq_consumer.aio_pika.connect_robust')
    async def test_start_sets_qos(
        self,
        mock_connect: AsyncMock,
        mock_bonus_service: AsyncMock,
        mock_rabbitmq_connection: AsyncMock
    ):
        """Test start method sets QoS to process one message at a time"""
        # Arrange
        mock_connect.return_value = mock_rabbitmq_connection
        mock_channel = await mock_rabbitmq_connection.channel()
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)

        # Act
        await consumer.start()

        # Assert
        mock_channel.set_qos.assert_called_once_with(prefetch_count=1)

    @patch('app.services.rabbitmq_consumer.aio_pika.connect_robust')
    async def test_start_declares_queue(
        self,
        mock_connect: AsyncMock,
        mock_bonus_service: AsyncMock,
        mock_rabbitmq_connection: AsyncMock
    ):
        """Test start method declares queue"""
        # Arrange
        mock_connect.return_value = mock_rabbitmq_connection
        mock_channel = await mock_rabbitmq_connection.channel()
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)

        # Act
        await consumer.start()

        # Assert
        mock_channel.declare_queue.assert_called_once_with(
            settings.PAYMENT_QUEUE,
            durable=True
        )

    @patch('app.services.rabbitmq_consumer.aio_pika.connect_robust')
    async def test_start_begins_consuming(
        self,
        mock_connect: AsyncMock,
        mock_bonus_service: AsyncMock,
        mock_rabbitmq_connection: AsyncMock
    ):
        """Test start method begins consuming messages"""
        # Arrange
        mock_connect.return_value = mock_rabbitmq_connection
        mock_channel = await mock_rabbitmq_connection.channel()
        mock_queue = await mock_channel.declare_queue(settings.PAYMENT_QUEUE, durable=True)
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)

        # Act
        await consumer.start()

        # Assert
        mock_queue.consume.assert_called_once()

    @patch('app.services.rabbitmq_consumer.aio_pika.connect_robust')
    async def test_start_connection_error_raises_exception(
        self,
        mock_connect: AsyncMock,
        mock_bonus_service: AsyncMock
    ):
        """Test start method raises exception on connection error"""
        # Arrange
        mock_connect.side_effect = ConnectionError("Failed to connect to RabbitMQ")
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)

        # Act & Assert
        with pytest.raises(ConnectionError):
            await consumer.start()


@pytest.mark.unit
@pytest.mark.asyncio
class TestOnMessage:
    """Test on_message handler"""

    async def test_on_message_valid_payload_success(self, mock_bonus_service: AsyncMock):
        """Test processing valid payment_succeeded message"""
        # Arrange
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)

        message_data = {
            "order_id": "123e4567-e89b-12d3-a456-426614174000",
            "user_id": "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d",
            "amount": 10000.0
        }

        mock_message = Mock()
        mock_message.body = json.dumps(message_data).encode()

        # Create async context manager mock
        @asynccontextmanager
        async def mock_process():
            yield

        mock_message.process = mock_process
        mock_bonus_service.accrue_bonuses.return_value = 100.0

        # Act
        await consumer.on_message(mock_message)

        # Assert
        mock_bonus_service.accrue_bonuses.assert_called_once_with(
            user_id=UUID("c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d"),
            order_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            payment_amount=10000.0,
            rate=settings.BONUS_ACCRUAL_RATE
        )

    async def test_on_message_calculates_correct_bonuses(self, mock_bonus_service: AsyncMock):
        """Test message processing uses correct bonus rate"""
        # Arrange
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)

        message_data = {
            "order_id": "123e4567-e89b-12d3-a456-426614174000",
            "user_id": "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d",
            "amount": 5000.0
        }

        mock_message = Mock()
        mock_message.body = json.dumps(message_data).encode()

        @asynccontextmanager
        async def mock_process():
            yield

        mock_message.process = mock_process
        mock_bonus_service.accrue_bonuses.return_value = 50.0

        # Act
        await consumer.on_message(mock_message)

        # Assert
        mock_bonus_service.accrue_bonuses.assert_called_once()
        call_kwargs = mock_bonus_service.accrue_bonuses.call_args.kwargs
        assert call_kwargs["payment_amount"] == 5000.0
        assert call_kwargs["rate"] == settings.BONUS_ACCRUAL_RATE

    async def test_on_message_missing_order_id_logs_error(self, mock_bonus_service: AsyncMock):
        """Test handling message with missing order_id"""
        # Arrange
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)

        message_data = {
            "user_id": "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d",
            "amount": 10000.0
        }

        mock_message = Mock()
        mock_message.body = json.dumps(message_data).encode()

        @asynccontextmanager
        async def mock_process():
            yield

        mock_message.process = mock_process

        # Act - should not raise exception
        await consumer.on_message(mock_message)

        # Assert - service should not be called
        mock_bonus_service.accrue_bonuses.assert_not_called()

    async def test_on_message_missing_user_id_logs_error(self, mock_bonus_service: AsyncMock):
        """Test handling message with missing user_id"""
        # Arrange
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)

        message_data = {
            "order_id": "123e4567-e89b-12d3-a456-426614174000",
            "amount": 10000.0
        }

        mock_message = Mock()
        mock_message.body = json.dumps(message_data).encode()

        @asynccontextmanager
        async def mock_process():
            yield

        mock_message.process = mock_process

        # Act
        await consumer.on_message(mock_message)

        # Assert
        mock_bonus_service.accrue_bonuses.assert_not_called()

    async def test_on_message_missing_amount_logs_error(self, mock_bonus_service: AsyncMock):
        """Test handling message with missing amount"""
        # Arrange
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)

        message_data = {
            "order_id": "123e4567-e89b-12d3-a456-426614174000",
            "user_id": "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d"
        }

        mock_message = Mock()
        mock_message.body = json.dumps(message_data).encode()

        @asynccontextmanager
        async def mock_process():
            yield

        mock_message.process = mock_process

        # Act
        await consumer.on_message(mock_message)

        # Assert
        mock_bonus_service.accrue_bonuses.assert_not_called()

    async def test_on_message_invalid_json_logs_error(self, mock_bonus_service: AsyncMock):
        """Test handling message with invalid JSON"""
        # Arrange
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)

        mock_message = Mock()
        mock_message.body = b"invalid json {{{{"

        @asynccontextmanager
        async def mock_process():
            yield

        mock_message.process = mock_process

        # Act - should not raise exception
        await consumer.on_message(mock_message)

        # Assert
        mock_bonus_service.accrue_bonuses.assert_not_called()

    async def test_on_message_invalid_uuid_logs_error(self, mock_bonus_service: AsyncMock):
        """Test handling message with invalid UUID format"""
        # Arrange
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)

        message_data = {
            "order_id": "not-a-uuid",
            "user_id": "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d",
            "amount": 10000.0
        }

        mock_message = Mock()
        mock_message.body = json.dumps(message_data).encode()

        @asynccontextmanager
        async def mock_process():
            yield

        mock_message.process = mock_process

        # Act
        await consumer.on_message(mock_message)

        # Assert
        mock_bonus_service.accrue_bonuses.assert_not_called()

    async def test_on_message_invalid_amount_type_logs_error(self, mock_bonus_service: AsyncMock):
        """Test handling message with non-numeric amount"""
        # Arrange
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)

        message_data = {
            "order_id": "123e4567-e89b-12d3-a456-426614174000",
            "user_id": "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d",
            "amount": "not-a-number"
        }

        mock_message = Mock()
        mock_message.body = json.dumps(message_data).encode()

        @asynccontextmanager
        async def mock_process():
            yield

        mock_message.process = mock_process

        # Act
        await consumer.on_message(mock_message)

        # Assert
        mock_bonus_service.accrue_bonuses.assert_not_called()

    async def test_on_message_service_exception_logs_error(self, mock_bonus_service: AsyncMock):
        """Test handling exception from bonus service"""
        # Arrange
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)

        message_data = {
            "order_id": "123e4567-e89b-12d3-a456-426614174000",
            "user_id": "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d",
            "amount": 10000.0
        }

        mock_message = Mock()
        mock_message.body = json.dumps(message_data).encode()

        @asynccontextmanager
        async def mock_process():
            yield

        mock_message.process = mock_process
        mock_bonus_service.accrue_bonuses.side_effect = Exception("Database error")

        # Act - should not raise exception (error is logged)
        await consumer.on_message(mock_message)

        # Assert - service was called but exception was caught
        mock_bonus_service.accrue_bonuses.assert_called_once()

    async def test_on_message_large_amount(self, mock_bonus_service: AsyncMock):
        """Test processing message with large payment amount"""
        # Arrange
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)

        message_data = {
            "order_id": "123e4567-e89b-12d3-a456-426614174000",
            "user_id": "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d",
            "amount": 1000000.0
        }

        mock_message = Mock()
        mock_message.body = json.dumps(message_data).encode()

        @asynccontextmanager
        async def mock_process():
            yield

        mock_message.process = mock_process
        mock_bonus_service.accrue_bonuses.return_value = 10000.0

        # Act
        await consumer.on_message(mock_message)

        # Assert
        mock_bonus_service.accrue_bonuses.assert_called_once()
        call_kwargs = mock_bonus_service.accrue_bonuses.call_args.kwargs
        assert call_kwargs["payment_amount"] == 1000000.0


@pytest.mark.unit
@pytest.mark.asyncio
class TestConsumerStop:
    """Test consumer stop method"""

    async def test_stop_closes_channel(self, mock_bonus_service: AsyncMock):
        """Test stop method closes channel"""
        # Arrange
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)
        mock_channel = AsyncMock()
        consumer.channel = mock_channel

        # Act
        await consumer.stop()

        # Assert
        mock_channel.close.assert_called_once()

    async def test_stop_closes_connection(self, mock_bonus_service: AsyncMock):
        """Test stop method closes connection"""
        # Arrange
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)
        mock_connection = AsyncMock()
        consumer.connection = mock_connection

        # Act
        await consumer.stop()

        # Assert
        mock_connection.close.assert_called_once()

    async def test_stop_with_no_channel(self, mock_bonus_service: AsyncMock):
        """Test stop method when channel is None"""
        # Arrange
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)
        consumer.channel = None
        mock_connection = AsyncMock()
        consumer.connection = mock_connection

        # Act - should not raise exception
        await consumer.stop()

        # Assert
        mock_connection.close.assert_called_once()

    async def test_stop_with_no_connection(self, mock_bonus_service: AsyncMock):
        """Test stop method when connection is None"""
        # Arrange
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)
        consumer.connection = None

        # Act - should not raise exception
        await consumer.stop()

        # No assertions needed - just verify no exception raised

    async def test_stop_with_exception_logs_error(self, mock_bonus_service: AsyncMock):
        """Test stop method logs error on exception"""
        # Arrange
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)
        mock_channel = AsyncMock()
        mock_channel.close.side_effect = Exception("Close error")
        consumer.channel = mock_channel

        # Act - should not raise exception (error is logged)
        await consumer.stop()

        # Assert
        mock_channel.close.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
class TestConsumerIntegration:
    """Test consumer integration scenarios"""

    @patch('app.services.rabbitmq_consumer.aio_pika.connect_robust')
    async def test_start_and_stop_lifecycle(
        self,
        mock_connect: AsyncMock,
        mock_bonus_service: AsyncMock,
        mock_rabbitmq_connection: AsyncMock
    ):
        """Test complete start and stop lifecycle"""
        # Arrange
        mock_connect.return_value = mock_rabbitmq_connection
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)

        # Act
        await consumer.start()
        await consumer.stop()

        # Assert
        mock_connect.assert_called_once()
        mock_rabbitmq_connection.channel.assert_called_once()

    async def test_message_processing_with_different_amounts(
        self, mock_bonus_service: AsyncMock
    ):
        """Test processing messages with various payment amounts"""
        # Arrange
        consumer = RabbitMQConsumer(bonus_service=mock_bonus_service)
        amounts = [100.0, 1000.0, 10000.0, 50000.0]

        @asynccontextmanager
        async def mock_process():
            yield

        # Act
        for amount in amounts:
            message_data = {
                "order_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d",
                "amount": amount
            }

            mock_message = Mock()
            mock_message.body = json.dumps(message_data).encode()
            mock_message.process = mock_process
            mock_bonus_service.accrue_bonuses.return_value = amount * 0.01

            await consumer.on_message(mock_message)

        # Assert
        assert mock_bonus_service.accrue_bonuses.call_count == len(amounts)
