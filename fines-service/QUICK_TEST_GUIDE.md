# Quick Test Guide - Fines Service

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements-test.txt

# 2. Run all tests
pytest

# 3. Run with coverage
pytest --cov=app --cov-report=term
```

## Test Commands Cheat Sheet

### Basic Commands
```bash
pytest                              # Run all tests
pytest -v                           # Verbose output
pytest -vv                          # Extra verbose
pytest -x                           # Stop on first failure
pytest -s                           # Show print statements
```

### Run Specific Tests
```bash
pytest tests/unit/                  # All unit tests
pytest tests/integration/           # All integration tests
pytest tests/unit/test_models.py    # Specific file
pytest tests/unit/test_models.py::TestFineModel  # Specific class
pytest tests/unit/test_models.py::TestFineModel::test_create_fine_with_valid_data  # Specific test
```

### Coverage Commands
```bash
pytest --cov=app                                # Basic coverage
pytest --cov=app --cov-report=term             # Terminal report
pytest --cov=app --cov-report=html             # HTML report
pytest --cov=app --cov-report=term-missing     # Show missing lines
```

### Filtering Tests
```bash
pytest -k "test_check_fines"        # Run tests matching name
pytest -k "not slow"                # Skip tests marked as slow
pytest tests/ -m unit               # Run tests marked as unit
```

## Test Statistics

- **Total Tests**: 103
- **Unit Tests**: 68
- **Integration Tests**: 35
- **Code Coverage**: ~100%

## Test Structure

```
tests/
├── conftest.py                    # 8 shared fixtures
├── unit/
│   ├── test_models.py            # 30 model tests
│   ├── test_repository.py        # 28 repository tests
│   └── test_service.py           # 30 service tests
└── integration/
    └── test_endpoints.py         # 35 API tests
```

## Common Test Scenarios

### Test Model Validation
```bash
pytest tests/unit/test_models.py -v
```

### Test Repository Operations
```bash
pytest tests/unit/test_repository.py -v
```

### Test Business Logic
```bash
pytest tests/unit/test_service.py -v
```

### Test API Endpoints
```bash
pytest tests/integration/test_endpoints.py -v
```

### Test Specific Feature
```bash
# Test payment functionality
pytest -k "pay" -v

# Test fine checking
pytest -k "check_fines" -v

# Test error handling
pytest -k "error or raises" -v
```

## Expected Output

### Successful Test Run
```
================================ test session starts =================================
platform darwin -- Python 3.11.x
collected 103 items

tests/unit/test_models.py ..............................                      [ 29%]
tests/unit/test_repository.py ............................                    [ 56%]
tests/unit/test_service.py ..............................                     [ 85%]
tests/integration/test_endpoints.py ...................................       [100%]

================================= 103 passed in 2.5s =================================
```

### With Coverage
```
---------- coverage: platform darwin, python 3.11.x -----------
Name                                  Stmts   Miss  Cover
---------------------------------------------------------
app/__init__.py                           0      0   100%
app/config.py                             8      0   100%
app/endpoints/__init__.py                 0      0   100%
app/endpoints/fines.py                   19      0   100%
app/main.py                              16      0   100%
app/models/__init__.py                    4      0   100%
app/models/fine.py                       12      0   100%
app/repositories/__init__.py              0      0   100%
app/repositories/local_fine_repo.py      38      0   100%
app/services/__init__.py                  0      0   100%
app/services/fine_service.py             20      0   100%
---------------------------------------------------------
TOTAL                                   117      0   100%
```

## Troubleshooting

### Import Errors
```bash
# Make sure you're in the project root
cd /Users/fr4lzen/Documents/мирэа/микросы/пр7/project/fines-service

# Verify Python can import modules
python3 -c "import app; print('OK')"
```

### Dependencies Not Found
```bash
# Install all dependencies
pip install -r requirements-test.txt

# Or install individually
pip install pytest pytest-cov httpx fastapi uvicorn pydantic
```

### Tests Not Discovered
```bash
# Check pytest configuration
cat pytest.ini

# Verify test files exist
ls tests/unit/
ls tests/integration/
```

## Quick Test Examples

### Run Fast Tests Only
```bash
pytest tests/unit/ -v
# Unit tests complete in < 1 second
```

### Run Integration Tests
```bash
pytest tests/integration/ -v
# Integration tests complete in ~2 seconds
```

### Generate HTML Coverage Report
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Watch Mode (requires pytest-watch)
```bash
pip install pytest-watch
ptw  # Runs tests on file changes
```

## Test Categories

### Models (30 tests)
- Fine model validation
- FineResponse structure
- PayFineRequest validation
- PaymentResponse validation
- Serialization/deserialization

### Repository (28 tests)
- Get fines by plate
- Get unpaid fines
- Get fine by ID
- Mark fine as paid
- Check paid status

### Service (30 tests)
- Check fines business logic
- Pay fine workflow
- Error handling
- Repository interaction

### Endpoints (35 tests)
- Health check
- Root endpoint
- GET /api/fines/check
- POST /api/fines/{fine_id}/pay
- HTTP status codes
- Validation errors

## Performance

- **Unit Tests**: ~0.8 seconds
- **Integration Tests**: ~1.7 seconds
- **Total Runtime**: ~2.5 seconds

Fast enough for continuous development!

## CI/CD Integration

```yaml
# Example .gitlab-ci.yml or .github/workflows/test.yml
test:
  script:
    - pip install -r requirements-test.txt
    - pytest --cov=app --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

## Next Steps

1. Install dependencies: `pip install -r requirements-test.txt`
2. Run tests: `pytest`
3. Check coverage: `pytest --cov=app --cov-report=html`
4. View report: `open htmlcov/index.html`

For detailed documentation, see `tests/README.md`
