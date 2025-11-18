"""Unit tests for RabbitMQPublisher."""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.services.rabbitmq_publisher import RabbitMQPublisher


class TestRabbitMQPublisherConnection:
    """Tests for RabbitMQ connection management."""

    @pytest.mark.asyncio
    async def test_connect_success(self, mock_aio_pika_connection):
        """Test successfully connecting to RabbitMQ."""
        # Arrange
        mock_connection, mock_channel = mock_aio_pika_connection
        publisher = RabbitMQPublisher()

        with patch("app.services.rabbitmq_publisher.aio_pika.connect_robust") as mock_connect:
            mock_connect.return_value = mock_connection

            # Act
            await publisher.connect()

            # Assert
            mock_connect.assert_called_once()
            mock_connection.channel.assert_called_once()
            mock_channel.declare_queue.assert_called_once_with(
                "payment_succeeded_queue", durable=True
            )
            assert publisher.connection == mock_connection
            assert publisher.channel == mock_channel

    @pytest.mark.asyncio
    async def test_connect_failure_raises_exception(self):
        """Test connection failure raises exception."""
        # Arrange
        publisher = RabbitMQPublisher()

        with patch(
            "app.services.rabbitmq_publisher.aio_pika.connect_robust"
        ) as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")

            # Act & Assert
            with pytest.raises(Exception, match="Connection failed"):
                await publisher.connect()

    @pytest.mark.asyncio
    async def test_connect_sets_queue_name(self, mock_aio_pika_connection):
        """Test connect sets correct queue name."""
        # Arrange
        mock_connection, mock_channel = mock_aio_pika_connection
        publisher = RabbitMQPublisher()

        with patch("app.services.rabbitmq_publisher.aio_pika.connect_robust") as mock_connect:
            mock_connect.return_value = mock_connection

            # Act
            await publisher.connect()

            # Assert
            assert publisher.queue_name == "payment_succeeded_queue"

    @pytest.mark.asyncio
    async def test_close_connection_success(self):
        """Test successfully closing RabbitMQ connection."""
        # Arrange
        publisher = RabbitMQPublisher()
        mock_connection = AsyncMock()
        publisher.connection = mock_connection

        # Act
        await publisher.close()

        # Assert
        mock_connection.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_connection_no_connection(self):
        """Test closing when no connection exists does not raise error."""
        # Arrange
        publisher = RabbitMQPublisher()
        publisher.connection = None

        # Act & Assert - should not raise
        await publisher.close()

    @pytest.mark.asyncio
    async def test_close_connection_handles_exception(self):
        """Test close handles exception gracefully."""
        # Arrange
        publisher = RabbitMQPublisher()
        mock_connection = AsyncMock()
        mock_connection.close.side_effect = Exception("Close failed")
        publisher.connection = mock_connection

        # Act & Assert - should not raise
        await publisher.close()
        mock_connection.close.assert_called_once()


class TestRabbitMQPublisherPublish:
    """Tests for publishing messages to RabbitMQ."""

    @pytest.mark.asyncio
    async def test_publish_payment_success_message_format(self, mock_aio_pika_connection):
        """Test publish sends correctly formatted message."""
        # Arrange
        mock_connection, mock_channel = mock_aio_pika_connection
        publisher = RabbitMQPublisher()
        publisher.connection = mock_connection
        publisher.channel = mock_channel

        order_id = "ord_test123"
        user_id = "user_456"
        amount = 2500.00

        # Act
        await publisher.publish_payment_success(order_id, user_id, amount)

        # Assert
        mock_channel.default_exchange.publish.assert_called_once()
        call_args = mock_channel.default_exchange.publish.call_args

        # Verify routing key
        assert call_args[1]["routing_key"] == "payment_succeeded_queue"

        # Verify message body
        message = call_args[0][0]
        message_body = json.loads(message.body.decode())
        assert message_body["order_id"] == order_id
        assert message_body["user_id"] == user_id
        assert message_body["amount"] == amount

    @pytest.mark.asyncio
    async def test_publish_payment_success_without_channel_raises_error(self):
        """Test publishing without initialized channel raises RuntimeError."""
        # Arrange
        publisher = RabbitMQPublisher()
        publisher.channel = None

        # Act & Assert
        with pytest.raises(RuntimeError, match="RabbitMQ channel is not initialized"):
            await publisher.publish_payment_success("ord_123", "user_456", 1000.00)

    @pytest.mark.asyncio
    async def test_publish_payment_success_persistent_message(self, mock_aio_pika_connection):
        """Test published message has persistent delivery mode."""
        # Arrange
        mock_connection, mock_channel = mock_aio_pika_connection
        publisher = RabbitMQPublisher()
        publisher.connection = mock_connection
        publisher.channel = mock_channel

        # Act
        await publisher.publish_payment_success("ord_123", "user_456", 1000.00)

        # Assert
        mock_channel.default_exchange.publish.assert_called_once()
        call_args = mock_channel.default_exchange.publish.call_args
        message = call_args[0][0]

        # Verify delivery mode is PERSISTENT (value 2)
        from aio_pika import DeliveryMode
        assert message.delivery_mode == DeliveryMode.PERSISTENT

    @pytest.mark.asyncio
    async def test_publish_payment_success_handles_publish_error(
        self, mock_aio_pika_connection
    ):
        """Test publish handles RabbitMQ publish errors."""
        # Arrange
        mock_connection, mock_channel = mock_aio_pika_connection
        mock_channel.default_exchange.publish.side_effect = Exception("Publish failed")

        publisher = RabbitMQPublisher()
        publisher.connection = mock_connection
        publisher.channel = mock_channel

        # Act & Assert
        with pytest.raises(Exception, match="Publish failed"):
            await publisher.publish_payment_success("ord_123", "user_456", 1000.00)

    @pytest.mark.asyncio
    async def test_publish_payment_success_correct_routing_key(
        self, mock_aio_pika_connection
    ):
        """Test message is published with correct routing key."""
        # Arrange
        mock_connection, mock_channel = mock_aio_pika_connection
        publisher = RabbitMQPublisher()
        publisher.connection = mock_connection
        publisher.channel = mock_channel
        publisher.queue_name = "payment_succeeded_queue"

        # Act
        await publisher.publish_payment_success("ord_xyz", "user_999", 5000.00)

        # Assert
        call_args = mock_channel.default_exchange.publish.call_args
        assert call_args[1]["routing_key"] == "payment_succeeded_queue"

    @pytest.mark.asyncio
    async def test_publish_payment_success_with_float_amount(
        self, mock_aio_pika_connection
    ):
        """Test publishing with float amount preserves precision."""
        # Arrange
        mock_connection, mock_channel = mock_aio_pika_connection
        publisher = RabbitMQPublisher()
        publisher.connection = mock_connection
        publisher.channel = mock_channel

        amount = 1234.56

        # Act
        await publisher.publish_payment_success("ord_123", "user_456", amount)

        # Assert
        call_args = mock_channel.default_exchange.publish.call_args
        message = call_args[0][0]
        message_body = json.loads(message.body.decode())
        assert message_body["amount"] == amount
        assert isinstance(message_body["amount"], float)

    @pytest.mark.asyncio
    async def test_publish_payment_success_with_special_characters(
        self, mock_aio_pika_connection
    ):
        """Test publishing with special characters in IDs."""
        # Arrange
        mock_connection, mock_channel = mock_aio_pika_connection
        publisher = RabbitMQPublisher()
        publisher.connection = mock_connection
        publisher.channel = mock_channel

        order_id = "ord_test-123_special"
        user_id = "user_test-456_special"

        # Act
        await publisher.publish_payment_success(order_id, user_id, 1000.00)

        # Assert
        call_args = mock_channel.default_exchange.publish.call_args
        message = call_args[0][0]
        message_body = json.loads(message.body.decode())
        assert message_body["order_id"] == order_id
        assert message_body["user_id"] == user_id


