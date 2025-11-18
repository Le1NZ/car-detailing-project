"""Unit tests for LocalTicketRepository."""
import pytest
from datetime import datetime
from uuid import UUID, uuid4
from unittest.mock import patch, MagicMock

from app.repositories.local_ticket_repo import LocalTicketRepository
from app.models.ticket import Ticket, Message


class TestLocalTicketRepository:
    """Test suite for LocalTicketRepository."""

    @pytest.fixture
    def repository(self):
        """Create a fresh repository instance for each test."""
        return LocalTicketRepository()

    @pytest.fixture
    def sample_user_id(self):
        """Sample user UUID for tests."""
        return uuid4()

    @pytest.fixture
    def sample_order_id(self):
        """Sample order UUID for tests."""
        return uuid4()

    def test_repository_initialization(self, repository):
        """Test that repository initializes with empty storage."""
        assert isinstance(repository.tickets, dict)
        assert isinstance(repository.messages, dict)
        assert len(repository.tickets) == 0
        assert len(repository.messages) == 0

    def test_create_ticket_with_all_fields(self, repository, sample_user_id, sample_order_id):
        """Test creating a ticket with all fields including order_id."""
        subject = "Test Subject"
        message = "Test Message"

        ticket = repository.create_ticket(
            user_id=sample_user_id,
            subject=subject,
            message=message,
            order_id=sample_order_id
        )

        # Verify ticket properties
        assert isinstance(ticket.ticket_id, UUID)
        assert ticket.user_id == sample_user_id
        assert ticket.subject == subject
        assert ticket.message == message
        assert ticket.order_id == sample_order_id
        assert ticket.status == "open"
        assert isinstance(ticket.created_at, datetime)

        # Verify ticket is stored
        assert ticket.ticket_id in repository.tickets
        assert repository.tickets[ticket.ticket_id] == ticket

        # Verify initial message is stored
        assert ticket.ticket_id in repository.messages
        assert len(repository.messages[ticket.ticket_id]) == 1
        initial_message = repository.messages[ticket.ticket_id][0]
        assert initial_message.message == message
        assert initial_message.author_id == str(sample_user_id)

    def test_create_ticket_without_order_id(self, repository, sample_user_id):
        """Test creating a ticket without order_id."""
        ticket = repository.create_ticket(
            user_id=sample_user_id,
            subject="Test Subject",
            message="Test Message"
        )

        assert ticket.order_id is None
        assert ticket.status == "open"

    def test_create_ticket_generates_unique_ids(self, repository, sample_user_id):
        """Test that each ticket gets a unique ID."""
        ticket1 = repository.create_ticket(
            user_id=sample_user_id,
            subject="Subject 1",
            message="Message 1"
        )

        ticket2 = repository.create_ticket(
            user_id=sample_user_id,
            subject="Subject 2",
            message="Message 2"
        )

        assert ticket1.ticket_id != ticket2.ticket_id
        assert len(repository.tickets) == 2

    def test_create_ticket_stores_initial_message(self, repository, sample_user_id):
        """Test that creating a ticket stores the initial message."""
        ticket = repository.create_ticket(
            user_id=sample_user_id,
            subject="Subject",
            message="Initial message content"
        )

        messages = repository.messages[ticket.ticket_id]
        assert len(messages) == 1
        assert messages[0].message == "Initial message content"
        assert messages[0].ticket_id == ticket.ticket_id
        assert messages[0].author_id == str(sample_user_id)

    @patch('app.repositories.local_ticket_repo.datetime')
    def test_create_ticket_uses_utc_timestamp(self, mock_datetime, repository, sample_user_id):
        """Test that ticket creation uses UTC timestamp."""
        fixed_time = datetime(2024, 6, 12, 9, 0, 0)
        mock_datetime.utcnow.return_value = fixed_time

        ticket = repository.create_ticket(
            user_id=sample_user_id,
            subject="Subject",
            message="Message"
        )

        assert ticket.created_at == fixed_time
        mock_datetime.utcnow.assert_called()

    def test_get_ticket_by_id_existing(self, repository, sample_user_id):
        """Test retrieving an existing ticket by ID."""
        created_ticket = repository.create_ticket(
            user_id=sample_user_id,
            subject="Subject",
            message="Message"
        )

        retrieved_ticket = repository.get_ticket_by_id(created_ticket.ticket_id)

        assert retrieved_ticket is not None
        assert retrieved_ticket.ticket_id == created_ticket.ticket_id
        assert retrieved_ticket.subject == created_ticket.subject
        assert retrieved_ticket.message == created_ticket.message

    def test_get_ticket_by_id_nonexistent(self, repository):
        """Test retrieving a non-existent ticket returns None."""
        random_id = uuid4()

        ticket = repository.get_ticket_by_id(random_id)

        assert ticket is None

    def test_get_ticket_by_id_empty_repository(self, repository):
        """Test getting ticket from empty repository returns None."""
        ticket = repository.get_ticket_by_id(uuid4())

        assert ticket is None

    def test_is_ticket_closed_open_ticket(self, repository, sample_user_id):
        """Test is_ticket_closed returns False for open ticket."""
        ticket = repository.create_ticket(
            user_id=sample_user_id,
            subject="Subject",
            message="Message"
        )

        assert repository.is_ticket_closed(ticket.ticket_id) is False

    def test_is_ticket_closed_closed_ticket(self, repository, sample_user_id):
        """Test is_ticket_closed returns True for closed ticket."""
        ticket = repository.create_ticket(
            user_id=sample_user_id,
            subject="Subject",
            message="Message"
        )

        # Manually close the ticket
        ticket.status = "closed"
        repository.tickets[ticket.ticket_id] = ticket

        assert repository.is_ticket_closed(ticket.ticket_id) is True

    def test_is_ticket_closed_in_progress_ticket(self, repository, sample_user_id):
        """Test is_ticket_closed returns False for in_progress ticket."""
        ticket = repository.create_ticket(
            user_id=sample_user_id,
            subject="Subject",
            message="Message"
        )

        # Change status to in_progress
        ticket.status = "in_progress"
        repository.tickets[ticket.ticket_id] = ticket

        assert repository.is_ticket_closed(ticket.ticket_id) is False

    def test_is_ticket_closed_nonexistent_ticket(self, repository):
        """Test is_ticket_closed returns False for non-existent ticket."""
        random_id = uuid4()

        assert repository.is_ticket_closed(random_id) is False

    def test_add_message_to_existing_ticket(self, repository, sample_user_id):
        """Test adding a message to an existing ticket."""
        ticket = repository.create_ticket(
            user_id=sample_user_id,
            subject="Subject",
            message="Initial message"
        )

        author_id = "support_agent_01"
        message_text = "This is a reply"

        message = repository.add_message(
            ticket_id=ticket.ticket_id,
            author_id=author_id,
            message_text=message_text
        )

        assert isinstance(message.message_id, UUID)
        assert message.ticket_id == ticket.ticket_id
        assert message.author_id == author_id
        assert message.message == message_text
        assert isinstance(message.created_at, datetime)

        # Verify message is stored
        messages = repository.messages[ticket.ticket_id]
        assert len(messages) == 2  # Initial message + new message
        assert messages[1] == message

    def test_add_message_generates_unique_ids(self, repository, sample_user_id):
        """Test that each message gets a unique ID."""
        ticket = repository.create_ticket(
            user_id=sample_user_id,
            subject="Subject",
            message="Initial"
        )

        message1 = repository.add_message(
            ticket_id=ticket.ticket_id,
            author_id="author1",
            message_text="Message 1"
        )

        message2 = repository.add_message(
            ticket_id=ticket.ticket_id,
            author_id="author2",
            message_text="Message 2"
        )

        assert message1.message_id != message2.message_id

    def test_add_message_to_ticket_without_messages_list(self, repository):
        """Test adding a message when ticket_id not in messages dict."""
        ticket_id = uuid4()
        author_id = "support_agent_01"
        message_text = "First message"

        message = repository.add_message(
            ticket_id=ticket_id,
            author_id=author_id,
            message_text=message_text
        )

        assert ticket_id in repository.messages
        assert len(repository.messages[ticket_id]) == 1
        assert repository.messages[ticket_id][0] == message

    @patch('app.repositories.local_ticket_repo.datetime')
    def test_add_message_uses_utc_timestamp(self, mock_datetime, repository, sample_user_id):
        """Test that message addition uses UTC timestamp."""
        fixed_time = datetime(2024, 6, 12, 9, 15, 0)
        mock_datetime.utcnow.return_value = fixed_time

        ticket = repository.create_ticket(
            user_id=sample_user_id,
            subject="Subject",
            message="Initial"
        )

        message = repository.add_message(
            ticket_id=ticket.ticket_id,
            author_id="agent",
            message_text="Reply"
        )

        # utcnow is called twice: once for ticket creation, once for message
        assert mock_datetime.utcnow.call_count >= 1
        assert message.created_at == fixed_time

    def test_add_multiple_messages_to_ticket(self, repository, sample_user_id):
        """Test adding multiple messages to the same ticket."""
        ticket = repository.create_ticket(
            user_id=sample_user_id,
            subject="Subject",
            message="Initial"
        )

        message1 = repository.add_message(
            ticket_id=ticket.ticket_id,
            author_id="user",
            message_text="First reply"
        )

        message2 = repository.add_message(
            ticket_id=ticket.ticket_id,
            author_id="agent",
            message_text="Second reply"
        )

        message3 = repository.add_message(
            ticket_id=ticket.ticket_id,
            author_id="user",
            message_text="Third reply"
        )

        messages = repository.messages[ticket.ticket_id]
        assert len(messages) == 4  # Initial + 3 replies
        assert messages[1] == message1
        assert messages[2] == message2
        assert messages[3] == message3

    def test_get_messages_by_ticket_existing(self, repository, sample_user_id):
        """Test retrieving messages for an existing ticket."""
        ticket = repository.create_ticket(
            user_id=sample_user_id,
            subject="Subject",
            message="Initial"
        )

        repository.add_message(
            ticket_id=ticket.ticket_id,
            author_id="agent",
            message_text="Reply 1"
        )

        repository.add_message(
            ticket_id=ticket.ticket_id,
            author_id="user",
            message_text="Reply 2"
        )

        messages = repository.get_messages_by_ticket(ticket.ticket_id)

        assert len(messages) == 3  # Initial + 2 replies
        assert messages[0].message == "Initial"
        assert messages[1].message == "Reply 1"
        assert messages[2].message == "Reply 2"

    def test_get_messages_by_ticket_nonexistent(self, repository):
        """Test retrieving messages for non-existent ticket returns empty list."""
        random_id = uuid4()

        messages = repository.get_messages_by_ticket(random_id)

        assert messages == []

    def test_get_messages_by_ticket_no_messages(self, repository):
        """Test retrieving messages when ticket has no messages returns empty list."""
        ticket_id = uuid4()

        messages = repository.get_messages_by_ticket(ticket_id)

        assert messages == []

    def test_repository_isolation_between_tickets(self, repository, sample_user_id):
        """Test that tickets and messages are properly isolated."""
        ticket1 = repository.create_ticket(
            user_id=sample_user_id,
            subject="Ticket 1",
            message="Message 1"
        )

        ticket2 = repository.create_ticket(
            user_id=sample_user_id,
            subject="Ticket 2",
            message="Message 2"
        )

        repository.add_message(
            ticket_id=ticket1.ticket_id,
            author_id="agent",
            message_text="Reply to ticket 1"
        )

        # Verify isolation
        messages1 = repository.get_messages_by_ticket(ticket1.ticket_id)
        messages2 = repository.get_messages_by_ticket(ticket2.ticket_id)

        assert len(messages1) == 2  # Initial + 1 reply
        assert len(messages2) == 1  # Only initial message
        assert messages1[1].message == "Reply to ticket 1"
        assert messages2[0].message == "Message 2"

    def test_create_ticket_preserves_all_data(self, repository, sample_user_id, sample_order_id):
        """Test that all ticket data is preserved correctly."""
        ticket = repository.create_ticket(
            user_id=sample_user_id,
            subject="Original Subject",
            message="Original Message",
            order_id=sample_order_id
        )

        retrieved = repository.get_ticket_by_id(ticket.ticket_id)

        assert retrieved.user_id == sample_user_id
        assert retrieved.subject == "Original Subject"
        assert retrieved.message == "Original Message"
        assert retrieved.order_id == sample_order_id
        assert retrieved.status == "open"

    def test_multiple_tickets_different_users(self, repository):
        """Test creating tickets for different users."""
        user1 = uuid4()
        user2 = uuid4()

        ticket1 = repository.create_ticket(
            user_id=user1,
            subject="User 1 ticket",
            message="Message from user 1"
        )

        ticket2 = repository.create_ticket(
            user_id=user2,
            subject="User 2 ticket",
            message="Message from user 2"
        )

        assert ticket1.user_id == user1
        assert ticket2.user_id == user2
        assert ticket1.ticket_id != ticket2.ticket_id
        assert len(repository.tickets) == 2
