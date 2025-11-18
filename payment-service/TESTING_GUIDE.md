# Testing Guide - Quick Reference

## Quick Start

### 1. Install Test Dependencies
```bash
pip install -r requirements-test.txt
```

### 2. Run All Tests
```bash
pytest
```

### 3. Run Tests with Coverage
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html  # View coverage report
```

## Common Test Commands

### Run Specific Test Types

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run only repository tests
pytest tests/unit/test_payment_repository.py

# Run only RabbitMQ publisher tests
pytest tests/unit/test_rabbitmq_publisher.py

# Run only service tests
pytest tests/unit/test_payment_service.py

# Run only model tests
pytest tests/unit/test_models.py

# Run only API endpoint tests
pytest tests/integration/test_api_endpoints.py
```

### Run Specific Test Cases

```bash
# Run specific test class
pytest tests/unit/test_payment_service.py::TestPaymentServiceInitiatePayment

# Run specific test method
pytest tests/unit/test_payment_service.py::TestPaymentServiceInitiatePayment::test_initiate_payment_success

# Run all tests matching a pattern
pytest -k "test_create"
pytest -k "test_rabbitmq"
pytest -k "not slow"
```

### Verbose and Debug Options

```bash
# Verbose output
pytest -v

# Extra verbose (show all test names)
pytest -vv

# Show print statements
pytest -s

# Show local variables on failure
pytest --showlocals

# Stop on first failure
pytest -x

# Run last failed tests only
pytest --lf

# Run with Python debugger on failure
pytest --pdb
```

### Coverage Options

```bash
# Basic coverage
pytest --cov=app

# Coverage with missing lines
pytest --cov=app --cov-report=term-missing

# Coverage with HTML report
pytest --cov=app --cov-report=html

# Coverage with XML report (for CI/CD)
pytest --cov=app --cov-report=xml

# Fail if coverage below threshold
pytest --cov=app --cov-fail-under=80
```

### Performance Options

```bash
# Run tests in parallel (faster)
pytest -n auto

# Run tests with timing
pytest --durations=10  # Show 10 slowest tests

# Run with minimal output
pytest -q
```

## Test Development Workflow

### 1. Test-Driven Development (TDD)

```bash
# 1. Write failing test
pytest tests/unit/test_new_feature.py -v

# 2. Implement feature
# ... edit code ...

# 3. Run test again
pytest tests/unit/test_new_feature.py -v

# 4. Refactor and verify
pytest tests/unit/test_new_feature.py -v
```

### 2. Running Tests During Development

```bash
# Watch mode (requires pytest-watch)
pip install pytest-watch
ptw

# Or use file watching with entr (macOS/Linux)
find . -name "*.py" | entr -c pytest tests/unit/
```

### 3. Pre-Commit Test Check

```bash
# Run all tests before commit
pytest -x --ff

# Run with coverage check
pytest --cov=app --cov-fail-under=80
```

## Understanding Test Output

### Success Example
```
tests/unit/test_payment_repository.py::TestPaymentRepositoryCreate::test_create_payment_success PASSED [1%]
```

### Failure Example
```
tests/unit/test_payment_service.py::TestPaymentServiceInitiatePayment::test_initiate_payment_success FAILED [50%]

FAILED tests/unit/test_payment_service.py::TestPaymentServiceInitiatePayment::test_initiate_payment_success - AssertionError: assert 'pending' == 'succeeded'
```

### Coverage Report Example
```
Name                                      Stmts   Miss  Cover   Missing
-----------------------------------------------------------------------
app/endpoints/payments.py                    45      2    96%   23-24
app/repositories/local_payment_repo.py       48      1    98%   105
app/services/payment_service.py              67      5    93%   72, 85-88
app/services/rabbitmq_publisher.py           35      0   100%
-----------------------------------------------------------------------
TOTAL                                       195      8    96%
```

## Testing Specific Scenarios

### Testing PaymentRepository

```bash
# Test create operations
pytest tests/unit/test_payment_repository.py::TestPaymentRepositoryCreate -v

# Test retrieve operations
pytest tests/unit/test_payment_repository.py::TestPaymentRepositoryRetrieve -v

# Test update operations
pytest tests/unit/test_payment_repository.py::TestPaymentRepositoryUpdate -v

# Test order checks
pytest tests/unit/test_payment_repository.py::TestPaymentRepositoryOrderChecks -v
```

### Testing RabbitMQ Publisher

```bash
# Test connection
pytest tests/unit/test_rabbitmq_publisher.py::TestRabbitMQPublisherConnection -v

# Test publishing
pytest tests/unit/test_rabbitmq_publisher.py::TestRabbitMQPublisherPublish -v

# Test edge cases
pytest tests/unit/test_rabbitmq_publisher.py::TestRabbitMQPublisherEdgeCases -v
```

