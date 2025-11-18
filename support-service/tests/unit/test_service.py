"""Unit tests for SupportService business logic."""
import pytest
from datetime import datetime
from uuid import UUID, uuid4
from unittest.mock import Mock, MagicMock, patch
from fastapi import HTTPException, status

from app.services.support_service import SupportService
from app.models.ticket import (
    CreateTicketRequest,
    TicketResponse,
    AddMessageRequest,
    MessageResponse,
    Ticket,
    Message,
)


class TestSupportService:
    """Test suite for SupportService business logic."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        return Mock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create a SupportService instance with mocked repository."""
        service = SupportService()
        service.repository = mock_repository
        return service

    @pytest.fixture
    def sample_user_id(self):
        """Sample user UUID for tests."""
        return uuid4()

    @pytest.fixture
    def sample_ticket_id(self):
        """Sample ticket UUID for tests."""
        return uuid4()

    @pytest.fixture
    def sample_order_id(self):
        """Sample order UUID for tests."""
        return uuid4()


class TestCreateTicket(TestSupportService):
    """Test suite for create_ticket method."""

    def test_create_ticket_success(self, service, mock_repository, sample_user_id, sample_order_id):
        """Test successful ticket creation."""
        request = CreateTicketRequest(
            subject="Test Subject",
            message="Test Message",
            order_id=sample_order_id
        )

        ticket_id = uuid4()
        created_at = datetime.utcnow()

        mock_ticket = Ticket(
            ticket_id=ticket_id,
            user_id=sample_user_id,
            subject=request.subject,
            message=request.message,
            order_id=request.order_id,
            status="open",
            created_at=created_at
        )

        mock_repository.create_ticket.return_value = mock_ticket

        response = service.create_ticket(request, sample_user_id)

        # Verify repository was called correctly
        mock_repository.create_ticket.assert_called_once_with(
            user_id=sample_user_id,
            subject=request.subject,
            message=request.message,
            order_id=request.order_id
        )

        # Verify response
        assert isinstance(response, TicketResponse)
        assert response.ticket_id == ticket_id
        assert response.status == "open"
        assert response.created_at == created_at

    def test_create_ticket_without_order_id(self, service, mock_repository, sample_user_id):
        """Test creating ticket without optional order_id."""
        request = CreateTicketRequest(
            subject="Test Subject",
            message="Test Message"
        )

        mock_ticket = Ticket(
            ticket_id=uuid4(),
            user_id=sample_user_id,
            subject=request.subject,
            message=request.message,
            status="open",
            created_at=datetime.utcnow()
        )

        mock_repository.create_ticket.return_value = mock_ticket

        response = service.create_ticket(request, sample_user_id)

        # Verify order_id=None was passed to repository
        mock_repository.create_ticket.assert_called_once_with(
            user_id=sample_user_id,
            subject=request.subject,
            message=request.message,
            order_id=None
        )

        assert isinstance(response, TicketResponse)

    def test_create_ticket_returns_correct_response_format(self, service, mock_repository, sample_user_id):
        """Test that create_ticket returns correctly formatted TicketResponse."""
        request = CreateTicketRequest(
            subject="Subject",
            message="Message"
        )

        ticket_id = uuid4()
        created_at = datetime.utcnow()

        mock_ticket = Ticket(
            ticket_id=ticket_id,
            user_id=sample_user_id,
            subject="Subject",
            message="Message",
            status="open",
            created_at=created_at
        )

        mock_repository.create_ticket.return_value = mock_ticket

        response = service.create_ticket(request, sample_user_id)

        assert response.ticket_id == ticket_id
        assert response.status == "open"
        assert response.created_at == created_at

    def test_create_ticket_propagates_repository_exception(self, service, mock_repository, sample_user_id):
        """Test that exceptions from repository are propagated."""
        request = CreateTicketRequest(
            subject="Subject",
            message="Message"
        )

        mock_repository.create_ticket.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            service.create_ticket(request, sample_user_id)


