# User Service Tests

Comprehensive test suite for the user-service microservice.

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures for all tests
├── unit/                       # Unit tests (isolated, mocked dependencies)
│   ├── test_utils.py          # Password hashing, JWT utilities
│   ├── test_models.py         # Pydantic model validation
│   ├── test_repository.py     # UserRepository database operations
│   └── test_service.py        # UserService business logic
└── integration/               # Integration tests (with database)
    └── test_api_endpoints.py  # API endpoint tests (FastAPI routes)
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
pytest tests/unit/test_service.py
```

### Run Specific Test Class

```bash
pytest tests/unit/test_service.py::TestUserServiceRegisterUser
```

### Run Specific Test Function

```bash
pytest tests/unit/test_service.py::TestUserServiceRegisterUser::test_register_user_success
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Coverage Report

```bash
pytest --cov=app --cov-report=term-missing
```

### Run with HTML Coverage Report

```bash
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

## Test Categories

### Unit Tests

Unit tests are completely isolated from external dependencies:

- **test_utils.py**: Tests password hashing and JWT token creation/validation
- **test_models.py**: Tests Pydantic model validation (RegisterRequest, LoginRequest, etc.)
- **test_repository.py**: Tests UserRepository with mocked database sessions
- **test_service.py**: Tests UserService business logic with mocked repositories

**Key characteristics:**
- No actual database connections
- All external dependencies are mocked
- Fast execution (milliseconds)
- Test individual functions/methods in isolation

### Integration Tests

Integration tests verify the complete application flow:

- **test_api_endpoints.py**: Tests API endpoints with real database operations

**Key characteristics:**
- Uses SQLite in-memory database for testing
- Tests complete request/response cycle
- Verifies database state after operations
- Tests error handling across all layers

## Test Coverage

The test suite covers:

1. **API Endpoints** (Integration)
   - POST /api/users/register (success, duplicate email/phone, validation errors)
   - POST /api/users/login (success, wrong credentials, missing fields)
   - GET /health (health check)
   - GET / (root endpoint)

2. **Service Layer** (Unit)
   - User registration with validation
   - Password hashing
   - Duplicate email/phone detection
   - User authentication
   - JWT token generation
   - Error handling (409, 401, 422)

3. **Repository Layer** (Unit)
   - User creation
   - User lookup by email
   - Email existence check
   - Phone number existence check
   - IntegrityError handling

4. **Utility Functions** (Unit)
   - Password hashing (bcrypt)
   - Password verification
   - JWT token creation
   - JWT token validation

5. **Pydantic Models** (Unit)
   - RegisterRequest validation
   - LoginRequest validation
   - Response model serialization
   - Field validation rules

## Fixtures

Common fixtures available in `conftest.py`:

- `mock_db_session`: Mock database session for unit tests
- `async_db_session`: Real in-memory database session for integration tests
- `test_client`: AsyncClient with database dependency override
- `sample_user`: Sample User model instance
- `sample_user_data`: Sample user registration data
- `mock_user_repository`: Mock UserRepository for service tests

## Writing New Tests

### Unit Test Example

```python
import pytest
from unittest.mock import patch

@pytest.mark.asyncio
async def test_my_function(mock_db_session):
    """Test description."""
    # Arrange
    with patch('app.module.dependency', return_value=expected):
        # Act
        result = await my_function(mock_db_session)

        # Assert
        assert result == expected
```

### Integration Test Example

```python
@pytest.mark.asyncio
async def test_my_endpoint(test_client):
    """Test description."""
    # Arrange
    payload = {"key": "value"}

    # Act
    response = await test_client.post("/endpoint", json=payload)

    # Assert
    assert response.status_code == 200
    assert response.json()["key"] == "value"
```

## Best Practices

1. **Follow AAA Pattern**: Arrange, Act, Assert
2. **Descriptive Names**: Test names should explain what is being tested
3. **One Assertion Focus**: Each test should verify one specific behavior
4. **Mock External Dependencies**: Unit tests should not make real network/DB calls
5. **Clean Fixtures**: Use fixtures to reduce code duplication
6. **Test Error Cases**: Always test both success and failure scenarios
7. **Async/Await**: Use `@pytest.mark.asyncio` for async tests

## Troubleshooting

### Import Errors

If you get import errors, ensure you're running from the project root:

```bash
cd /Users/fr4lzen/Documents/мирэа/микросы/пр7/project/user-service
pytest
```

### Database Errors

Integration tests use SQLite in-memory database. If you encounter database errors:

1. Ensure `aiosqlite` is installed: `pip install aiosqlite`
2. Check that fixtures are properly defined in `conftest.py`

### Async Errors

If async tests fail:

1. Ensure test function is marked with `@pytest.mark.asyncio`
2. Check that `pytest-asyncio` is installed
3. Verify `asyncio_mode = auto` is set in `pytest.ini`

## CI/CD Integration

To run tests in CI/CD pipeline:

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Run tests with coverage
pytest --cov=app --cov-report=xml --cov-report=term

# Generate coverage badge (optional)
coverage-badge -o coverage.svg
```

## Test Statistics

Run this command to see test statistics:

```bash
pytest --co -q  # Count tests without running
pytest --durations=10  # Show 10 slowest tests
```

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [FastAPI testing documentation](https://fastapi.tiangolo.com/tutorial/testing/)
