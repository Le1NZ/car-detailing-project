"""Unit tests for Pydantic models."""
import pytest
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import ValidationError

from app.models.ticket import (
    CreateTicketRequest,
    TicketResponse,
    AddMessageRequest,
    MessageResponse,
    Ticket,
    Message,
)


class TestCreateTicketRequest:
    """Test suite for CreateTicketRequest model validation."""

    def test_create_ticket_request_valid_data(self):
        """Test CreateTicketRequest with valid data."""
        request = CreateTicketRequest(
            subject="Test Subject",
            message="Test Message",
            order_id=uuid4()
        )

        assert request.subject == "Test Subject"
        assert request.message == "Test Message"
        assert isinstance(request.order_id, UUID)

    def test_create_ticket_request_without_order_id(self):
        """Test CreateTicketRequest without optional order_id."""
        request = CreateTicketRequest(
            subject="Test Subject",
            message="Test Message"
        )

        assert request.subject == "Test Subject"
        assert request.message == "Test Message"
        assert request.order_id is None

    def test_create_ticket_request_strips_whitespace(self):
        """Test that CreateTicketRequest strips leading/trailing whitespace."""
        request = CreateTicketRequest(
            subject="  Test Subject  ",
            message="  Test Message  "
        )

        assert request.subject == "Test Subject"
        assert request.message == "Test Message"

    def test_create_ticket_request_empty_subject(self):
        """Test CreateTicketRequest fails with empty subject."""
        with pytest.raises(ValidationError) as exc_info:
            CreateTicketRequest(
                subject="",
                message="Test Message"
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("subject",)
        assert "at least 1 character" in errors[0]["msg"].lower()

    def test_create_ticket_request_empty_message(self):
        """Test CreateTicketRequest fails with empty message."""
        with pytest.raises(ValidationError) as exc_info:
            CreateTicketRequest(
                subject="Test Subject",
                message=""
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("message",)
        assert "at least 1 character" in errors[0]["msg"].lower()

    def test_create_ticket_request_whitespace_only_subject(self):
        """Test CreateTicketRequest fails with whitespace-only subject."""
        with pytest.raises(ValidationError) as exc_info:
            CreateTicketRequest(
                subject="   ",
                message="Test Message"
            )

        errors = exc_info.value.errors()
        assert any("cannot be empty or whitespace" in str(e["msg"]).lower() for e in errors)

    def test_create_ticket_request_whitespace_only_message(self):
        """Test CreateTicketRequest fails with whitespace-only message."""
        with pytest.raises(ValidationError) as exc_info:
            CreateTicketRequest(
                subject="Test Subject",
                message="   "
            )

        errors = exc_info.value.errors()
        assert any("cannot be empty or whitespace" in str(e["msg"]).lower() for e in errors)

    def test_create_ticket_request_missing_required_fields(self):
        """Test CreateTicketRequest fails when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            CreateTicketRequest()

        errors = exc_info.value.errors()
        assert len(errors) == 2  # subject and message are required
        error_fields = [e["loc"][0] for e in errors]
        assert "subject" in error_fields
        assert "message" in error_fields

    def test_create_ticket_request_invalid_order_id_type(self):
        """Test CreateTicketRequest fails with invalid order_id type."""
        with pytest.raises(ValidationError) as exc_info:
            CreateTicketRequest(
                subject="Test Subject",
                message="Test Message",
                order_id="not-a-uuid"
            )

        errors = exc_info.value.errors()
        assert any(e["loc"][0] == "order_id" for e in errors)


class TestTicketResponse:
    """Test suite for TicketResponse model."""

    def test_ticket_response_valid_data(self):
        """Test TicketResponse with valid data."""
        ticket_id = uuid4()
        created_at = datetime.utcnow()

        response = TicketResponse(
            ticket_id=ticket_id,
            status="open",
            created_at=created_at
        )

        assert response.ticket_id == ticket_id
        assert response.status == "open"
        assert response.created_at == created_at

    def test_ticket_response_missing_required_fields(self):
        """Test TicketResponse fails when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            TicketResponse()

        errors = exc_info.value.errors()
        assert len(errors) == 3  # ticket_id, status, created_at are required
        error_fields = [e["loc"][0] for e in errors]
        assert "ticket_id" in error_fields
        assert "status" in error_fields
        assert "created_at" in error_fields


class TestAddMessageRequest:
    """Test suite for AddMessageRequest model validation."""

    def test_add_message_request_valid_data(self):
        """Test AddMessageRequest with valid data."""
        request = AddMessageRequest(message="Test message content")

        assert request.message == "Test message content"

    def test_add_message_request_strips_whitespace(self):
        """Test that AddMessageRequest strips leading/trailing whitespace."""
        request = AddMessageRequest(message="  Test message content  ")

        assert request.message == "Test message content"

    def test_add_message_request_empty_message(self):
        """Test AddMessageRequest fails with empty message."""
        with pytest.raises(ValidationError) as exc_info:
            AddMessageRequest(message="")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("message",)
        assert "at least 1 character" in errors[0]["msg"].lower()

    def test_add_message_request_whitespace_only_message(self):
        """Test AddMessageRequest fails with whitespace-only message."""
        with pytest.raises(ValidationError) as exc_info:
            AddMessageRequest(message="   ")

        errors = exc_info.value.errors()
        assert any("cannot be empty or whitespace" in str(e["msg"]).lower() for e in errors)

    def test_add_message_request_missing_message(self):
        """Test AddMessageRequest fails when message is missing."""
        with pytest.raises(ValidationError) as exc_info:
            AddMessageRequest()

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("message",)


class TestMessageResponse:
    """Test suite for MessageResponse model."""

    def test_message_response_valid_data(self):
        """Test MessageResponse with valid data."""
        message_id = uuid4()
        ticket_id = uuid4()
        created_at = datetime.utcnow()

        response = MessageResponse(
            message_id=message_id,
            ticket_id=ticket_id,
            author_id="support_agent_01",
            message="Test message",
            created_at=created_at
        )

        assert response.message_id == message_id
        assert response.ticket_id == ticket_id
        assert response.author_id == "support_agent_01"
        assert response.message == "Test message"
        assert response.created_at == created_at

    def test_message_response_missing_required_fields(self):
        """Test MessageResponse fails when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            MessageResponse()

        errors = exc_info.value.errors()
        assert len(errors) == 5  # All fields are required
        error_fields = [e["loc"][0] for e in errors]
        assert "message_id" in error_fields
        assert "ticket_id" in error_fields
        assert "author_id" in error_fields
        assert "message" in error_fields
        assert "created_at" in error_fields


class TestTicket:
    """Test suite for internal Ticket model."""

    def test_ticket_valid_data(self):
        """Test Ticket model with valid data."""
        ticket_id = uuid4()
        user_id = uuid4()
        order_id = uuid4()
        created_at = datetime.utcnow()

        ticket = Ticket(
            ticket_id=ticket_id,
            user_id=user_id,
            subject="Test Subject",
            message="Test Message",
            order_id=order_id,
            status="open",
            created_at=created_at
        )

        assert ticket.ticket_id == ticket_id
        assert ticket.user_id == user_id
        assert ticket.subject == "Test Subject"
        assert ticket.message == "Test Message"
        assert ticket.order_id == order_id
        assert ticket.status == "open"
        assert ticket.created_at == created_at

    def test_ticket_without_order_id(self):
        """Test Ticket model without optional order_id."""
        ticket_id = uuid4()
        user_id = uuid4()
        created_at = datetime.utcnow()

        ticket = Ticket(
            ticket_id=ticket_id,
            user_id=user_id,
            subject="Test Subject",
            message="Test Message",
            status="in_progress",
            created_at=created_at
        )

        assert ticket.order_id is None
        assert ticket.status == "in_progress"

    def test_ticket_with_closed_status(self):
        """Test Ticket model with closed status."""
        ticket = Ticket(
            ticket_id=uuid4(),
            user_id=uuid4(),
            subject="Test Subject",
            message="Test Message",
            status="closed",
            created_at=datetime.utcnow()
        )

        assert ticket.status == "closed"

    def test_ticket_missing_required_fields(self):
        """Test Ticket model fails when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            Ticket()

        errors = exc_info.value.errors()
        error_fields = [e["loc"][0] for e in errors]
        assert "ticket_id" in error_fields
        assert "user_id" in error_fields
        assert "subject" in error_fields
        assert "message" in error_fields
        assert "status" in error_fields
        assert "created_at" in error_fields


class TestMessage:
    """Test suite for internal Message model."""

    def test_message_valid_data(self):
        """Test Message model with valid data."""
        message_id = uuid4()
        ticket_id = uuid4()
        created_at = datetime.utcnow()

        message = Message(
            message_id=message_id,
            ticket_id=ticket_id,
            author_id="user_123",
            message="This is a test message",
            created_at=created_at
        )

        assert message.message_id == message_id
        assert message.ticket_id == ticket_id
        assert message.author_id == "user_123"
        assert message.message == "This is a test message"
        assert message.created_at == created_at

    def test_message_different_author_ids(self):
        """Test Message model with different author ID formats."""
        # Test with user UUID as string
        message1 = Message(
            message_id=uuid4(),
            ticket_id=uuid4(),
            author_id=str(uuid4()),
            message="User message",
            created_at=datetime.utcnow()
        )
        assert isinstance(message1.author_id, str)

        # Test with support agent ID
        message2 = Message(
            message_id=uuid4(),
            ticket_id=uuid4(),
            author_id="support_agent_01",
            message="Support message",
            created_at=datetime.utcnow()
        )
        assert message2.author_id == "support_agent_01"

    def test_message_missing_required_fields(self):
        """Test Message model fails when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            Message()

        errors = exc_info.value.errors()
        error_fields = [e["loc"][0] for e in errors]
        assert "message_id" in error_fields
        assert "ticket_id" in error_fields
        assert "author_id" in error_fields
        assert "message" in error_fields
        assert "created_at" in error_fields