class TestAddMessageToTicket(TestSupportService):
    """Test suite for add_message_to_ticket method."""

    def test_add_message_success(self, service, mock_repository, sample_ticket_id):
        """Test successfully adding a message to an existing ticket."""
        request = AddMessageRequest(message="Test reply message")
        author_id = "support_agent_01"

        # Mock existing open ticket
        mock_ticket = Ticket(
            ticket_id=sample_ticket_id,
            user_id=uuid4(),
            subject="Subject",
            message="Initial message",
            status="open",
            created_at=datetime.utcnow()
        )

        message_id = uuid4()
        created_at = datetime.utcnow()

        mock_message = Message(
            message_id=message_id,
            ticket_id=sample_ticket_id,
            author_id=author_id,
            message=request.message,
            created_at=created_at
        )

        mock_repository.get_ticket_by_id.return_value = mock_ticket
        mock_repository.is_ticket_closed.return_value = False
        mock_repository.add_message.return_value = mock_message

        response = service.add_message_to_ticket(sample_ticket_id, request, author_id)

        # Verify repository calls
        mock_repository.get_ticket_by_id.assert_called_once_with(sample_ticket_id)
        mock_repository.is_ticket_closed.assert_called_once_with(sample_ticket_id)
        mock_repository.add_message.assert_called_once_with(
            ticket_id=sample_ticket_id,
            author_id=author_id,
            message_text=request.message
        )

        # Verify response
        assert isinstance(response, MessageResponse)
        assert response.message_id == message_id
        assert response.ticket_id == sample_ticket_id
        assert response.author_id == author_id
        assert response.message == request.message
        assert response.created_at == created_at

    def test_add_message_ticket_not_found(self, service, mock_repository, sample_ticket_id):
        """Test adding message to non-existent ticket raises 404."""
        request = AddMessageRequest(message="Test message")
        author_id = "support_agent_01"

        mock_repository.get_ticket_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            service.add_message_to_ticket(sample_ticket_id, request, author_id)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert str(sample_ticket_id) in exc_info.value.detail
        assert "not found" in exc_info.value.detail.lower()

        # Verify repository was checked
        mock_repository.get_ticket_by_id.assert_called_once_with(sample_ticket_id)

        # Verify no message was added
        mock_repository.add_message.assert_not_called()

    def test_add_message_ticket_closed(self, service, mock_repository, sample_ticket_id):
        """Test adding message to closed ticket raises 409."""
        request = AddMessageRequest(message="Test message")
        author_id = "support_agent_01"

        # Mock closed ticket
        mock_ticket = Ticket(
            ticket_id=sample_ticket_id,
            user_id=uuid4(),
            subject="Subject",
            message="Initial message",
            status="closed",
            created_at=datetime.utcnow()
        )

        mock_repository.get_ticket_by_id.return_value = mock_ticket
        mock_repository.is_ticket_closed.return_value = True

        with pytest.raises(HTTPException) as exc_info:
            service.add_message_to_ticket(sample_ticket_id, request, author_id)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "closed" in exc_info.value.detail.lower()

        # Verify checks were performed
        mock_repository.get_ticket_by_id.assert_called_once_with(sample_ticket_id)
        mock_repository.is_ticket_closed.assert_called_once_with(sample_ticket_id)

        # Verify no message was added
        mock_repository.add_message.assert_not_called()

    def test_add_message_to_in_progress_ticket(self, service, mock_repository, sample_ticket_id):
        """Test adding message to in_progress ticket succeeds."""
        request = AddMessageRequest(message="Test message")
        author_id = "support_agent_01"

        # Mock in_progress ticket
        mock_ticket = Ticket(
            ticket_id=sample_ticket_id,
            user_id=uuid4(),
            subject="Subject",
            message="Initial message",
            status="in_progress",
            created_at=datetime.utcnow()
        )

        mock_message = Message(
            message_id=uuid4(),
            ticket_id=sample_ticket_id,
            author_id=author_id,
            message=request.message,
            created_at=datetime.utcnow()
        )

        mock_repository.get_ticket_by_id.return_value = mock_ticket
        mock_repository.is_ticket_closed.return_value = False
        mock_repository.add_message.return_value = mock_message

        response = service.add_message_to_ticket(sample_ticket_id, request, author_id)

        assert isinstance(response, MessageResponse)
        mock_repository.add_message.assert_called_once()

    def test_add_message_with_different_author_types(self, service, mock_repository, sample_ticket_id):
        """Test adding messages with different author ID formats."""
        request = AddMessageRequest(message="Test message")

        mock_ticket = Ticket(
            ticket_id=sample_ticket_id,
            user_id=uuid4(),
            subject="Subject",
            message="Initial",
            status="open",
            created_at=datetime.utcnow()
        )

        mock_repository.get_ticket_by_id.return_value = mock_ticket
        mock_repository.is_ticket_closed.return_value = False

        # Test with support agent ID
        mock_message1 = Message(
            message_id=uuid4(),
            ticket_id=sample_ticket_id,
            author_id="support_agent_01",
            message=request.message,
            created_at=datetime.utcnow()
        )
        mock_repository.add_message.return_value = mock_message1

        response1 = service.add_message_to_ticket(sample_ticket_id, request, "support_agent_01")
        assert response1.author_id == "support_agent_01"

        # Test with user UUID string
        user_uuid = str(uuid4())
        mock_message2 = Message(
            message_id=uuid4(),
            ticket_id=sample_ticket_id,
            author_id=user_uuid,
            message=request.message,
            created_at=datetime.utcnow()
        )
        mock_repository.add_message.return_value = mock_message2

        response2 = service.add_message_to_ticket(sample_ticket_id, request, user_uuid)
        assert response2.author_id == user_uuid

    def test_add_message_calls_repository_in_correct_order(self, service, mock_repository, sample_ticket_id):
        """Test that service checks ticket existence and status before adding message."""
        request = AddMessageRequest(message="Test message")
        author_id = "agent"

        mock_ticket = Ticket(
            ticket_id=sample_ticket_id,
            user_id=uuid4(),
            subject="Subject",
            message="Initial",
            status="open",
            created_at=datetime.utcnow()
        )

        mock_message = Message(
            message_id=uuid4(),
            ticket_id=sample_ticket_id,
            author_id=author_id,
            message=request.message,
            created_at=datetime.utcnow()
        )

        mock_repository.get_ticket_by_id.return_value = mock_ticket
        mock_repository.is_ticket_closed.return_value = False
        mock_repository.add_message.return_value = mock_message

        service.add_message_to_ticket(sample_ticket_id, request, author_id)

        # Verify call order
        call_order = []
        for call in mock_repository.method_calls:
            call_order.append(call[0])

        assert call_order == ['get_ticket_by_id', 'is_ticket_closed', 'add_message']

    def test_add_message_handles_empty_message_after_validation(self, service, mock_repository, sample_ticket_id):
        """Test that pydantic validation prevents empty messages before service layer."""
        # Pydantic should catch this before it reaches the service
        with pytest.raises(Exception):  # ValidationError from Pydantic
            AddMessageRequest(message="")

    def test_add_message_preserves_message_content(self, service, mock_repository, sample_ticket_id):
        """Test that message content is preserved exactly as provided (after validation stripping)."""
        long_message = "This is a very long message " * 50
        request = AddMessageRequest(message=long_message)
        author_id = "agent"

        # The request strips whitespace, so we need to expect the stripped version
        expected_message = long_message.strip()

        mock_ticket = Ticket(
            ticket_id=sample_ticket_id,
            user_id=uuid4(),
            subject="Subject",
            message="Initial",
            status="open",
            created_at=datetime.utcnow()
        )

        mock_message = Message(
            message_id=uuid4(),
            ticket_id=sample_ticket_id,
            author_id=author_id,
            message=expected_message,
            created_at=datetime.utcnow()
        )

        mock_repository.get_ticket_by_id.return_value = mock_ticket
        mock_repository.is_ticket_closed.return_value = False
        mock_repository.add_message.return_value = mock_message

        response = service.add_message_to_ticket(sample_ticket_id, request, author_id)

        # Verify full message content is passed (stripped version)
        mock_repository.add_message.assert_called_once_with(
            ticket_id=sample_ticket_id,
            author_id=author_id,
            message_text=expected_message
        )
        assert response.message == expected_message


