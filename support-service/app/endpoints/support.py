"""Support ticket API endpoints."""
from fastapi import APIRouter, status, Depends
from typing import Dict
from uuid import UUID

from app.models.ticket import (
    CreateTicketRequest,
    TicketResponse,
    AddMessageRequest,
    MessageResponse,
)
from app.services.support_service import support_service
from app.config import settings
from app.auth import get_current_user_id


router = APIRouter(prefix="/api/support", tags=["support"])


@router.post(
    "/tickets",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new support ticket",
    description="Create a new support ticket with subject and initial message"
)
async def create_ticket(
    request: CreateTicketRequest,
    user_id: UUID = Depends(get_current_user_id)
) -> TicketResponse:
    """
    Create a new support ticket.

    Request body:
    - subject: Ticket subject (required, min_length=1)
    - message: Initial message content (required, min_length=1)
    - order_id: Related order UUID (optional)

    Returns:
    - ticket_id: Unique ticket UUID
    - status: Current ticket status (always "open" for new tickets)
    - created_at: Ticket creation timestamp

    Errors:
    - 401 Unauthorized: Missing or invalid authorization token
    - 422 Unprocessable Entity: Missing or empty required fields
    """
    return support_service.create_ticket(request, user_id)


@router.post(
    "/tickets/{ticket_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a message to a ticket",
    description="Add a reply message to an existing support ticket"
)
async def add_message_to_ticket(
    ticket_id: UUID,
    request: AddMessageRequest,
    user_id: UUID = Depends(get_current_user_id)
) -> MessageResponse:
    """
    Add a message to an existing ticket.

    Path parameters:
    - ticket_id: The unique UUID of the ticket

    Request body:
    - message: Message content (required, min_length=1)

    Returns:
    - message_id: Unique message UUID
    - ticket_id: Related ticket UUID
    - author_id: Message author identifier (from JWT token)
    - message: Message content
    - created_at: Message creation timestamp

    Errors:
    - 401 Unauthorized: Missing or invalid authorization token
    - 404 Not Found: Ticket not found
    - 409 Conflict: Ticket is closed (cannot add messages)
    - 422 Unprocessable Entity: Empty message field
    """
    # Use user_id from JWT token as author
    author_id = str(user_id)

    return support_service.add_message_to_ticket(ticket_id, request, author_id)


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Check if the service is running"
)
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns:
    - status: Service status
    - service: Service name
    """
    return {"status": "healthy", "service": settings.service_name}
