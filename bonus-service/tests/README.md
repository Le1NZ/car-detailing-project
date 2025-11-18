# Bonus Service - Test Suite

## Overview

Comprehensive test suite for bonus-service microservice with 100+ test cases covering all layers of the application.

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and pytest configuration
├── unit/                          # Unit tests (isolated, no external dependencies)
│   ├── test_models.py            # Pydantic model validation tests
│   ├── test_repository.py        # Repository layer tests
│   ├── test_service.py           # Service layer business logic tests
│   └── test_rabbitmq_consumer.py # RabbitMQ consumer tests
└── integration/                   # Integration tests (API endpoints)
    └── test_api_endpoints.py     # End-to-end API tests
```

## Test Coverage

### Unit Tests (75+ test cases)

#### 1. Models Tests (`test_models.py`)
- **ApplyPromocodeRequest**: Validation, UUID handling, empty/missing fields
- **PromocodeResponse**: Serialization, field validation
- **SpendBonusesRequest**: Amount validation (positive, non-zero), type conversion
- **SpendBonusesResponse**: Balance calculations, JSON serialization
- **HealthResponse**: Status reporting
- **Model Integration**: Request-response cycles

**Total**: 20+ test cases

#### 2. Repository Tests (`test_repository.py`)
- **Promocode Class**: Initialization, default values
- **Repository Initialization**: Predefined promocodes, empty balances
- **get_user_balance**: New users, existing users, non-modification
- **add_bonuses**: New users, existing users, fractional amounts, multiple users
- **spend_bonuses**: Sufficient balance, insufficient balance errors, all bonuses, edge cases
- **find_promocode**: Valid codes, invalid codes, inactive codes, case sensitivity
- **Integration Scenarios**: Complete bonus lifecycle, multi-user operations

**Total**: 35+ test cases

#### 3. Service Tests (`test_service.py`)
- **apply_promocode**: Valid codes (SUMMER24, WELCOME10), invalid codes, error handling
- **spend_bonuses**: Sufficient/insufficient balance, zero balance, fractional amounts
- **accrue_bonuses**: Standard rate (1%), custom rates, large amounts, edge cases
- **Service Integration**: Complete workflows, multiple operations, multi-user scenarios

**Total**: 30+ test cases

#### 4. RabbitMQ Consumer Tests (`test_rabbitmq_consumer.py`)
- **Initialization**: Consumer setup with bonus service
- **start Method**: RabbitMQ connection, channel creation, QoS settings, queue declaration
- **on_message Handler**:
  - Valid payloads with correct bonus calculations
  - Missing fields (order_id, user_id, amount)
  - Invalid data (malformed JSON, invalid UUIDs, non-numeric amounts)
  - Service exceptions and error logging
- **stop Method**: Graceful shutdown, connection cleanup, error handling
- **Integration**: Complete lifecycle testing

**Total**: 25+ test cases

### Integration Tests (40+ test cases)

#### API Endpoints (`test_api_endpoints.py`)

**Health & Root Endpoints**:
- Health check availability and format
- Root endpoint service information

**POST /api/bonuses/promocodes/apply**:
- Valid promocodes (SUMMER24, WELCOME10)
- Invalid/inactive promocodes (404)
- Missing fields (422)
- Invalid UUID format (422)
- Case sensitivity
- Multiple applications to same order
- Concurrent operations

**POST /api/bonuses/spend**:
- Sufficient balance scenarios
- Insufficient balance (400)
- Zero/negative amounts (422)
- Missing fields (422)
- Invalid UUID (422)
- Large amounts
- Fractional balance handling

**Integration Scenarios**:
- Complete workflow: promocode → accrue → spend
- Multiple users spending independently
- Error response format verification
- CORS headers (if applicable)
- Edge cases and boundary conditions

**Total**: 40+ test cases

## Running Tests

### Prerequisites

Python 3.11+ is required (Python 3.14 may have compatibility issues with pydantic 2.5.0).

### Installation

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/ -m unit

# Integration tests only
pytest tests/integration/ -m integration

# Specific test file
pytest tests/unit/test_service.py

# Specific test class
pytest tests/unit/test_service.py::TestApplyPromocode

# Specific test method
pytest tests/unit/test_service.py::TestApplyPromocode::test_apply_valid_promocode_success
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=html --cov-report=term-missing

# View HTML coverage report
open htmlcov/index.html  # On macOS
# Or: xdg-open htmlcov/index.html  # On Linux
# Or: start htmlcov/index.html  # On Windows
```