class TestSupportServiceInitialization(TestSupportService):
    """Test suite for service initialization."""

    def test_service_initialization(self):
        """Test that service initializes with repository."""
        service = SupportService()

        assert service.repository is not None

    def test_service_uses_singleton_repository(self):
        """Test that service uses the singleton repository instance."""
        from app.repositories.local_ticket_repo import ticket_repository

        service = SupportService()

        assert service.repository is ticket_repository


class TestSupportServiceEdgeCases(TestSupportService):
    """Test suite for edge cases and error scenarios."""

    def test_create_ticket_with_special_characters(self, service, mock_repository, sample_user_id):
        """Test creating ticket with special characters in subject and message."""
        request = CreateTicketRequest(
            subject="Bug Report: File not found @#$%",
            message="Error occurred: 'Cannot find /path/to/file' <script>alert('test')</script>"
        )

        mock_ticket = Ticket(
            ticket_id=uuid4(),
            user_id=sample_user_id,
            subject=request.subject,
            message=request.message,
            status="open",
            created_at=datetime.utcnow()
        )

        mock_repository.create_ticket.return_value = mock_ticket

        response = service.create_ticket(request, sample_user_id)

        # Verify special characters are preserved
        call_args = mock_repository.create_ticket.call_args
        assert call_args.kwargs['subject'] == request.subject
        assert call_args.kwargs['message'] == request.message

    def test_add_message_ticket_exists_but_status_check_fails(self, service, mock_repository, sample_ticket_id):
        """Test scenario where ticket exists but status check indicates closed."""
        request = AddMessageRequest(message="Test message")
        author_id = "agent"

        # Ticket exists
        mock_ticket = Ticket(
            ticket_id=sample_ticket_id,
            user_id=uuid4(),
            subject="Subject",
            message="Initial",
            status="open",  # Status says open
            created_at=datetime.utcnow()
        )

        mock_repository.get_ticket_by_id.return_value = mock_ticket
        mock_repository.is_ticket_closed.return_value = True  # But check says closed

        with pytest.raises(HTTPException) as exc_info:
            service.add_message_to_ticket(sample_ticket_id, request, author_id)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
