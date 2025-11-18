# Order Service - Testing Documentation

## Overview

This document provides comprehensive information about the test suite for the order-service microservice.

## Test Structure

```
order-service/
├── tests/
│   ├── conftest.py                      # Shared fixtures and test configuration
│   ├── unit/                            # Unit tests (isolated component tests)
│   │   ├── __init__.py
│   │   ├── test_models.py              # Pydantic model validation tests
│   │   ├── test_repository.py          # Repository layer tests
│   │   ├── test_car_client.py          # HTTP client tests (with mocking)
│   │   └── test_order_service.py       # Business logic tests
│   └── integration/                     # Integration tests (API endpoint tests)
│       ├── __init__.py
│       └── test_api_endpoints.py       # FastAPI endpoint tests
├── pytest.ini                           # Pytest configuration
├── requirements-test.txt                # Test dependencies
└── run_tests.sh                         # Test runner script
```

## Test Coverage

### Unit Tests

#### 1. Model Tests (`tests/unit/test_models.py`)
**Test Count: 35+ tests**

Tests for Pydantic models covering:
- **CreateOrderRequest**: UUID validation, datetime validation, description length constraints
- **UpdateStatusRequest**: Valid status literals, invalid status rejection
- **ReviewRequest**: Rating range validation (1-5), comment length constraints
- **OrderResponse**: Response serialization and UUID handling
- **ReviewResponse**: Response serialization
- **ErrorResponse**: Error message formatting
- **Order class**: Initialization and `to_response()` conversion
- **Review class**: Initialization and `to_response()` conversion

**Key Test Scenarios:**
- Valid data creates models successfully
- Invalid UUIDs raise ValidationError
- Empty or too-long strings are rejected
- Rating boundaries (0, 1, 5, 6) are enforced
- Missing required fields raise ValidationError

---

#### 2. Repository Tests (`tests/unit/test_repository.py`)
**Test Count: 20+ tests**

Tests for LocalOrderRepository covering:
- **Order Operations**: create_order, get_order_by_id, update_order_status
- **Review Operations**: create_review, has_review, get_review_by_order_id
- **Data Persistence**: Multiple orders, order-review associations

**Key Test Scenarios:**
- Create order generates unique UUID and sets initial status to "created"
- Retrieve existing order returns correct data
- Retrieve non-existent order returns None
- Update order status modifies and persists state
- Create review associates it with order
- has_review correctly identifies reviewed orders
- Multiple orders coexist without conflicts

---

#### 3. Car Client Tests (`tests/unit/test_car_client.py`)
**Test Count: 15+ tests**

Tests for CarServiceClient with HTTP mocking:
- **verify_car_exists()**: Success (200), Not Found (404), Server Error (500)
- **Error Handling**: Timeout, Connection Error, Generic RequestError, Unexpected Exception
- **Configuration**: URL construction, timeout usage

**Key Test Scenarios:**
- 200 response returns True
- 404 response returns False
- 500 response returns False
- TimeoutException returns False
- ConnectError returns False
- RequestError returns False
- Generic Exception returns False
- Correct URL construction with base_url
- Timeout parameter passed to httpx.AsyncClient

**Mocking Strategy:**
```python
with patch('httpx.AsyncClient') as mock_client_class:
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client_class.return_value.__aenter__.return_value = mock_client
```

---

#### 4. Order Service Tests (`tests/unit/test_order_service.py`)
**Test Count: 25+ tests**

Tests for OrderService business logic:
- **create_order()**: Success path, car not found, car-service unavailable
- **update_order_status()**: Valid transitions, invalid transitions, terminal state
- **add_review()**: Success, order not found, duplicate review
- **Status Transitions**: Validation logic, state machine correctness

**Key Test Scenarios:**

**Create Order:**
- Car exists → order created with status "created"
- Car not found → HTTPException 404
- Car-service returns False → HTTPException 404

**Update Status:**
- created → in_progress ✓
- in_progress → work_completed ✓
- work_completed → car_issued ✓
- created → work_completed ✗ (HTTPException 400)
- car_issued → any status ✗ (terminal state)
- Non-existent order → HTTPException 404

**Add Review:**
- Order exists + no review → review created
- Order not found → HTTPException 404
- Review exists → HTTPException 409

**Mocking Strategy:**
```python
# Mock repository
mock_repository.get_order_by_id.return_value = sample_order
mock_repository.update_order_status.return_value = updated_order

# Mock car client
mock_car_client.verify_car_exists.return_value = True

# Inject mocks
service = OrderService()
service.repository = mock_repository
service.car_client = mock_car_client
```

