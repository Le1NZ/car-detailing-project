# Car Service Test Suite

Comprehensive test suite for car-service microservice with unit and integration tests.

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and test configuration
├── unit/                          # Unit tests (isolated component testing)
│   ├── test_models.py            # Pydantic model validation tests
│   ├── test_repository.py        # Repository layer tests
│   └── test_service.py           # Service layer business logic tests
├── integration/                   # Integration tests (end-to-end API testing)
│   └── test_endpoints.py         # FastAPI endpoint tests
└── README.md                      # This file
```

## Running Tests

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run tests for a specific file
pytest tests/unit/test_models.py

# Run a specific test class
pytest tests/unit/test_models.py::TestAddCarRequest

# Run a specific test
pytest tests/unit/test_models.py::TestAddCarRequest::test_valid_car_request
```

### Run with Coverage

```bash
# Run tests with coverage report
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Output Capture Disabled

```bash
pytest -s
```

## Test Coverage

The test suite provides comprehensive coverage across all layers:

### Unit Tests (tests/unit/)

#### test_models.py (Pydantic Models)
- **TestAddCarRequest**: 15 tests
  - Valid car request creation
  - VIN validation (uppercase conversion, alphanumeric check, length)
  - License plate normalization (strip, uppercase)
  - Year boundary validation (1900-2025)
  - Field length constraints
  - Required field validation

- **TestCarResponse**: 2 tests
  - Valid response creation
  - Serialization to dict/JSON

- **TestAddDocumentRequest**: 4 tests
  - Document request with/without file
  - Document type constraints
  - Required field validation

- **TestDocumentResponse**: 3 tests
  - Valid response creation
  - Serialization
  - Required fields validation

- **TestModelEdgeCases**: 5 tests
  - UUID string/object conversion
  - Invalid UUID handling
  - Special characters in fields
  - Numeric/alpha-only VINs

**Total Model Tests**: 29 tests

#### test_repository.py (Repository Layer)
- **TestLocalCarRepositoryAddCar**: 6 tests
  - Successful car addition
  - Unique ID generation
  - Duplicate VIN detection
  - Duplicate license plate detection
  - Multiple unique cars
  - Data preservation

- **TestLocalCarRepositoryGetCar**: 3 tests
  - Get car by ID success
  - Car not found handling
  - Get specific car from multiple

- **TestLocalCarRepositoryDocuments**: 9 tests
  - Add document success
  - Unique document ID generation
  - Document for non-existent car
  - Document without file
  - Multiple documents per car
  - Get documents by car ID
  - Get documents for car with no documents
  - Documents isolation between cars

- **TestLocalCarRepositoryUtilityMethods**: 6 tests
  - Get all cars (empty and populated)
  - Get all cars returns copy
  - Clear removes cars and documents
  - Clear on empty repository

- **TestRepositorySingleton**: 3 tests
  - Singleton pattern validation
  - Instance type verification
  - State persistence

- **TestRepositoryEdgeCases**: 3 tests
  - UUID vs string owner_id
  - Case-sensitive duplicate detection
  - Document status always pending

**Total Repository Tests**: 30 tests

#### test_service.py (Service Layer)
- **TestCarServiceCreateCar**: 6 tests
  - Create car success
  - Repository interaction verification
  - Duplicate VIN error handling
  - Duplicate license plate error handling
  - Error propagation
  - Multiple cars creation

- **TestCarServiceGetCar**: 5 tests
  - Get car success
  - Car not found error
  - Repository interaction verification
  - Repository returning None
  - Get specific car from multiple

- **TestCarServiceAddDocument**: 6 tests
  - Add document success
  - Repository interaction verification
  - Car not found error
  - Document without file
  - Multiple documents to one car
  - Error propagation

- **TestCarServiceGetCarDocuments**: 5 tests
  - Get documents success
  - Empty document list
  - Car not found error
  - Repository interaction verification
  - Documents isolation between cars

- **TestCarServiceInitialization**: 2 tests
  - Service initialization with repository
  - Service initialization with mock

- **TestCarServiceEdgeCases**: 4 tests
  - Boundary year values
  - Minimal field lengths
  - Document status consistency
  - Data integrity preservation

**Total Service Tests**: 28 tests

### Integration Tests (tests/integration/)

#### test_endpoints.py (API Endpoints)
- **TestHealthEndpoints**: 2 tests
  - Health check endpoint
  - Root endpoint

- **TestCreateCarEndpoint**: 15 tests
  - POST /api/cars success
  - Response schema validation
  - Duplicate VIN (409 Conflict)
  - Duplicate license plate (409 Conflict)
  - Invalid VIN length (422 Unprocessable Entity)
  - Invalid VIN characters (422)
  - Invalid year boundaries (422)
  - Missing required fields (422)
  - Invalid UUID format (422)
  - VIN uppercase conversion
  - License plate normalization
  - Multiple unique cars creation

- **TestGetCarEndpoint**: 7 tests
  - GET /api/cars/{car_id} success
  - Car not found (404 Not Found)
  - Invalid UUID format (422)
  - Response schema validation
  - CRITICAL: order-service integration test
  - Data consistency between create/get
  - Get specific car from multiple

- **TestAddDocumentEndpoint**: 10 tests
  - POST /api/cars/{car_id}/documents success
  - Response schema validation
  - Document without file
  - Car not found (404)
  - Invalid car ID format (422)
  - Missing document_type (422)
  - Empty document_type (422)
  - Multiple documents to same car
  - Document status always pending

- **TestEndToEndFlows**: 4 tests
  - Complete car lifecycle (create -> get -> add documents)
  - Order-service integration flow
  - Duplicate prevention flow
  - Multiple cars and documents management

- **TestAPIErrorHandling**: 4 tests
  - Invalid JSON body handling
  - Content-Type validation
  - Malformed UUID handling
  - Case-sensitive endpoint paths

**Total Integration Tests**: 42 tests

## Total Test Count: 129 tests

## Test Quality Features

### 1. Complete Isolation
- All tests are independent and can run in any order
- No external dependencies (databases, network calls)
- Clean repository fixtures ensure test isolation

### 2. Comprehensive Coverage
- Happy path scenarios
- Error scenarios (4xx, 5xx)
- Edge cases and boundary conditions
- Business logic validation
- Data integrity checks

### 3. Clear Test Organization
- AAA pattern (Arrange, Act, Assert)
- Descriptive test names
- Clear docstrings
- Logical grouping by functionality

### 4. Mocking Strategy
- Repository mocking for service tests
- Dependency injection override for integration tests
- Mock verification for interaction testing

### 5. Fixtures
- Reusable test data fixtures
- Clean repository fixtures
- Service with pre-populated data
- Test client with dependency overrides

## Key Test Scenarios

### Critical for order-service Integration
- `test_get_car_critical_for_order_service_integration`: Validates the exact endpoint used by order-service
- `test_order_service_integration_flow`: Tests complete integration flow

### Duplicate Detection
- VIN uniqueness enforcement
- License plate uniqueness enforcement
- Proper 409 Conflict responses

### Data Validation
- Pydantic model validation
- Field constraints (length, format, range)
- Required fields enforcement

### Error Handling
- 404 Not Found for non-existent resources
- 409 Conflict for duplicates
- 422 Unprocessable Entity for validation errors
- Proper error messages

## Running Tests in CI/CD

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests with coverage
pytest --cov=app --cov-report=xml --cov-report=term

# Check minimum coverage threshold (e.g., 90%)
pytest --cov=app --cov-fail-under=90
```

## Test Markers

Tests are marked for easy filtering:

- `@pytest.mark.unit`: Unit tests (fast, isolated)
- `@pytest.mark.integration`: Integration tests (API endpoints)
- `@pytest.mark.slow`: Tests that take longer to run

## Common Issues and Solutions

### Issue: Tests fail with import errors
**Solution**: Make sure you're running tests from the project root and `app` package is importable.

### Issue: Singleton repository state persists
**Solution**: Use the `clean_repository` fixture which clears state after each test.

### Issue: Tests pass individually but fail when run together
**Solution**: Check for shared state. Use fixtures to ensure isolation.

## Contributing

When adding new features:

1. Write unit tests for new business logic
2. Write integration tests for new endpoints
3. Ensure all tests pass: `pytest`
4. Check coverage: `pytest --cov=app`
5. Update this README if adding new test categories

## Test Maintenance

- Keep tests updated when changing business logic
- Maintain high coverage (target: >90%)
- Refactor tests to reduce duplication
- Add tests for bug fixes to prevent regression
