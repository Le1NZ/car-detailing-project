"""Integration tests for support ticket API endpoints."""
import pytest
from datetime import datetime
from uuid import UUID, uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.local_ticket_repo import LocalTicketRepository
from app.services.support_service import SupportService


@pytest.fixture(autouse=True)
def reset_repository():
    """Reset repository state before each test."""
    # Create fresh repository for each test
    from app.repositories.local_ticket_repo import ticket_repository
    ticket_repository.tickets.clear()
    ticket_repository.messages.clear()
    yield
    # Cleanup after test
    ticket_repository.tickets.clear()
    ticket_repository.messages.clear()


class TestRootEndpoint:
    """Test suite for root endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns service information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "support-service"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"


class TestHealthEndpoint:
    """Test suite for health check endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint returns healthy status."""
        response = client.get("/api/support/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "support-service"


class TestCreateTicketEndpoint:
    """Test suite for POST /api/support/tickets endpoint."""

    def test_create_ticket_success_with_all_fields(self, client):
        """Test successful ticket creation with all fields."""
        order_id = str(uuid4())
        payload = {
            "subject": "Unable to access my account",
            "message": "I've been trying to log in but keep getting an error",
            "order_id": order_id
        }

        response = client.post("/api/support/tickets", json=payload)

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "ticket_id" in data
        assert "status" in data
        assert "created_at" in data

        # Verify response values
        assert UUID(data["ticket_id"])  # Valid UUID
        assert data["status"] == "open"
        assert datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))

    def test_create_ticket_success_without_order_id(self, client):
        """Test successful ticket creation without optional order_id."""
        payload = {
            "subject": "Question about pricing",
            "message": "How much does the premium plan cost?"
        }

        response = client.post("/api/support/tickets", json=payload)

        assert response.status_code == 201
        data = response.json()

        assert "ticket_id" in data
        assert UUID(data["ticket_id"])
        assert data["status"] == "open"

    def test_create_ticket_missing_subject(self, client):
        """Test ticket creation fails when subject is missing."""
        payload = {
            "message": "This is a message without a subject"
        }

        response = client.post("/api/support/tickets", json=payload)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_ticket_missing_message(self, client):
        """Test ticket creation fails when message is missing."""
        payload = {
            "subject": "This is a subject without message"
        }

        response = client.post("/api/support/tickets", json=payload)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_ticket_empty_subject(self, client):
        """Test ticket creation fails with empty subject."""
        payload = {
            "subject": "",
            "message": "This message has an empty subject"
        }

        response = client.post("/api/support/tickets", json=payload)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_ticket_empty_message(self, client):
        """Test ticket creation fails with empty message."""
        payload = {
            "subject": "Subject here",
            "message": ""
        }

        response = client.post("/api/support/tickets", json=payload)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_ticket_whitespace_only_subject(self, client):
        """Test ticket creation fails with whitespace-only subject."""
        payload = {
            "subject": "   ",
            "message": "Valid message"
        }

        response = client.post("/api/support/tickets", json=payload)

        assert response.status_code == 422

    def test_create_ticket_whitespace_only_message(self, client):
        """Test ticket creation fails with whitespace-only message."""
        payload = {
            "subject": "Valid subject",
            "message": "   "
        }

        response = client.post("/api/support/tickets", json=payload)

        assert response.status_code == 422

    def test_create_ticket_strips_whitespace(self, client):
        """Test that ticket creation strips leading/trailing whitespace."""
        payload = {
            "subject": "  Test Subject  ",
            "message": "  Test Message  "
        }

        response = client.post("/api/support/tickets", json=payload)

        assert response.status_code == 201

        # Verify in repository that whitespace was stripped
        from app.repositories.local_ticket_repo import ticket_repository
        ticket_id = UUID(response.json()["ticket_id"])
        ticket = ticket_repository.get_ticket_by_id(ticket_id)
        assert ticket.subject == "Test Subject"
        assert ticket.message == "Test Message"

    def test_create_ticket_invalid_order_id_format(self, client):
        """Test ticket creation fails with invalid order_id format."""
        payload = {
            "subject": "Test Subject",
            "message": "Test Message",
            "order_id": "not-a-valid-uuid"
        }

        response = client.post("/api/support/tickets", json=payload)

        assert response.status_code == 422

    def test_create_ticket_with_special_characters(self, client):
        """Test ticket creation with special characters."""
        payload = {
            "subject": "Bug: API returns 500 @endpoint/test",
            "message": "Error: 'Invalid token' - need help ASAP! <urgent>"
        }

        response = client.post("/api/support/tickets", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert UUID(data["ticket_id"])

    def test_create_ticket_with_long_content(self, client):
        """Test ticket creation with very long subject and message."""
        long_subject = "A" * 500
        long_message = "B" * 5000

        payload = {
            "subject": long_subject,
            "message": long_message
        }

        response = client.post("/api/support/tickets", json=payload)

        assert response.status_code == 201

    def test_create_multiple_tickets_generates_unique_ids(self, client):
        """Test that creating multiple tickets generates unique IDs."""
        payload1 = {
            "subject": "First ticket",
            "message": "First message"
        }

        payload2 = {
            "subject": "Second ticket",
            "message": "Second message"
        }

        response1 = client.post("/api/support/tickets", json=payload1)
        response2 = client.post("/api/support/tickets", json=payload2)

        assert response1.status_code == 201
        assert response2.status_code == 201

        ticket_id1 = response1.json()["ticket_id"]
        ticket_id2 = response2.json()["ticket_id"]

        assert ticket_id1 != ticket_id2

    def test_create_ticket_invalid_json(self, client):
        """Test ticket creation fails with invalid JSON."""
        response = client.post(
            "/api/support/tickets",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422


class TestAddMessageToTicketEndpoint:
    """Test suite for POST /api/support/tickets/{ticket_id}/messages endpoint."""

    def test_add_message_success(self, client):
        """Test successfully adding a message to an existing ticket."""
        # First create a ticket
        create_payload = {
            "subject": "Need help",
            "message": "I have a problem"
        }
        create_response = client.post("/api/support/tickets", json=create_payload)
        ticket_id = create_response.json()["ticket_id"]

        # Add a message to the ticket
        message_payload = {
            "message": "Can you provide more details about your issue?"
        }

        response = client.post(
            f"/api/support/tickets/{ticket_id}/messages",
            json=message_payload
        )

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "message_id" in data
        assert "ticket_id" in data
        assert "author_id" in data
        assert "message" in data
        assert "created_at" in data

        # Verify response values
        assert UUID(data["message_id"])
        assert data["ticket_id"] == ticket_id
        # After auth implementation, author_id is now a UUID from JWT token
        assert UUID(data["author_id"])  # Verify it's a valid UUID
        assert data["message"] == message_payload["message"]
        assert datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))

    def test_add_message_ticket_not_found(self, client):
        """Test adding message to non-existent ticket returns 404."""
        random_ticket_id = str(uuid4())
        message_payload = {
            "message": "This ticket doesn't exist"
        }

        response = client.post(
            f"/api/support/tickets/{random_ticket_id}/messages",
            json=message_payload
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_add_message_to_closed_ticket(self, client):
        """Test adding message to closed ticket returns 409."""
        # Create a ticket
        create_payload = {
            "subject": "Test",
            "message": "Test message"
        }
        create_response = client.post("/api/support/tickets", json=create_payload)
        ticket_id = UUID(create_response.json()["ticket_id"])

        # Manually close the ticket
        from app.repositories.local_ticket_repo import ticket_repository
        ticket = ticket_repository.get_ticket_by_id(ticket_id)
        ticket.status = "closed"
        ticket_repository.tickets[ticket_id] = ticket

        # Try to add a message
        message_payload = {
            "message": "This should fail"
        }

        response = client.post(
            f"/api/support/tickets/{ticket_id}/messages",
            json=message_payload
        )

        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert "closed" in data["detail"].lower()

    def test_add_message_missing_message_field(self, client):
        """Test adding message fails when message field is missing."""
        # Create a ticket
        create_payload = {
            "subject": "Test",
            "message": "Test message"
        }
        create_response = client.post("/api/support/tickets", json=create_payload)
        ticket_id = create_response.json()["ticket_id"]

        # Try to add message without message field
        response = client.post(
            f"/api/support/tickets/{ticket_id}/messages",
            json={}
        )

        assert response.status_code == 422

    def test_add_message_empty_message(self, client):
        """Test adding message fails with empty message."""
        # Create a ticket
        create_payload = {
            "subject": "Test",
            "message": "Test message"
        }
        create_response = client.post("/api/support/tickets", json=create_payload)
        ticket_id = create_response.json()["ticket_id"]

        # Try to add empty message
        message_payload = {
            "message": ""
        }

        response = client.post(
            f"/api/support/tickets/{ticket_id}/messages",
            json=message_payload
        )

        assert response.status_code == 422

    def test_add_message_whitespace_only(self, client):
        """Test adding message fails with whitespace-only message."""
        # Create a ticket
        create_payload = {
            "subject": "Test",
            "message": "Test message"
        }
        create_response = client.post("/api/support/tickets", json=create_payload)
        ticket_id = create_response.json()["ticket_id"]

        # Try to add whitespace-only message
        message_payload = {
            "message": "   "
        }

        response = client.post(
            f"/api/support/tickets/{ticket_id}/messages",
            json=message_payload
        )

        assert response.status_code == 422

    def test_add_message_strips_whitespace(self, client):
        """Test that message content is stripped of leading/trailing whitespace."""
        # Create a ticket
        create_payload = {
            "subject": "Test",
            "message": "Test message"
        }
        create_response = client.post("/api/support/tickets", json=create_payload)
        ticket_id = create_response.json()["ticket_id"]

        # Add message with whitespace
        message_payload = {
            "message": "  This message has whitespace  "
        }

        response = client.post(
            f"/api/support/tickets/{ticket_id}/messages",
            json=message_payload
        )

        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "This message has whitespace"

    def test_add_message_invalid_ticket_id_format(self, client):
        """Test adding message fails with invalid ticket ID format."""
        message_payload = {
            "message": "Test message"
        }

        response = client.post(
            "/api/support/tickets/not-a-uuid/messages",
            json=message_payload
        )

        assert response.status_code == 422

    def test_add_multiple_messages_to_same_ticket(self, client):
        """Test adding multiple messages to the same ticket."""
        # Create a ticket
        create_payload = {
            "subject": "Test",
            "message": "Initial message"
        }
        create_response = client.post("/api/support/tickets", json=create_payload)
        ticket_id = create_response.json()["ticket_id"]

        # Add multiple messages
        messages = [
            "First reply",
            "Second reply",
            "Third reply"
        ]

        message_ids = []
        for msg in messages:
            message_payload = {"message": msg}
            response = client.post(
                f"/api/support/tickets/{ticket_id}/messages",
                json=message_payload
            )
            assert response.status_code == 201
            message_ids.append(response.json()["message_id"])

        # Verify all message IDs are unique
        assert len(message_ids) == len(set(message_ids))

    def test_add_message_with_special_characters(self, client):
        """Test adding message with special characters."""
        # Create a ticket
        create_payload = {
            "subject": "Test",
            "message": "Test message"
        }
        create_response = client.post("/api/support/tickets", json=create_payload)
        ticket_id = create_response.json()["ticket_id"]

        # Add message with special characters
        message_payload = {
            "message": "Here's the fix: run `sudo apt update && apt upgrade` @ terminal <script>test</script>"
        }

        response = client.post(
            f"/api/support/tickets/{ticket_id}/messages",
            json=message_payload
        )

        assert response.status_code == 201
        data = response.json()
        assert message_payload["message"] in data["message"]

    def test_add_message_with_long_content(self, client):
        """Test adding very long message."""
        # Create a ticket
        create_payload = {
            "subject": "Test",
            "message": "Test message"
        }
        create_response = client.post("/api/support/tickets", json=create_payload)
        ticket_id = create_response.json()["ticket_id"]

        # Add very long message
        long_message = "A" * 10000
        message_payload = {
            "message": long_message
        }

        response = client.post(
            f"/api/support/tickets/{ticket_id}/messages",
            json=message_payload
        )

        assert response.status_code == 201

    def test_add_message_to_in_progress_ticket(self, client):
        """Test adding message to ticket with in_progress status."""
        # Create a ticket
        create_payload = {
            "subject": "Test",
            "message": "Test message"
        }
        create_response = client.post("/api/support/tickets", json=create_payload)
        ticket_id = UUID(create_response.json()["ticket_id"])

        # Change status to in_progress
        from app.repositories.local_ticket_repo import ticket_repository
        ticket = ticket_repository.get_ticket_by_id(ticket_id)
        ticket.status = "in_progress"
        ticket_repository.tickets[ticket_id] = ticket

        # Add message
        message_payload = {
            "message": "This should succeed"
        }

        response = client.post(
            f"/api/support/tickets/{ticket_id}/messages",
            json=message_payload
        )

        assert response.status_code == 201


class TestEndToEndScenarios:
    """Test suite for end-to-end scenarios."""

    def test_complete_ticket_lifecycle(self, client):
        """Test complete ticket lifecycle from creation to multiple messages."""
        # Step 1: Create ticket
        create_payload = {
            "subject": "Account Issue",
            "message": "I cannot log into my account",
            "order_id": str(uuid4())
        }
        create_response = client.post("/api/support/tickets", json=create_payload)
        assert create_response.status_code == 201
        ticket_id = create_response.json()["ticket_id"]

        # Step 2: Support agent replies
        reply1_payload = {
            "message": "Can you tell me your email address?"
        }
        reply1_response = client.post(
            f"/api/support/tickets/{ticket_id}/messages",
            json=reply1_payload
        )
        assert reply1_response.status_code == 201

        # Step 3: User replies
        reply2_payload = {
            "message": "My email is user@example.com"
        }
        reply2_response = client.post(
            f"/api/support/tickets/{ticket_id}/messages",
            json=reply2_payload
        )
        assert reply2_response.status_code == 201

        # Step 4: Support agent provides solution
        reply3_payload = {
            "message": "I've reset your password. Please check your email."
        }
        reply3_response = client.post(
            f"/api/support/tickets/{ticket_id}/messages",
            json=reply3_payload
        )
        assert reply3_response.status_code == 201

        # Verify all messages are stored
        from app.repositories.local_ticket_repo import ticket_repository
        messages = ticket_repository.get_messages_by_ticket(UUID(ticket_id))
        assert len(messages) == 4  # Initial + 3 replies

    def test_concurrent_ticket_creation(self, client):
        """Test creating multiple tickets concurrently."""
        tickets = []
        for i in range(10):
            payload = {
                "subject": f"Ticket {i}",
                "message": f"Message {i}"
            }
            response = client.post("/api/support/tickets", json=payload)
            assert response.status_code == 201
            tickets.append(response.json()["ticket_id"])

        # Verify all tickets have unique IDs
        assert len(tickets) == len(set(tickets))

    def test_error_handling_with_invalid_data_types(self, client):
        """Test API error handling with various invalid data types."""
        # Integer instead of string for subject
        response = client.post("/api/support/tickets", json={
            "subject": 12345,
            "message": "Valid message"
        })
        assert response.status_code == 422

        # List instead of string for message
        response = client.post("/api/support/tickets", json={
            "subject": "Valid subject",
            "message": ["list", "of", "strings"]
        })
        assert response.status_code == 422

        # Boolean instead of UUID for order_id
        response = client.post("/api/support/tickets", json={
            "subject": "Valid subject",
            "message": "Valid message",
            "order_id": True
        })
        assert response.status_code == 422
