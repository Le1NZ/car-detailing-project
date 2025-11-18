"""Pydantic models for ticket-related API operations."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


# API Request/Response Models
class CreateTicketRequest(BaseModel):
    """Request model for creating a new support ticket."""

    subject: str = Field(..., min_length=1, description="Subject of the ticket")
    message: str = Field(..., min_length=1, description="Initial message content")
    order_id: Optional[UUID] = Field(None, description="Related order ID (optional)")

    @field_validator("subject", "message")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate that required fields are not empty or whitespace."""
        if not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip()


class TicketResponse(BaseModel):
    """Response model for ticket creation."""

    ticket_id: UUID = Field(..., description="Unique ticket identifier")
    status: str = Field(..., description="Current ticket status")
    created_at: datetime = Field(..., description="Ticket creation timestamp")


class AddMessageRequest(BaseModel):
    """Request model for adding a message to a ticket."""

    message: str = Field(..., min_length=1, description="Message content")

    @field_validator("message")
    @classmethod
    def validate_message_not_empty(cls, v: str) -> str:
        """Validate that message is not empty or whitespace."""
        if not v.strip():
            raise ValueError("Message cannot be empty or whitespace")
        return v.strip()


class MessageResponse(BaseModel):
    """Response model for adding a message."""

    message_id: UUID = Field(..., description="Unique message identifier")
    ticket_id: UUID = Field(..., description="Related ticket identifier")
    author_id: str = Field(..., description="Message author identifier")
    message: str = Field(..., description="Message content")
    created_at: datetime = Field(..., description="Message creation timestamp")


# Internal Storage Models
class Ticket(BaseModel):
    """Internal model for ticket storage."""

    ticket_id: UUID
    user_id: UUID
    subject: str
    message: str
    order_id: Optional[UUID] = None
    status: str  # open, in_progress, closed
    created_at: datetime


class Message(BaseModel):
    """Internal model for message storage."""

    message_id: UUID
    ticket_id: UUID
    author_id: str
    message: str
    created_at: datetime
