#!/bin/bash

# Test execution script for payment-service
# This script sets up the environment and runs the test suite

set -e  # Exit on error

echo "=========================================="
echo "Payment Service Test Suite"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q -r requirements-test.txt

echo ""
echo "=========================================="
echo "Running Test Suite"
echo "=========================================="
echo ""

# Run tests with coverage
pytest -v \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-report=xml

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""

# Show coverage summary
coverage report --show-missing

echo ""
echo "=========================================="
echo "HTML Coverage Report"
echo "=========================================="
echo "Coverage report generated: htmlcov/index.html"
echo ""

# Deactivate virtual environment
deactivate || true

echo "Tests completed successfully!"