### Run with Verbose Output

```bash
pytest -v -s
```

### Run Fast (Skip Slow Tests)

```bash
pytest -m "not slow"
```

## Test Markers

Tests are marked with pytest markers for selective execution:

- `@pytest.mark.unit` - Unit tests (isolated)
- `@pytest.mark.integration` - Integration tests (API)
- `@pytest.mark.asyncio` - Async tests
- `@pytest.mark.slow` - Time-consuming tests

## Expected Coverage

With all tests passing, expected coverage:

- **Models**: 100%
- **Repositories**: 95%+
- **Services**: 95%+
- **RabbitMQ Consumer**: 90%+
- **API Endpoints**: 95%+
- **Overall**: 90%+

## Test Isolation

All tests are completely isolated:

- **No external dependencies**: RabbitMQ and external services are mocked
- **No network calls**: HTTP clients are mocked
- **No real database**: In-memory repository is used
- **Clean state**: Repository is reset between tests

## Fixtures

Key fixtures in `conftest.py`:

- `test_user_id`, `test_order_id` - Standard UUIDs for testing
- `mock_repository` - Mocked repository with predefined behaviors
- `fresh_repository` - Clean repository instance
- `mock_bonus_service` - Mocked service for endpoint tests
- `bonus_service` - Service with mocked repository
- `mock_rabbitmq_connection` - Mocked aio_pika connection
- `test_client` - FastAPI test client (synchronous)
- `async_test_client` - Async test client

## Continuous Integration

For CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements-test.txt
    pytest --cov=app --cov-report=xml --cov-report=term-missing

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Troubleshooting

### Import Errors

Ensure you're running tests from the bonus-service root directory and the app package is importable:

```bash
cd /path/to/bonus-service
export PYTHONPATH=.
pytest
```

### Async Test Issues

If async tests fail, ensure `pytest-asyncio` is installed and configured:

```bash
pip install pytest-asyncio
```

### RabbitMQ Mock Issues

RabbitMQ consumer tests use complex mocking. If tests fail, check:
- `unittest.mock` imports are correct
- Async context managers are properly mocked
- `aio_pika` module is available

## Best Practices

1. **Run tests before committing**: `pytest`
2. **Check coverage**: Aim for 90%+ coverage
3. **Keep tests fast**: Unit tests should run in milliseconds
4. **Mock external services**: Never make real network calls
5. **Use descriptive test names**: Test name should explain what's being tested
6. **One assertion per test**: Focus on single behavior
7. **AAA Pattern**: Arrange, Act, Assert

## Contributing

When adding new features:

1. Write tests first (TDD)
2. Ensure all tests pass
3. Maintain or improve coverage
4. Add integration tests for new endpoints
5. Update this README if test structure changes

## Test Data

Standard test data:

- **User ID**: `c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d`
- **Order ID**: `123e4567-e89b-12d3-a456-426614174000`
- **Promocodes**: SUMMER24 (500), WELCOME10 (1000)
- **Bonus Rate**: 1% (0.01)

## Support

For issues or questions about tests:
1. Check pytest output for detailed error messages
2. Review test logs in verbose mode: `pytest -v -s`
3. Ensure all dependencies are installed: `pip list`
4. Verify Python version: `python --version` (requires 3.11+)
