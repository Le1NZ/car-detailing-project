# Cart Service - Complete Testing Guide

## Project Structure with Tests

```
cart-service/
├── app/                                # Application code
│   ├── __init__.py
│   ├── main.py                         # FastAPI application
│   ├── config.py                       # Configuration
│   ├── models/
│   │   ├── __init__.py
│   │   └── cart.py                     # Pydantic models
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── local_cart_repo.py          # In-memory repository
│   ├── services/
│   │   ├── __init__.py
│   │   └── cart_service.py             # Business logic + CATALOG
│   └── endpoints/
│       ├── __init__.py
│       └── cart.py                     # API endpoints
│
├── tests/                              # Test suite
│   ├── __init__.py
│   ├── conftest.py                     # Shared fixtures
│   ├── README.md                       # Test documentation
│   │
│   ├── unit/                           # Unit tests (81 tests)
│   │   ├── __init__.py
│   │   ├── test_models.py              # 25 tests - Pydantic models
│   │   ├── test_repository.py          # 25 tests - Repository layer
│   │   └── test_service.py             # 31 tests - Service layer
│   │
│   └── integration/                    # Integration tests (30 tests)
│       ├── __init__.py
│       └── test_api.py                 # 30 tests - API endpoints
│
├── requirements.txt                    # Production dependencies
├── requirements-dev.txt                # Development & testing dependencies
├── pytest.ini                          # Pytest configuration
├── TEST_SUMMARY.md                     # Test suite summary
├── TESTING_GUIDE.md                    # This file
├── Dockerfile
└── README.md
```

## Quick Start

### 1. Install Dependencies

```bash
# Install all dependencies (production + development)
pip install -r requirements-dev.txt

# Or install separately
pip install -r requirements.txt      # Production
pip install -r requirements-dev.txt  # Testing
```

### 2. Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app --cov-report=term-missing
```

### 3. View Coverage

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Open in browser (macOS)
open htmlcov/index.html

# Open in browser (Linux)
xdg-open htmlcov/index.html
```

## Test Categories

### Unit Tests (81 tests)

Test individual components in complete isolation with mocked dependencies.

#### Models Tests (25 tests)
**File**: `tests/unit/test_models.py`

```bash
# Run all model tests
pytest tests/unit/test_models.py -v

# Run specific model class tests
pytest tests/unit/test_models.py::TestCartItem -v
pytest tests/unit/test_models.py::TestCartResponse -v
pytest tests/unit/test_models.py::TestAddItemRequest -v
```

**What's tested**:
- Pydantic validation rules
- Field constraints (positive values, required fields)
- Serialization/deserialization
- Edge cases (zero, negative values)

#### Repository Tests (25 tests)
**File**: `tests/unit/test_repository.py`

```bash
# Run all repository tests
pytest tests/unit/test_repository.py -v

# Run specific method tests
pytest tests/unit/test_repository.py::TestLocalCartRepoGetCart -v
pytest tests/unit/test_repository.py::TestLocalCartRepoAddItem -v
```

**What's tested**:
- CRUD operations (Create, Read, Update, Delete)
- Data persistence in memory
- User isolation
- Edge cases (empty cart, non-existent items)

#### Service Tests (31 tests)
**File**: `tests/unit/test_service.py`

```bash
# Run all service tests
pytest tests/unit/test_service.py -v

# Run specific service method tests
pytest tests/unit/test_service.py::TestCartServiceAddItem -v
pytest tests/unit/test_service.py::TestCartServiceCalculateTotalPrice -v
```

**What's tested**:
- Business logic
- Catalog validation
- Price calculation
- Error handling (404, 400)
- Repository interaction

### Integration Tests (30 tests)

Test complete HTTP request/response cycles through the API.

#### API Endpoint Tests (30 tests)
**File**: `tests/integration/test_api.py`

```bash
# Run all integration tests
pytest tests/integration/test_api.py -v

# Run specific endpoint tests
pytest tests/integration/test_api.py::TestGetCartEndpoint -v
pytest tests/integration/test_api.py::TestAddItemEndpoint -v
pytest tests/integration/test_api.py::TestRemoveItemEndpoint -v
```

