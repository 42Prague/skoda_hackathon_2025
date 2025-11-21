#!/bin/bash
# Script to run tests locally (without Docker)

set -e

echo "🧪 Running tests locally..."

cd "$(dirname "$0")/.."

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest is not installed. Installing..."
    pip install pytest pytest-asyncio httpx psutil coverage pytest-cov
fi

# Run tests
echo "Running pytest..."
pytest tests/ -v --tb=short --cov=swx_api --cov-report=xml --cov-report=html --cov-report=term

echo "✅ Tests completed!"
echo "📊 Coverage report: htmlcov/index.html"

