# Testing Quick Start Guide

Quick reference for running tests in the support-service.

## Setup (One Time)

```bash
cd /Users/fr4lzen/Documents/мирэа/микросы/пр7/project/support-service/

# Install test dependencies
pip install -r requirements-test.txt
```

## Common Commands

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=term-missing
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
pytest tests/unit/test_models.py
pytest tests/unit/test_repository.py
pytest tests/unit/test_service.py
pytest tests/integration/test_endpoints.py
```

### Run Specific Test Class
```bash
pytest tests/unit/test_models.py::TestCreateTicketRequest
pytest tests/integration/test_endpoints.py::TestCreateTicketEndpoint
```

### Run Specific Test Function
```bash
pytest tests/unit/test_models.py::TestCreateTicketRequest::test_create_ticket_request_valid_data
```

### Run with Different Verbosity
```bash
# Quiet (minimal output)
pytest -q

# Verbose (recommended)
pytest -v

# Extra verbose with local variables
pytest -vv -l

# Show print statements
pytest -s
```

### Run and Generate HTML Coverage Report
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

### Run Tests in Watch Mode (requires pytest-watch)
```bash
pip install pytest-watch
ptw  # Runs tests on file changes
```

### Run Tests in Parallel (requires pytest-xdist)
```bash
pip install pytest-xdist
pytest -n auto  # Use all CPU cores
```

## Expected Results

When all tests pass, you should see:
```
======================== 99 passed in X.XXs ========================
```

## Test Coverage Breakdown

| Component | Test File | Test Count |
|-----------|-----------|------------|
| Models | test_models.py | 40 tests |
| Repository | test_repository.py | 30 tests |
| Service | test_service.py | 17 tests |
| API Endpoints | test_endpoints.py | 47 tests |
| **Total** | | **99 tests** |

## Troubleshooting

### Import Errors
Make sure you're in the service root directory:
```bash
cd /Users/fr4lzen/Documents/мирэа/микросы/пр7/project/support-service/
pytest
```

### Dependencies Not Installed
```bash
pip install -r requirements-test.txt
```

### Coverage Not Working
```bash
pip install pytest-cov
```

### Tests Failing
1. Check if service code was modified
2. Read the test failure message
3. Run specific failing test with verbose output: `pytest -vv test_file.py::test_name`
4. Check if fixtures are working: `pytest --fixtures`

## Test Organization

```
tests/
├── unit/              # Tests isolated components
│   ├── test_models.py       # Pydantic validation
│   ├── test_repository.py   # Data storage logic
│   └── test_service.py      # Business logic
└── integration/       # Tests API endpoints
    └── test_endpoints.py    # HTTP requests/responses
```

## Quick Test Examples

### Example 1: Test Model Validation
```python
def test_create_ticket_request_valid_data():
    """Test CreateTicketRequest with valid data."""
    request = CreateTicketRequest(
        subject="Test Subject",
        message="Test Message"
    )
    assert request.subject == "Test Subject"
```

### Example 2: Test Repository
```python
def test_create_ticket(repository, sample_user_id):
    """Test creating a ticket."""
    ticket = repository.create_ticket(
        user_id=sample_user_id,
        subject="Test",
        message="Message"
    )
    assert ticket.status == "open"
```

### Example 3: Test API Endpoint
```python
def test_create_ticket_success(client):
    """Test successful ticket creation."""
    response = client.post("/api/support/tickets", json={
        "subject": "Test",
        "message": "Message"
    })
    assert response.status_code == 201
```

## Pre-Commit Checklist

Before committing code:
```bash
# 1. Run all tests
pytest

# 2. Check coverage
pytest --cov=app --cov-report=term-missing

# 3. Ensure coverage is >90%
# (Look at coverage percentage in output)

# 4. Run code quality checks (if configured)
flake8 app/
black --check app/
isort --check app/
mypy app/
```

## Additional Documentation

- `tests/README.md` - Comprehensive test documentation
- `TEST_SUMMARY.md` - Detailed test summary
- `pytest.ini` - Pytest configuration

## Support

For more information about specific tests, refer to:
- Test docstrings (in test files)
- `tests/README.md` for detailed documentation
- `conftest.py` for available fixtures
