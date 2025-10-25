#!/bin/bash

# Test runner script for the backend

set -e

echo "Running backend tests..."
echo ""

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
pip install -q -r requirements.txt

# Run tests
echo "Running pytest..."
pytest tests/ -v --tb=short

echo ""
echo "All tests completed!"