### Testing Payment Service

```bash
# Test payment initiation
pytest tests/unit/test_payment_service.py::TestPaymentServiceInitiatePayment -v

# Test async processing
pytest tests/unit/test_payment_service.py::TestPaymentServiceProcessPaymentAsync -v

# Test complete flow
pytest tests/unit/test_payment_service.py::TestPaymentServiceIntegration -v
```

### Testing API Endpoints

```bash
# Test health endpoint
pytest tests/integration/test_api_endpoints.py::TestHealthEndpoint -v

# Test create payment endpoint
pytest tests/integration/test_api_endpoints.py::TestCreatePaymentEndpoint -v

# Test get payment status endpoint
pytest tests/integration/test_api_endpoints.py::TestGetPaymentStatusEndpoint -v

# Test complete workflow
pytest tests/integration/test_api_endpoints.py::TestPaymentWorkflow -v
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### GitLab CI Example

```yaml
test:
  image: python:3.11
  before_script:
    - pip install -r requirements.txt
    - pip install -r requirements-test.txt
  script:
    - pytest --cov=app --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

### Docker-based Testing

```bash
# Run tests in Docker
docker run --rm -v $(pwd):/app -w /app python:3.11 bash -c "
  pip install -r requirements-test.txt && pytest
"
```

## Troubleshooting

### Import Errors

```bash
# Ensure you're in the project root
cd /path/to/payment-service

# Set PYTHONPATH if needed
export PYTHONPATH=/path/to/payment-service:$PYTHONPATH
pytest
```

### Async Tests Not Running

```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Check pytest.ini has asyncio_mode = auto
cat pytest.ini | grep asyncio_mode
```

### Coverage Not Generated

```bash
# Ensure pytest-cov is installed
pip install pytest-cov

# Run with explicit coverage
pytest --cov=app --cov-report=term
```

### Tests Hanging

```bash
# Run with timeout
pip install pytest-timeout
pytest --timeout=10  # 10 seconds per test
```

### Flaky Tests

```bash
# Run multiple times to identify flaky tests
pip install pytest-repeat
pytest --count=10 tests/unit/test_payment_service.py
```

## Best Practices

### Writing New Tests

1. **Follow the AAA Pattern**
   ```python
   def test_example():
       # Arrange - set up test data
       data = {...}

       # Act - execute the code
       result = function(data)

       # Assert - verify the result
       assert result == expected
   ```

2. **Use Descriptive Names**
   ```python
   # Good
   def test_create_payment_returns_pending_status():
       ...

   # Bad
   def test_payment():
       ...
   ```

3. **Test One Thing**
   ```python
   # Good - tests one behavior
   def test_payment_creation_generates_unique_id():
       ...

   # Bad - tests multiple behaviors
   def test_payment_creation_and_status_update():
       ...
   ```

4. **Use Fixtures for Setup**
   ```python
   @pytest.fixture
   def sample_payment():
       return {"payment_id": "pay_123", "amount": 1000.00}

   def test_example(sample_payment):
       assert sample_payment["amount"] > 0
   ```

### Running Tests Efficiently

1. **Run affected tests only** during development
2. **Use parallel execution** for full test suites
3. **Run integration tests separately** from unit tests
4. **Set up pre-commit hooks** to run quick tests
5. **Use coverage reports** to identify untested code

## Useful Pytest Plugins

```bash
# Install useful plugins
pip install pytest-xdist      # Parallel execution
pip install pytest-timeout    # Test timeout
pip install pytest-watch      # Watch mode
pip install pytest-repeat     # Repeat tests
pip install pytest-randomly   # Random test order
pip install pytest-sugar      # Better output
```

## Getting Help

```bash
# Show pytest help
pytest --help

# Show available fixtures
pytest --fixtures

# Show available markers
pytest --markers

# Collect tests without running
pytest --collect-only
```

## Quick Reference Card

| Command | Description |
|---------|-------------|
| `pytest` | Run all tests |
| `pytest -v` | Verbose output |
| `pytest -x` | Stop on first failure |
| `pytest --lf` | Run last failed |
| `pytest -k "pattern"` | Run tests matching pattern |
| `pytest tests/unit/` | Run unit tests only |
| `pytest --cov=app` | Run with coverage |
| `pytest -n auto` | Run in parallel |
| `pytest --pdb` | Debug on failure |
| `pytest -s` | Show print output |

## Summary

- Use `./run_tests.sh` for quick test execution with coverage
- Use `pytest tests/unit/` for fast unit tests during development
- Use `pytest --cov=app` to check coverage
- Use `pytest -x --ff` before committing changes
- See `tests/README.md` for detailed documentation