**What's tested**:
- HTTP status codes (200, 204, 400, 404, 422)
- Request/response formats
- End-to-end workflows
- Error responses
- API documentation endpoints

## Test Execution Examples

### By Test Type

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/test_models.py -v
```

### By Test Name

```bash
# Run single test
pytest tests/unit/test_models.py::TestCartItem::test_cart_item_creation_success -v

# Run tests matching pattern
pytest -k "test_add_item" -v

# Run tests matching multiple patterns
pytest -k "test_add_item or test_remove_item" -v
```

### By Test Class

```bash
# Run all tests in a class
pytest tests/unit/test_models.py::TestCartItem -v
pytest tests/integration/test_api.py::TestAddItemEndpoint -v
```

### With Different Output Formats

```bash
# Minimal output
pytest -q

# Verbose output with test docstrings
pytest -v

# Show print statements
pytest -s

# Show local variables in tracebacks
pytest -l

# Stop on first failure
pytest -x

# Stop after N failures
pytest --maxfail=3
```

## Coverage Analysis

### Generate Coverage Reports

```bash
# Terminal report with missing lines
pytest --cov=app --cov-report=term-missing

# HTML report (most detailed)
pytest --cov=app --cov-report=html
open htmlcov/index.html

# XML report (for CI/CD)
pytest --cov=app --cov-report=xml

# Combined reports
pytest --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml
```

### Coverage by Module

```bash
# Coverage for specific module
pytest --cov=app.models tests/unit/test_models.py
pytest --cov=app.repositories tests/unit/test_repository.py
pytest --cov=app.services tests/unit/test_service.py
```

### Expected Coverage

- **Overall**: >90%
- **Models**: 100%
- **Repository**: 100%
- **Services**: 100%
- **Endpoints**: 100%

## Test Fixtures

### Available Fixtures (from conftest.py)

#### Model Fixtures
```python
# Use in tests like this:
def test_something(sample_cart_item):
    assert sample_cart_item.item_id == "svc_oil_change"
```

- `sample_cart_item` - Service cart item
- `sample_cart_item_product` - Product cart item
- `sample_add_item_request` - Service add request
- `sample_add_item_request_product` - Product add request

#### Repository Fixtures
```python
def test_something(clean_cart_repo):
    # Fresh repository for each test
    repo = clean_cart_repo
    repo.add_item(user_id, item)
```

- `clean_cart_repo` - Fresh repository
- `populated_cart_repo` - Repository with sample data
- `mock_cart_repo` - Mocked repository

#### Service Fixtures
```python
def test_something(cart_service):
    # Service with clean repository
    response = cart_service.get_cart(user_id)
```

- `cart_service` - Service with clean repository
- `cart_service_with_data` - Service with pre-populated data

#### API Client Fixtures
```python
def test_something(test_client):
    # Make HTTP requests
    response = test_client.get("/api/cart")
    assert response.status_code == 200
```

- `test_client` - TestClient with real dependencies
- `test_client_with_mock_service` - TestClient with mocked service

## Writing New Tests

### Unit Test Template

```python
def test_feature_description(fixture_name):
    """
    Test that feature behaves correctly under specific conditions
    """
    # Arrange - Set up test data
    service = fixture_name
    input_data = {"key": "value"}

    # Act - Execute the code under test
    result = service.method(input_data)

    # Assert - Verify the result
    assert result.property == expected_value
    assert result.another_property is not None
```

### Integration Test Template

```python
def test_endpoint_behavior(test_client: TestClient):
    """
    Test that endpoint responds correctly to valid request
    """
    # Arrange - Prepare request data
    request_data = {
        "item_id": "test_item",
        "type": "service",
        "quantity": 1
    }

    # Act - Make HTTP request
    response = test_client.post("/api/cart/items", json=request_data)

    # Assert - Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["item_id"] == "test_item"
```

## Debugging Tests

### Enable Debugging

```bash
# Start Python debugger on failure
pytest --pdb

# Start debugger on first failure
pytest --pdb -x

