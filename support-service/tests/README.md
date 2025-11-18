# Support Service Test Suite

This directory contains comprehensive unit and integration tests for the support-service microservice.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures and pytest configuration
├── README.md                      # This file
├── unit/                          # Unit tests (isolated component testing)
│   ├── __init__.py
│   ├── test_models.py            # Pydantic model validation tests
│   ├── test_repository.py        # Repository layer tests (in-memory storage)
│   └── test_service.py           # Service layer business logic tests
└── integration/                   # Integration tests (API endpoint testing)
    ├── __init__.py
    └── test_endpoints.py         # Full API endpoint tests with TestClient
```

## Test Categories

### Unit Tests (`tests/unit/`)

**test_models.py** - Pydantic Model Validation Tests
- Tests for `CreateTicketRequest`, `TicketResponse`, `AddMessageRequest`, `MessageResponse`
- Tests for internal `Ticket` and `Message` models
- Validation tests for required fields, empty values, whitespace handling
- Tests for field validators and data type validation
- Edge cases and boundary conditions

**test_repository.py** - Repository Layer Tests
- Tests for `LocalTicketRepository` methods
- Tests for ticket creation, retrieval, and status checking
- Tests for message storage and retrieval
- Tests for data isolation between tickets
- Tests for UUID generation and timestamp handling
- Edge cases for non-existent tickets and empty repositories

**test_service.py** - Service Layer Business Logic Tests
- Tests for `SupportService` methods
- Tests for `create_ticket` business logic
- Tests for `add_message_to_ticket` with all error scenarios
- Tests for HTTP exception handling (404, 409)
- Tests for repository integration (mocked)
- Tests for edge cases and error propagation

### Integration Tests (`tests/integration/`)

**test_endpoints.py** - API Endpoint Integration Tests
- Full end-to-end tests using FastAPI TestClient
- Tests for POST `/api/support/tickets` (create ticket)
- Tests for POST `/api/support/tickets/{ticket_id}/messages` (add message)
- Tests for GET `/api/support/health` (health check)
- Tests for GET `/` (root endpoint)
- All HTTP status code scenarios (200, 201, 404, 409, 422)
- Tests for request validation and error responses
- Tests for complete ticket lifecycle workflows
- Tests for concurrent operations and data integrity

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_models.py

# Run specific test class
pytest tests/unit/test_models.py::TestCreateTicketRequest

# Run specific test function
pytest tests/unit/test_models.py::TestCreateTicketRequest::test_create_ticket_request_valid_data
```

### Run Tests with Coverage

```bash
# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser

# Generate XML coverage report (for CI/CD)
pytest --cov=app --cov-report=xml
```

### Run Tests with Markers

```bash
# Run only unit tests (if marked)
pytest -m unit

# Run only integration tests (if marked)
pytest -m integration

# Run only model tests
pytest -m models

# Skip slow tests
pytest -m "not slow"
```

### Run Tests with Different Verbosity

```bash
# Minimal output
pytest -q

# Verbose output (default in pytest.ini)
pytest -v

# Extra verbose with full output
pytest -vv

# Show local variables in tracebacks
pytest -l

# Show print statements
pytest -s
```

### Run Tests in Parallel (requires pytest-xdist)

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel using all CPU cores
pytest -n auto
```

## Test Coverage

The test suite aims for >90% code coverage with the following targets:

- **Models**: 100% coverage (all validation paths tested)
- **Repository**: 95%+ coverage (all CRUD operations and edge cases)
- **Service**: 95%+ coverage (all business logic and error handling)
- **Endpoints**: 90%+ coverage (all API routes and status codes)

Current coverage can be checked by running:
```bash
pytest --cov=app --cov-report=term-missing
```

## Test Fixtures

Shared fixtures are defined in `conftest.py`:

- `sample_user_id` - UUID for test user
- `sample_ticket_id` - UUID for test ticket
- `sample_order_id` - UUID for test order
- `sample_ticket` - Complete Ticket object
- `sample_message` - Complete Message object
- `clean_repository` - Fresh repository instance
- `reset_singleton_repository` - Auto-resets singleton repository
- `test_client` - FastAPI TestClient instance
- `sample_create_ticket_payload` - Sample API request payload
- `sample_add_message_payload` - Sample message request payload

## Writing New Tests

### Unit Test Example

```python
def test_new_feature(mock_repository):
    """Test description."""
    # Arrange
    service = SupportService()
    service.repository = mock_repository

    # Act
    result = service.some_method()

    # Assert
    assert result == expected_value
    mock_repository.some_method.assert_called_once()
```

### Integration Test Example

```python
def test_new_endpoint(client):
    """Test description."""
    # Arrange
    payload = {"key": "value"}

    # Act
    response = client.post("/api/endpoint", json=payload)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements-test.txt
    pytest --cov=app --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Test Isolation

All tests are completely isolated:
- No external dependencies (no real databases, no network calls)
- In-memory storage is reset before each test
- Mocked dependencies where appropriate
- No test pollution between test runs

## Troubleshooting

### Import Errors

If you see import errors, make sure you're running tests from the service root:
```bash
cd /Users/fr4lzen/Documents/мирэа/микросы/пр7/project/support-service/
pytest
```

### Repository Not Resetting

The `reset_singleton_repository` fixture automatically resets the repository before each test. If you see data pollution, check that this fixture is not being overridden.

### Coverage Not Working

Make sure pytest-cov is installed:
```bash
pip install pytest-cov
```

## Best Practices

1. **Naming**: Test functions should start with `test_` and be descriptive
2. **Structure**: Use Arrange-Act-Assert (AAA) pattern
3. **Isolation**: Each test should be independent
4. **Clarity**: Use descriptive assertions and error messages
5. **Coverage**: Aim for both positive and negative test cases
6. **Documentation**: Include docstrings explaining what each test validates

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [FastAPI testing documentation](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pydantic validation testing](https://docs.pydantic.dev/latest/usage/validation_errors/)
