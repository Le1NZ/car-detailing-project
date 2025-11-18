"""In-memory repository for ticket storage."""
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from app.models.ticket import Ticket, Message


class LocalTicketRepository:
    """
    Repository for managing tickets and messages in memory.

    Storage structure:
    - tickets: Dict[UUID, Ticket] - key is ticket_id
    - messages: Dict[UUID, List[Message]] - key is ticket_id
    """

    def __init__(self):
        """Initialize in-memory storage."""
        self.tickets: Dict[UUID, Ticket] = {}
        self.messages: Dict[UUID, List[Message]] = {}

    def create_ticket(
        self,
        user_id: UUID,
        subject: str,
        message: str,
        order_id: Optional[UUID] = None
    ) -> Ticket:
        """
        Create a new ticket in storage.

        Args:
            user_id: User identifier who creates the ticket
            subject: Ticket subject
            message: Initial message content
            order_id: Optional related order identifier

        Returns:
            Created Ticket object
        """
        ticket_id = uuid4()
        created_at = datetime.utcnow()

        ticket = Ticket(
            ticket_id=ticket_id,
            user_id=user_id,
            subject=subject,
            message=message,
            order_id=order_id,
            status="open",
            created_at=created_at
        )

        self.tickets[ticket_id] = ticket

        # Store the initial message
        initial_message = Message(
            message_id=uuid4(),
            ticket_id=ticket_id,
            author_id=str(user_id),
            message=message,
            created_at=created_at
        )
        self.messages[ticket_id] = [initial_message]

        return ticket

    def get_ticket_by_id(self, ticket_id: UUID) -> Optional[Ticket]:
        """
        Retrieve a ticket by its ID.

        Args:
            ticket_id: The unique identifier of the ticket

        Returns:
            Ticket object if found, None otherwise
        """
        return self.tickets.get(ticket_id)

    def is_ticket_closed(self, ticket_id: UUID) -> bool:
        """
        Check if a ticket is closed.

        Args:
            ticket_id: The unique identifier of the ticket

        Returns:
            True if ticket status is 'closed', False otherwise
        """
        ticket = self.get_ticket_by_id(ticket_id)
        if ticket is None:
            return False
        return ticket.status == "closed"

    def add_message(self, ticket_id: UUID, author_id: str, message_text: str) -> Message:
        """
        Add a message to a ticket.

        Args:
            ticket_id: The unique identifier of the ticket
            author_id: Identifier of the message author
            message_text: Message content

        Returns:
            Created Message object
        """
        created_at = datetime.utcnow()

        message = Message(
            message_id=uuid4(),
            ticket_id=ticket_id,
            author_id=author_id,
            message=message_text,
            created_at=created_at
        )

        if ticket_id not in self.messages:
            self.messages[ticket_id] = []

        self.messages[ticket_id].append(message)

        return message

    def get_messages_by_ticket(self, ticket_id: UUID) -> List[Message]:
        """
        Retrieve all messages for a specific ticket.

        Args:
            ticket_id: The unique identifier of the ticket

        Returns:
            List of Message objects for the ticket
        """
        return self.messages.get(ticket_id, [])


# Singleton instance
ticket_repository = LocalTicketRepository()