# Show more context in tracebacks
pytest -vv

# Show full diff for assertions
pytest -vv --tb=long
```

### Print Debugging

```bash
# Show print statements
pytest -s

# Show print statements with verbose output
pytest -sv
```

### Test Markers

```python
# Mark test as slow
@pytest.mark.slow
def test_time_consuming_operation():
    pass

# Mark test as work in progress
@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

# Mark test as expected to fail
@pytest.mark.xfail(reason="Known bug")
def test_buggy_behavior():
    pass
```

```bash
# Run tests with specific marker
pytest -m slow

# Skip tests with specific marker
pytest -m "not slow"
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt

    - name: Run tests with coverage
      run: |
        pytest --cov=app --cov-report=xml --cov-report=term

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### GitLab CI Example

```yaml
test:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements-dev.txt
    - pytest --cov=app --cov-report=xml --cov-report=term
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

## Best Practices

### 1. Test Independence
- Tests should not depend on each other
- Use fixtures for setup/teardown
- Each test should start with clean state

### 2. Test Naming
```python
# Good: Descriptive name explains what is tested
def test_add_item_accumulates_quantity_for_existing_item():
    pass

# Bad: Generic name doesn't explain behavior
def test_add():
    pass
```

### 3. AAA Pattern
```python
def test_example():
    # Arrange - Set up test data
    service = CartService(repo)

    # Act - Execute code under test
    result = service.method()

    # Assert - Verify result
    assert result == expected
```

### 4. One Assertion Focus
```python
# Good: Single clear assertion
def test_item_added_to_cart():
    result = service.add_item(user_id, request)
    assert len(result.items) == 1

# Avoid: Multiple unrelated assertions
def test_everything():
    # Tests too many things at once
    assert condition1
    assert condition2
    assert condition3
```

### 5. Mock External Dependencies
```python
# Good: Mock external dependencies
def test_service_with_mock_repo(mock_cart_repo):
    service = CartService(mock_cart_repo)
    # Test service in isolation

# Avoid: Real external dependencies in unit tests
def test_service_with_real_database():
    # Don't use real database in unit tests
    pass
```

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Problem: ModuleNotFoundError
# Solution: Run tests from project root
cd /path/to/cart-service
pytest
```

#### Fixture Not Found
```bash
# Problem: fixture 'xxx' not found
# Solution: Check conftest.py is in tests/ directory
# Verify fixture name matches exactly
```

#### Coverage Not Working
```bash
# Problem: Coverage not generated
# Solution: Install pytest-cov
pip install pytest-cov

# Verify app module is in PYTHONPATH
export PYTHONPATH=.
pytest --cov=app
```

#### Tests Hang or Timeout
```bash
# Problem: Tests hang indefinitely
# Solution: Add timeout to pytest
pytest --timeout=10  # Fail tests after 10 seconds
```

## Test Maintenance

### Regular Tasks

1. **Add tests for new features**
   - Write tests before or alongside new code
   - Maintain test-to-code ratio

2. **Update tests when refactoring**
   - Keep tests in sync with code changes
   - Update fixtures when models change

3. **Review test coverage**
   - Run coverage reports regularly
   - Aim for >90% coverage
   - Focus on meaningful coverage

4. **Clean up obsolete tests**
   - Remove tests for removed features
   - Update outdated test data

## Resources

### Documentation
- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pydantic Validation](https://docs.pydantic.dev/latest/concepts/validation/)

### Tools
- **pytest**: Testing framework
- **pytest-cov**: Coverage plugin
- **httpx**: HTTP client for integration tests
- **FastAPI TestClient**: Built-in testing utilities

## Summary

This testing guide provides:
- Complete test execution instructions
- Coverage analysis tools
- Debugging techniques
- CI/CD integration examples
- Best practices and patterns
- Troubleshooting solutions

The cart-service test suite includes **111 comprehensive tests** ensuring high quality and reliability across all application layers.

For detailed test information, see:
- `tests/README.md` - Test structure and organization
- `TEST_SUMMARY.md` - Complete test statistics
- `pytest.ini` - Test configuration
