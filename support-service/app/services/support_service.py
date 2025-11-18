"""Business logic for support ticket operations."""
from uuid import UUID
from typing import Optional
from fastapi import HTTPException, status

from app.repositories.local_ticket_repo import ticket_repository
from app.models.ticket import (
    CreateTicketRequest,
    TicketResponse,
    AddMessageRequest,
    MessageResponse,
    Ticket,
    Message
)
from app.config import settings


class SupportService:
    """Service layer for handling support ticket business logic."""

    def __init__(self):
        """Initialize the service with repository."""
        self.repository = ticket_repository

    def create_ticket(self, request: CreateTicketRequest, user_id: UUID) -> TicketResponse:
        """
        Create a new support ticket.

        Args:
            request: CreateTicketRequest with subject, message, and optional order_id
            user_id: UUID of the user creating the ticket

        Returns:
            TicketResponse with ticket_id, status, and created_at

        Raises:
            HTTPException: 422 if validation fails (handled by Pydantic)
        """
        # Create ticket in repository
        ticket = self.repository.create_ticket(
            user_id=user_id,
            subject=request.subject,
            message=request.message,
            order_id=request.order_id
        )

        return TicketResponse(
            ticket_id=ticket.ticket_id,
            status=ticket.status,
            created_at=ticket.created_at
        )

    def add_message_to_ticket(
        self,
        ticket_id: UUID,
        request: AddMessageRequest,
        author_id: str
    ) -> MessageResponse:
        """
        Add a message to an existing ticket.

        Args:
            ticket_id: UUID of the ticket
            request: AddMessageRequest with message content
            author_id: Identifier of the message author

        Returns:
            MessageResponse with message details

        Raises:
            HTTPException:
                - 404 if ticket not found
                - 409 if ticket is closed
                - 422 if message validation fails (handled by Pydantic)
        """
        # Check if ticket exists
        ticket = self.repository.get_ticket_by_id(ticket_id)
        if ticket is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket with ID {ticket_id} not found"
            )

        # Check if ticket is closed
        if self.repository.is_ticket_closed(ticket_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot add message to a closed ticket"
            )

        # Add the message
        message = self.repository.add_message(
            ticket_id=ticket_id,
            author_id=author_id,
            message_text=request.message
        )

        return MessageResponse(
            message_id=message.message_id,
            ticket_id=message.ticket_id,
            author_id=message.author_id,
            message=message.message,
            created_at=message.created_at
        )


# Singleton instance
support_service = SupportService()
