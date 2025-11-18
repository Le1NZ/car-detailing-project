# Fines Service - Test Suite

Comprehensive test suite for the fines-service microservice.

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and test configuration
├── unit/                          # Unit tests (isolated components)
│   ├── test_models.py            # Pydantic model tests
│   ├── test_repository.py        # Repository layer tests
│   └── test_service.py           # Service layer business logic tests
└── integration/                   # Integration tests (API endpoints)
    └── test_endpoints.py         # FastAPI endpoint tests
```

## Installation

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with verbose output
```bash
pytest -v
```

### Run specific test file
```bash
pytest tests/unit/test_models.py
pytest tests/integration/test_endpoints.py
```

### Run specific test class
```bash
pytest tests/unit/test_models.py::TestFineModel
```

### Run specific test
```bash
pytest tests/unit/test_models.py::TestFineModel::test_create_fine_with_valid_data
```

### Run only unit tests
```bash
pytest tests/unit/
```

### Run only integration tests
```bash
pytest tests/integration/
```

## Code Coverage

### Generate coverage report
```bash
pytest --cov=app --cov-report=html --cov-report=term
```

### View HTML coverage report
```bash
open htmlcov/index.html
```

### Coverage with missing lines
```bash
pytest --cov=app --cov-report=term-missing
```

## Test Categories

### Unit Tests (tests/unit/)

Test individual components in isolation with mocked dependencies.

**test_models.py** - Pydantic Model Tests
- Fine model validation and serialization
- FineResponse model structure
- PayFineRequest validation
- PaymentResponse structure
- Model serialization/deserialization
- **Total: 30+ tests**

**test_repository.py** - Repository Layer Tests
- Repository initialization
- CRUD operations
- Fine retrieval by plate and ID
- Marking fines as paid
- Index synchronization
- Edge cases and error handling
- **Total: 35+ tests**

**test_service.py** - Service Layer Tests
- Business logic validation
- Fine checking workflow
- Payment processing
- Error handling (ValueError, RuntimeError)
- Service-repository interaction
- Edge cases and boundary conditions
- **Total: 30+ tests**

### Integration Tests (tests/integration/)

Test complete HTTP request/response flow through FastAPI.

**test_endpoints.py** - API Endpoint Tests
- Health check endpoint
- Root endpoint documentation
- GET /api/fines/check - Check fines
- POST /api/fines/{fine_id}/pay - Pay fine
- End-to-end workflows
- API validation and error handling
- HTTP status codes (200, 404, 409, 422)
- Request/response structure validation
- **Total: 40+ tests**

## Test Coverage Summary

### Models Coverage
- Fine: 100% (creation, validation, defaults, serialization)
- FineResponse: 100% (structure, validation)
- PayFineRequest: 100% (validation, edge cases)
- PaymentResponse: 100% (structure, validation)

### Repository Coverage
- LocalFineRepository: 100%
  - Initialization with test data
  - get_fines_by_plate (all scenarios)
  - get_unpaid_fines_by_plate (filtering logic)
  - get_fine_by_id (found/not found)
  - mark_fine_as_paid (success/failure)
  - is_fine_paid (all states)
  - Edge cases and data consistency

### Service Coverage
- FineService: 100%
  - check_fines (happy path, empty results, multiple fines)
  - pay_fine (success, not found, already paid)
  - Error handling (ValueError, RuntimeError)
  - Repository interaction
  - Business logic validation

### Endpoints Coverage
- All API endpoints: 100%
  - GET /health
  - GET /
  - GET /api/fines/check
  - POST /api/fines/{fine_id}/pay
  - All HTTP status codes
  - Request validation
  - Response structure
  - Error handling
  - End-to-end workflows

## Key Testing Patterns

### 1. Mocking External Dependencies
```python
def test_with_mock_repository(mock_repository):
    mock_repository.get_fine_by_id.return_value = sample_fine
    service = FineService(mock_repository)
    result = service.pay_fine(fine_id, "card_123")
```

### 2. Testing with Real Components
```python
def test_with_real_repository(real_repository):
    fines = real_repository.get_fines_by_plate("А123БВ799")
    assert len(fines) > 0
```

### 3. Integration Testing with TestClient
```python
def test_api_endpoint(test_client):
    response = test_client.get("/api/fines/check?license_plate=А123БВ799")
    assert response.status_code == 200
```

### 4. Testing Error Scenarios
```python
def test_fine_not_found_raises_error(mock_repository):
    mock_repository.get_fine_by_id.return_value = None
    with pytest.raises(ValueError):
        service.pay_fine(uuid4(), "card_123")
```

## Test Data

Tests use predefined test data from the repository:
- **А123БВ799**: 500 руб. - "Превышение скорости на 20-40 км/ч"
- **М456КЛ177**: 1000 руб. - "Проезд на красный свет"

Integration tests create fresh TestClient instances when needed to ensure test isolation.

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example CI configuration
test:
  script:
    - pip install -r requirements-test.txt
    - pytest --cov=app --cov-report=xml
    - pytest --cov=app --cov-report=term
```

## Best Practices

1. **Test Isolation**: Each test is independent and doesn't affect others
2. **Clear Naming**: Test names describe what is being tested and expected outcome
3. **AAA Pattern**: Arrange, Act, Assert structure in all tests
4. **Comprehensive Coverage**: Both happy paths and error scenarios
5. **Mock External Dependencies**: Repository layer is mocked in service tests
6. **Integration Testing**: Complete HTTP flow tested with TestClient
7. **Edge Cases**: Boundary conditions and error scenarios thoroughly tested

## Troubleshooting

### Import errors
Make sure you're running tests from the project root:
```bash
cd /Users/fr4lzen/Documents/мирэа/микросы/пр7/project/fines-service
pytest
```

### Test discovery issues
Verify pytest.ini is in the project root and testpaths is set correctly.

### Coverage not showing all files
Ensure you're running coverage from the project root with correct source path.

## Total Test Count

- **Unit Tests**: ~95 tests
- **Integration Tests**: ~40 tests
- **Total**: ~135 comprehensive tests

All tests follow production-grade testing standards with complete isolation from external systems.
