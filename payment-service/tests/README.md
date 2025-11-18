# Payment Service Tests

Comprehensive test suite for the payment-service microservice.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── unit/                    # Unit tests (isolated component testing)
│   ├── test_payment_repository.py
│   ├── test_rabbitmq_publisher.py
│   ├── test_payment_service.py
│   └── test_models.py
└── integration/             # Integration tests (API endpoint testing)
    └── test_api_endpoints.py
```

## Installation

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Unit Tests Only

```bash
pytest tests/unit/
```

### Run Integration Tests Only

```bash
pytest tests/integration/
```

### Run Specific Test File

```bash
pytest tests/unit/test_payment_service.py
```

### Run Specific Test Class

```bash
pytest tests/unit/test_payment_service.py::TestPaymentServiceInitiatePayment
```

### Run Specific Test Method

```bash
pytest tests/unit/test_payment_service.py::TestPaymentServiceInitiatePayment::test_initiate_payment_success
```

### Run Tests with Verbose Output

```bash
pytest -v
```

### Run Tests with Coverage Report

```bash
pytest --cov=app --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Run Tests in Parallel

```bash
pytest -n auto
```

### Run Tests and Stop on First Failure

```bash
pytest -x
```

### Run Only Failed Tests from Last Run

```bash
pytest --lf
```

## Test Coverage

The test suite aims for >80% code coverage and includes:

### Unit Tests

1. **PaymentRepository Tests** (`test_payment_repository.py`)
   - Create payment operations
   - Retrieve payment by ID
   - Update payment status
   - Check order paid status
   - Get order data from mock storage
   - Edge cases and error scenarios

2. **RabbitMQPublisher Tests** (`test_rabbitmq_publisher.py`)
   - Connection management (connect/close)
   - Message publishing with correct format
   - Error handling (connection failures, publish errors)
   - Persistent message delivery mode
   - Edge cases (zero amount, large amounts, special characters)

3. **PaymentService Tests** (`test_payment_service.py`)
   - Payment initiation (happy path and errors)
   - Background payment processing
   - RabbitMQ event publishing
   - Payment status retrieval
   - Complete payment flow integration
   - Error handling and exception scenarios

4. **Pydantic Models Tests** (`test_models.py`)
   - Request/response model validation
   - Field requirements and defaults
   - Data serialization/deserialization
   - Model aliases for backward compatibility
   - Edge cases and boundary conditions

### Integration Tests

**API Endpoints Tests** (`test_api_endpoints.py`)
- POST /api/payments - Create payment
  - Success scenarios
  - Order not found (404)
  - Order already paid (409)
  - Validation errors (422)
- GET /api/payments/{payment_id} - Get payment status
  - Pending status
  - Succeeded status
  - Payment not found (404)
- GET /health - Health check
- Complete payment workflows
- CORS configuration
- API documentation endpoints
- Error handling and edge cases

## Test Patterns

### Unit Test Pattern

```python
def test_function_name_scenario(fixture1, fixture2):
    """Test description of what is being tested."""
    # Arrange - Set up test data and mocks

    # Act - Execute the code under test

    # Assert - Verify expected outcomes
```

### Integration Test Pattern

```python
def test_endpoint_scenario(test_client: TestClient):
    """Test API endpoint behavior."""
    # Arrange - Prepare request data

    # Act - Make HTTP request
    response = test_client.post("/api/endpoint", json=data)

    # Assert - Verify response
    assert response.status_code == expected_status
    assert response.json()["field"] == expected_value
```

## Mocking Strategy

### RabbitMQ Mocking

RabbitMQ is mocked in all tests to avoid external dependencies:

```python
with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
    mock_publisher.publish_payment_success = AsyncMock()
    # Test code
```

### Repository Mocking

Repository is reset before each test using the `reset_singletons` fixture:

```python
@pytest.fixture(autouse=True)
def reset_singletons():
    payment_repository.payments_storage = []
    yield
    payment_repository.payments_storage = []
```

## Fixtures

Common fixtures available in `conftest.py`:

- `payment_repository` - Clean PaymentRepository instance
- `payment_service` - PaymentService with clean repository
- `mock_rabbitmq_publisher` - Mocked RabbitMQ publisher
- `sample_order_data` - Test order data
- `sample_payment_data` - Test payment data
- `test_client` - FastAPI TestClient
- `reset_singletons` - Auto-fixture to reset state

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

## Test Categories

Tests can be run by category using markers:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only async tests
pytest -m asyncio

# Exclude slow tests
pytest -m "not slow"
```

## Debugging Tests

### Run with Python Debugger

```bash
pytest --pdb
```

### Print Output During Tests

```bash
pytest -s
```

### Show Local Variables on Failure

```bash
pytest --showlocals
```

## Best Practices

1. **Test Isolation**: Each test should be independent and not rely on other tests
2. **Clear Naming**: Test names should describe what is being tested and expected outcome
3. **AAA Pattern**: Arrange, Act, Assert - structure tests clearly
4. **Mock External Dependencies**: Always mock RabbitMQ, external APIs, databases
5. **Comprehensive Coverage**: Test both happy paths and error scenarios
6. **Fast Execution**: Unit tests should run quickly (<1s each)
7. **Deterministic**: Tests should produce the same results every time

## Troubleshooting

### Tests Failing Due to Import Errors

Ensure you're running tests from the project root:
```bash
cd /path/to/payment-service
pytest
```

### Async Tests Not Running

Ensure `pytest-asyncio` is installed:
```bash
pip install pytest-asyncio
```

### Coverage Not Generated

Check that the `--cov` flag is set and `pytest-cov` is installed:
```bash
pip install pytest-cov
pytest --cov=app
```

## Contributing

When adding new features:

1. Write unit tests for new components
2. Write integration tests for new API endpoints
3. Ensure all tests pass: `pytest`
4. Verify coverage remains >80%: `pytest --cov=app`
5. Update this README if adding new test patterns

## Test Metrics

Run this command to see test statistics:

```bash
pytest --collect-only
```

Expected test count:
- Unit tests: ~100+ tests
- Integration tests: ~30+ tests
- Total: ~130+ tests

Expected coverage: >80% of application code
