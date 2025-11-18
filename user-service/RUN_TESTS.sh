#!/bin/bash

# Quick test runner script for user-service
# This script provides convenient commands to run different test suites

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "pytest.ini" ]; then
    print_error "pytest.ini not found. Please run this script from the user-service directory."
    exit 1
fi

# Check if test dependencies are installed
if ! python3 -c "import pytest" 2>/dev/null; then
    print_warning "Test dependencies not found. Installing..."
    pip install -r requirements-test.txt
fi

# Parse command line arguments
case "${1:-all}" in
    all)
        print_message "Running all tests..."
        pytest -v
        ;;

    unit)
        print_message "Running unit tests only..."
        pytest -v tests/unit/
        ;;

    integration)
        print_message "Running integration tests only..."
        pytest -v tests/integration/
        ;;

    coverage)
        print_message "Running tests with coverage report..."
        pytest --cov=app --cov-report=term-missing --cov-report=html
        print_success "Coverage report generated in htmlcov/index.html"
        ;;

    fast)
        print_message "Running fast unit tests only (no integration)..."
        pytest -v tests/unit/ -x
        ;;

    watch)
        print_message "Running tests in watch mode..."
        print_warning "Press Ctrl+C to stop"
        pytest-watch
        ;;

    specific)
        if [ -z "$2" ]; then
            print_error "Please specify a test file or function"
            echo "Usage: ./RUN_TESTS.sh specific tests/unit/test_service.py"
            exit 1
        fi
        print_message "Running specific test: $2"
        pytest -v "$2"
        ;;

    install)
        print_message "Installing test dependencies..."
        pip install -r requirements.txt
        pip install -r requirements-test.txt
        print_success "Dependencies installed successfully"
        ;;

    clean)
        print_message "Cleaning test artifacts..."
        rm -rf .pytest_cache
        rm -rf htmlcov
        rm -rf .coverage
        rm -rf **/__pycache__
        print_success "Cleaned test artifacts"
        ;;

    help|--help|-h)
        echo "User Service Test Runner"
        echo ""
        echo "Usage: ./RUN_TESTS.sh [command]"
        echo ""
        echo "Commands:"
        echo "  all           Run all tests (default)"
        echo "  unit          Run unit tests only"
        echo "  integration   Run integration tests only"
        echo "  coverage      Run tests with coverage report"
        echo "  fast          Run unit tests only, stop on first failure"
        echo "  specific      Run specific test file/function"
        echo "  install       Install test dependencies"
        echo "  clean         Clean test artifacts"
        echo "  help          Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./RUN_TESTS.sh                                    # Run all tests"
        echo "  ./RUN_TESTS.sh unit                               # Run unit tests"
        echo "  ./RUN_TESTS.sh coverage                           # Run with coverage"
        echo "  ./RUN_TESTS.sh specific tests/unit/test_service.py # Run specific file"
        ;;

    *)
        print_error "Unknown command: $1"
        echo "Run './RUN_TESTS.sh help' for usage information"
        exit 1
        ;;
esac
