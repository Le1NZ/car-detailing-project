# Cart Service Test Suite

Comprehensive unit and integration tests for the Cart Service microservice.

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and test configuration
├── unit/                          # Unit tests (isolated components)
│   ├── test_models.py            # Pydantic model validation tests
│   ├── test_repository.py        # Repository layer tests
│   └── test_service.py           # Service layer business logic tests
└── integration/                   # Integration tests (API endpoints)
    └── test_api.py               # End-to-end API endpoint tests
```

## Test Coverage

### Unit Tests

#### Models (`test_models.py`)
- **CartItem**: 13 tests
  - Field validation (positive values, required fields)
  - Serialization/deserialization
  - Edge cases (zero/negative values)

- **CartResponse**: 8 tests
  - Response structure validation
  - Empty cart handling
  - Multiple items support
  - UUID validation

- **AddItemRequest**: 9 tests
  - Request validation
  - Field requirements
  - Edge cases

**Total**: 30 unit tests for models

#### Repository (`test_repository.py`)
- **get_cart()**: 4 tests
  - Empty cart retrieval
  - Item retrieval
  - User isolation

- **add_item()**: 8 tests
  - Adding items
  - Quantity accumulation
  - Multiple items

- **remove_item()**: 6 tests
  - Successful removal
  - Error handling
  - User isolation

- **clear_cart()**: 4 tests
  - Cart clearing
  - User isolation

- **get_all_carts()**: 4 tests
  - Retrieval logic

**Total**: 26 unit tests for repository

#### Service (`test_service.py`)
- **get_cart()**: 4 tests
  - Empty and populated carts
  - Total price calculation
  - Repository integration

- **add_item()**: 8 tests
  - Catalog validation
  - Item addition
  - Error handling (404, 400)
  - Quantity accumulation

- **remove_item()**: 5 tests
  - Item removal
  - Error handling
  - Repository interaction

- **_calculate_total_price()**: 7 tests
  - Price calculation logic
  - Rounding
  - Multiple items

- **get_catalog()**: 3 tests
  - Catalog retrieval

- **Integration**: 3 tests
  - Complete workflows

**Total**: 30 unit tests for service

### Integration Tests

#### API Endpoints (`test_api.py`)
- **Health & Info**: 2 tests
  - `/health` endpoint
  - `/` root endpoint

- **GET /api/cart**: 4 tests
  - Empty cart
  - Cart with items
  - Multiple items
  - Response model validation

- **POST /api/cart/items**: 10 tests
  - Adding services and products
  - Quantity accumulation
  - Validation errors (404, 400, 422)
  - Invalid JSON handling

- **DELETE /api/cart/items/{item_id}**: 5 tests
  - Successful removal
  - Error handling (404)
  - Multiple removals

- **End-to-End Workflows**: 5 tests
  - Complete shopping workflow
  - Same item multiple times
  - Large quantities
  - Error recovery
  - Empty to full to empty

- **API Documentation**: 3 tests
  - OpenAPI schema
  - Swagger UI
  - ReDoc

- **Concurrent Operations**: 1 test
  - Sequential operation consistency

**Total**: 30 integration tests

## Running Tests

### Install Dependencies

```bash
# Install development dependencies
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=html
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
pytest tests/unit/test_models.py::TestCartItem

# Run specific test
pytest tests/unit/test_models.py::TestCartItem::test_cart_item_creation_success
```

### Run Tests by Markers

```bash
# Run unit tests (if marked)
pytest -m unit

# Run integration tests (if marked)
pytest -m integration

# Run smoke tests
pytest -m smoke
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Open coverage report (HTML)
open htmlcov/index.html

# Generate terminal coverage report
pytest --cov=app --cov-report=term-missing

# Generate XML coverage report (for CI/CD)
pytest --cov=app --cov-report=xml
```

## Test Fixtures

### Shared Fixtures (conftest.py)

- **Model Fixtures**:
  - `sample_cart_item`: Sample service cart item
  - `sample_cart_item_product`: Sample product cart item
  - `sample_add_item_request`: Sample add request
  - `sample_add_item_request_product`: Sample product add request

- **Repository Fixtures**:
  - `clean_cart_repo`: Fresh repository instance
  - `populated_cart_repo`: Repository with sample data
  - `mock_cart_repo`: Mocked repository for isolation

- **Service Fixtures**:
  - `cart_service`: Service with clean repository
  - `cart_service_with_data`: Service with pre-populated data

- **API Test Client Fixtures**:
  - `test_client`: TestClient with real dependencies
  - `test_client_with_mock_service`: TestClient with mocked service

## Test Design Principles

### Unit Tests
- **Isolation**: Each test is independent
- **Mocking**: External dependencies are mocked
- **Coverage**: All code paths are tested
- **Edge Cases**: Boundary conditions are validated

### Integration Tests
- **End-to-End**: Complete HTTP request/response cycle
- **Real Dependencies**: Uses actual FastAPI app
- **Workflows**: Tests realistic user scenarios
- **Error Handling**: Validates error responses

## Continuous Integration

### Running Tests in CI/CD

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements-dev.txt
    pytest --cov=app --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Test Metrics

- **Total Tests**: 116 tests
- **Unit Tests**: 86 tests (74%)
- **Integration Tests**: 30 tests (26%)
- **Expected Coverage**: >90%

## Writing New Tests

### Unit Test Template

```python
def test_feature_name(fixture_name):
    """Test description of what is being tested"""
    # Arrange - Set up test data
    service = fixture_name

    # Act - Execute the code under test
    result = service.method()

    # Assert - Verify the result
    assert result == expected_value
```

### Integration Test Template

```python
def test_endpoint_name(test_client: TestClient):
    """Test description of endpoint behavior"""
    # Arrange - Prepare request data
    request_data = {"key": "value"}

    # Act - Make HTTP request
    response = test_client.post("/api/endpoint", json=request_data)

    # Assert - Verify response
    assert response.status_code == 200
    assert response.json()["key"] == "value"
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running tests from the project root directory
2. **Fixture Not Found**: Check conftest.py is in the correct location
3. **Coverage Not Working**: Install pytest-cov: `pip install pytest-cov`

### Debug Mode

```bash
# Run with Python debugger
pytest --pdb

# Show print statements
pytest -s

# Stop on first failure
pytest -x
```

## Best Practices

1. **Test Naming**: Use descriptive test names that explain what is being tested
2. **Arrange-Act-Assert**: Follow AAA pattern for test structure
3. **One Assertion**: Focus each test on a single behavior
4. **Independent Tests**: Tests should not depend on each other
5. **Mocking**: Mock external dependencies to ensure isolation
6. **Coverage**: Aim for >90% code coverage with meaningful tests

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pydantic Validation Testing](https://docs.pydantic.dev/latest/concepts/validation/)
