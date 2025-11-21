#!/bin/bash
# Run All Async Tests for ŠKODA Skill Coach

set -e

echo "🧪 Running All Async Tests for ŠKODA Skill Coach"
echo "=================================================="
echo ""

cd "$(dirname "$0")"

# Check if pytest is installed
if ! python -m pytest --version > /dev/null 2>&1; then
    echo "❌ pytest is not installed. Installing..."
    pip install pytest pytest-asyncio httpx
fi

# Check if pytest-asyncio is installed
if ! python -c "import pytest_asyncio" 2>/dev/null; then
    echo "❌ pytest-asyncio is not installed. Installing..."
    pip install pytest-asyncio
fi

echo "📦 Test Suites:"
echo "  1. Repository Tests (test_repositories_async.py)"
echo "  2. Service Tests (test_services_async.py)"
echo "  3. Route Tests (test_routes_async.py)"
echo "  4. LLM Client Tests (test_llm_client_async.py)"
echo "  5. File I/O Tests (test_file_io_async.py)"
echo "  6. Integration Tests (test_integration_async.py)"
echo ""

# Run all tests
echo "🚀 Running all tests..."
python -m pytest swx_api/app/tests/ \
    -v \
    --asyncio-mode=auto \
    --tb=short \
    --cov=swx_api \
    --cov-report=term-missing \
    --cov-report=html \
    "$@"

echo ""
echo "✅ Tests completed!"
echo "📊 Coverage report generated in htmlcov/index.html"