---

### Integration Tests

#### 5. API Endpoint Tests (`tests/integration/test_api_endpoints.py`)
**Test Count: 30+ tests**

Tests for FastAPI endpoints using TestClient:
- **Health Endpoints**: /health, /
- **POST /api/orders**: Success, car not found, validation errors
- **PATCH /api/orders/{id}/status**: Valid transitions, invalid transitions, not found
- **POST /api/orders/review**: Success, duplicate, validation errors
- **End-to-End Workflows**: Complete order lifecycle

**Key Test Scenarios:**

**Health Checks:**
- GET /health returns 200 with status "healthy"
- GET / returns 200 with service info

**Create Order:**
- Valid request → 201 with order_id
- Car not found → 404
- Invalid UUID → 422
- Missing fields → 422
- Empty description → 422
- Description too long → 422

**Update Status:**
- Valid transition → 200 with updated status
- Invalid transition → 400
- Order not found → 404
- Invalid status value → 422
- Full workflow (created → in_progress → work_completed → car_issued) → All 200

**Add Review:**
- Valid review → 201 with review_id
- Order not found → 404
- Duplicate review → 409
- Invalid rating (0, 6) → 422
- Empty comment → 422
- Missing fields → 422

**End-to-End:**
- Complete workflow: Create order → Update to in_progress → Update to work_completed → Add review → Update to car_issued

**Mocking Strategy:**
```python
@patch('app.services.car_client.car_client.verify_car_exists')
def test_create_order_success(mock_verify_car, test_client, clean_repository):
    mock_verify_car.return_value = True

    with patch('app.services.order_service.order_repository', clean_repository):
        response = test_client.post("/api/orders", json={...})
```

---

## Running Tests

### Method 1: Using Test Runner Script (Recommended)

```bash
cd /Users/fr4lzen/Documents/мирэа/микросы/пр7/project/order-service
./run_tests.sh
```

This script will:
1. Create a virtual environment (if not exists)
2. Install test dependencies
3. Run the complete test suite
4. Generate coverage reports

### Method 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_models.py

# Run specific test class
pytest tests/unit/test_models.py::TestCreateOrderRequest

# Run specific test
pytest tests/unit/test_models.py::TestCreateOrderRequest::test_valid_create_order_request

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

### Method 3: Using Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run slow tests
pytest -m slow
```

---

## Coverage Reports

### Viewing Coverage

After running tests, coverage reports are generated in multiple formats:

1. **Terminal Output**: Shows missing lines directly in the terminal
2. **HTML Report**: `htmlcov/index.html` - Interactive browsable report
3. **XML Report**: `coverage.xml` - For CI/CD integration

```bash
# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage Target

**Minimum Coverage: 85%**

The test suite is configured to fail if coverage drops below 85%.

### Coverage Configuration

Coverage settings are defined in `pytest.ini`:

```ini
[coverage:run]
source = app
omit =
    */tests/*
    */test_*.py
    */__pycache__/*
    */site-packages/*
    */__init__.py
```

---

## Test Dependencies

### Core Testing Framework
- **pytest** (7.4.3): Test framework
- **pytest-asyncio** (0.21.1): Async test support
- **pytest-cov** (4.1.0): Coverage plugin
- **pytest-mock** (3.12.0): Mocking utilities

### HTTP Testing
- **httpx** (0.25.2): Async HTTP client (also used in production)

### Coverage
- **coverage** (7.3.2): Code coverage measurement

---

## Fixtures

### Shared Fixtures (`tests/conftest.py`)

**Test Data:**
- `test_car_id`: UUID for test car
- `test_order_id`: UUID for test order
- `test_review_id`: UUID for test review
- `test_datetime`: Standard datetime for tests
- `sample_order_data`: Complete order request data
- `sample_review_data`: Complete review request data
- `sample_order`: Pre-created Order instance
- `sample_review`: Pre-created Review instance

**Mock Objects:**
- `mock_repository`: Mock LocalOrderRepository with AsyncMock methods
- `mock_car_client`: Mock CarServiceClient
- `fresh_repository`: Fresh LocalOrderRepository instance for each test

**Usage Example:**
```python
def test_create_order(sample_order_data, mock_repository, mock_car_client):
    # Use fixtures in test
    pass
```

---

## Best Practices

### 1. Test Isolation
- Each test is independent and does not rely on other tests
- Fresh repository instances are created for each test
- Mocks are configured per test

