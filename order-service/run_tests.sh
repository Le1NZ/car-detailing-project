#!/bin/bash

# Test runner script for order-service
# This script sets up a virtual environment and runs the test suite

set -e  # Exit on error

echo "=========================================="
echo "Order Service Test Suite Runner"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing test dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements-test.txt

echo ""
echo "=========================================="
echo "Running Tests"
echo "=========================================="
echo ""

# Run tests with coverage
python -m pytest

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo "HTML Coverage Report: htmlcov/index.html"
echo "XML Coverage Report: coverage.xml"
echo ""
echo "To view the HTML coverage report, run:"
echo "  open htmlcov/index.html"
echo ""
