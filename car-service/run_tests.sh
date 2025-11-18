#!/bin/bash

# Test runner script for car-service
# This script sets up a virtual environment and runs all tests

set -e

echo "=========================================="
echo "Car Service Test Runner"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q -r requirements.txt

# Run tests based on argument
if [ "$1" == "unit" ]; then
    echo -e "${GREEN}Running unit tests only...${NC}"
    pytest -m unit -v
elif [ "$1" == "integration" ]; then
    echo -e "${GREEN}Running integration tests only...${NC}"
    pytest -m integration -v
elif [ "$1" == "coverage" ]; then
    echo -e "${GREEN}Running all tests with coverage...${NC}"
    pytest --cov=app --cov-report=html --cov-report=term-missing
    echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
elif [ "$1" == "verbose" ]; then
    echo -e "${GREEN}Running all tests with verbose output...${NC}"
    pytest -v -s
elif [ "$1" == "quick" ]; then
    echo -e "${GREEN}Running quick test (first failure stops)...${NC}"
    pytest -x
else
    echo -e "${GREEN}Running all tests...${NC}"
    pytest
fi

# Deactivate virtual environment
deactivate

echo -e "${GREEN}=========================================="
echo -e "Tests completed!"
echo -e "==========================================${NC}"
