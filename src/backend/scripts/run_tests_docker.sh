#!/bin/bash
# Script to run tests in Docker containers

set -e

echo "🧪 Running tests in Docker containers..."

# Navigate to project root
cd "$(dirname "$0")/../.."

# Build and run test containers
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Copy test results if needed
if [ -d "backend/test-results" ]; then
    echo "✅ Test results available in backend/test-results/"
fi

echo "✅ Tests completed!"