class TestRabbitMQPublisherInitialization:
    """Tests for RabbitMQ publisher initialization."""

    def test_init_sets_defaults(self):
        """Test initialization sets default values."""
        # Act
        publisher = RabbitMQPublisher()

        # Assert
        assert publisher.connection is None
        assert publisher.channel is None
        assert publisher.queue_name == "payment_succeeded_queue"

    def test_init_creates_independent_instances(self):
        """Test each instance is independent."""
        # Act
        publisher1 = RabbitMQPublisher()
        publisher2 = RabbitMQPublisher()

        # Assert
        assert publisher1 is not publisher2
        publisher1.queue_name = "custom_queue"
        assert publisher2.queue_name == "payment_succeeded_queue"


class TestRabbitMQPublisherEdgeCases:
    """Tests for edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_publish_with_zero_amount(self, mock_aio_pika_connection):
        """Test publishing payment with zero amount."""
        # Arrange
        mock_connection, mock_channel = mock_aio_pika_connection
        publisher = RabbitMQPublisher()
        publisher.connection = mock_connection
        publisher.channel = mock_channel

        # Act
        await publisher.publish_payment_success("ord_123", "user_456", 0.0)

        # Assert
        call_args = mock_channel.default_exchange.publish.call_args
        message = call_args[0][0]
        message_body = json.loads(message.body.decode())
        assert message_body["amount"] == 0.0

    @pytest.mark.asyncio
    async def test_publish_with_large_amount(self, mock_aio_pika_connection):
        """Test publishing payment with very large amount."""
        # Arrange
        mock_connection, mock_channel = mock_aio_pika_connection
        publisher = RabbitMQPublisher()
        publisher.connection = mock_connection
        publisher.channel = mock_channel

        large_amount = 999999999.99

        # Act
        await publisher.publish_payment_success("ord_123", "user_456", large_amount)

        # Assert
        call_args = mock_channel.default_exchange.publish.call_args
        message = call_args[0][0]
        message_body = json.loads(message.body.decode())
        assert message_body["amount"] == large_amount

    @pytest.mark.asyncio
    async def test_publish_with_empty_string_ids(self, mock_aio_pika_connection):
        """Test publishing with empty string IDs."""
        # Arrange
        mock_connection, mock_channel = mock_aio_pika_connection
        publisher = RabbitMQPublisher()
        publisher.connection = mock_connection
        publisher.channel = mock_channel

        # Act
        await publisher.publish_payment_success("", "", 100.00)

        # Assert
        call_args = mock_channel.default_exchange.publish.call_args
        message = call_args[0][0]
        message_body = json.loads(message.body.decode())
        assert message_body["order_id"] == ""
        assert message_body["user_id"] == ""

    @pytest.mark.asyncio
    async def test_multiple_publishes(self, mock_aio_pika_connection):
        """Test publishing multiple messages sequentially."""
        # Arrange
        mock_connection, mock_channel = mock_aio_pika_connection
        publisher = RabbitMQPublisher()
        publisher.connection = mock_connection
        publisher.channel = mock_channel

        # Act
        await publisher.publish_payment_success("ord_001", "user_001", 100.00)
        await publisher.publish_payment_success("ord_002", "user_002", 200.00)
        await publisher.publish_payment_success("ord_003", "user_003", 300.00)

        # Assert
        assert mock_channel.default_exchange.publish.call_count == 3