### 2. Arrange-Act-Assert Pattern
```python
def test_example():
    # Arrange: Set up test data and mocks
    mock_repository.get_order_by_id.return_value = sample_order

    # Act: Execute the code under test
    result = await service.update_order_status(order_id, "in_progress")

    # Assert: Verify the results
    assert result.status == "in_progress"
    mock_repository.update_order_status.assert_called_once()
```

### 3. Descriptive Test Names
Test names clearly describe what is being tested and the expected outcome:
- `test_create_order_success`
- `test_create_order_car_not_found`
- `test_update_status_invalid_transition`

### 4. Comprehensive Error Testing
Every error path is tested:
- 404 Not Found
- 400 Bad Request
- 409 Conflict
- 422 Validation Error
- 503 Service Unavailable

### 5. Mock External Dependencies
All external dependencies are mocked:
- HTTP calls to car-service
- Repository operations (in service tests)
- Time-dependent functions

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt

    - name: Run tests
      run: |
        pytest

    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

---

## Troubleshooting

### Common Issues

**Issue: `ImportError: No module named 'app'`**
```bash
# Solution: Ensure pytest is run from project root
cd /Users/fr4lzen/Documents/мирэа/микросы/пр7/project/order-service
pytest
```

**Issue: Async tests not running**
```bash
# Solution: Install pytest-asyncio
pip install pytest-asyncio

# Or ensure pytest.ini has:
asyncio_mode = auto
```

**Issue: Coverage not generated**
```bash
# Solution: Install pytest-cov
pip install pytest-cov

# Run with coverage explicitly
pytest --cov=app
```

**Issue: Tests fail with "externally-managed-environment"**
```bash
# Solution: Use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-test.txt
pytest
```

---

## Test Statistics

### Summary

| Category | Test Files | Test Count | Coverage Target |
|----------|-----------|-----------|-----------------|
| Unit Tests | 4 | 95+ | >85% |
| Integration Tests | 1 | 30+ | >85% |
| **Total** | **5** | **125+** | **>85%** |

### Test Distribution

```
Unit Tests (95+):
├── test_models.py (35 tests)
│   ├── CreateOrderRequest: 8 tests
│   ├── UpdateStatusRequest: 5 tests
│   ├── ReviewRequest: 8 tests
│   ├── OrderResponse: 2 tests
│   ├── ReviewResponse: 1 test
│   ├── ErrorResponse: 2 tests
│   ├── Order class: 2 tests
│   └── Review class: 2 tests
│
├── test_repository.py (20 tests)
│   ├── Order operations: 9 tests
│   ├── Review operations: 9 tests
│   └── Data persistence: 2 tests
│
├── test_car_client.py (15 tests)
│   ├── verify_car_exists: 10 tests
│   ├── get_car_details: 4 tests
│   └── Configuration: 2 tests
│
└── test_order_service.py (25 tests)
    ├── create_order: 3 tests
    ├── update_order_status: 6 tests
    ├── add_review: 5 tests
    ├── Status transitions: 7 tests
    └── Initialization: 2 tests

Integration Tests (30+):
└── test_api_endpoints.py (30+ tests)
    ├── Health endpoints: 2 tests
    ├── Create order: 6 tests
    ├── Update status: 6 tests
    ├── Add review: 7 tests
    └── End-to-end workflows: 1 test
```

---

## Maintenance

### Adding New Tests

When adding new functionality:

1. **Add unit tests** for isolated component logic
2. **Add integration tests** for API endpoints
3. **Update fixtures** if new test data is needed
4. **Update this documentation** with new test descriptions

### Test Naming Convention

```python
# Unit tests
def test_<method_name>_<scenario>()
def test_create_order_success()
def test_create_order_car_not_found()

# Integration tests
def test_<endpoint>_<scenario>()
def test_create_order_endpoint_success()
def test_create_order_endpoint_validation_error()
```

---

## Additional Resources

- **FastAPI Testing**: https://fastapi.tiangolo.com/tutorial/testing/
- **Pytest Documentation**: https://docs.pytest.org/
- **Pytest-Asyncio**: https://pytest-asyncio.readthedocs.io/
- **Coverage.py**: https://coverage.readthedocs.io/

---

## Contact

For questions or issues with the test suite, please refer to the main README.md or contact the development team.

---

**Last Updated**: 2025-11-18
**Test Framework Version**: pytest 7.4.3
**Python Version**: 3.11+
