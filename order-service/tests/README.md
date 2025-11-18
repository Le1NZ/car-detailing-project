# Order Service - Tests

This directory contains the complete test suite for the order-service microservice.

## Quick Start

```bash
# From project root
./run_tests.sh
```

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures (11 fixtures)
├── unit/                          # Unit tests (84 tests)
│   ├── test_models.py            # Model validation (28 tests)
│   ├── test_repository.py        # Data access (19 tests)
│   ├── test_car_client.py        # HTTP client (15 tests)
│   └── test_order_service.py     # Business logic (22 tests)
└── integration/                   # Integration tests (22 tests)
    └── test_api_endpoints.py     # API endpoints (22 tests)
```

## Test Statistics

- **Total Tests**: 106
- **Unit Tests**: 84
- **Integration Tests**: 22
- **Expected Coverage**: >85%
- **Execution Time**: ~2 seconds

## Running Tests

### All tests
```bash
pytest
```

### Unit tests only
```bash
pytest tests/unit/
```

### Integration tests only
```bash
pytest tests/integration/
```

### Specific file
```bash
pytest tests/unit/test_models.py
```

### With coverage report
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## Documentation

- **Detailed Guide**: `../TESTING.md`
- **Summary**: `../TEST_SUITE_SUMMARY.md`

## Test Categories

### Unit Tests (tests/unit/)
Test individual components in isolation with all external dependencies mocked.

- **test_models.py**: Pydantic validation logic
- **test_repository.py**: In-memory storage operations
- **test_car_client.py**: HTTP client with mocked httpx
- **test_order_service.py**: Business logic with mocked dependencies

### Integration Tests (tests/integration/)
Test API endpoints end-to-end using FastAPI TestClient.

- **test_api_endpoints.py**: Complete HTTP request/response flow

## Fixtures (conftest.py)

Available fixtures for all tests:

**Test Data:**
- `test_car_id`, `test_order_id`, `test_review_id`
- `test_datetime`
- `sample_order_data`, `sample_review_data`
- `sample_order`, `sample_review`

**Mocks:**
- `mock_repository` - Mock LocalOrderRepository
- `mock_car_client` - Mock CarServiceClient
- `fresh_repository` - Fresh repository instance

## Contributing

When adding new tests:
1. Place unit tests in `tests/unit/`
2. Place integration tests in `tests/integration/`
3. Add new fixtures to `conftest.py` if needed
4. Follow naming convention: `test_<component>_<scenario>`
5. Update documentation in `../TESTING.md`

## Requirements

```bash
pip install -r requirements-test.txt
```

Required packages:
- pytest==7.4.3
- pytest-asyncio==0.21.1
- pytest-cov==4.1.0
- pytest-mock==3.12.0
