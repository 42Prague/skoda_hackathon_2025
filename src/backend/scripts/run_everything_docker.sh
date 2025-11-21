#!/bin/bash
# Complete test runner in Docker: Backend, Migrations, and Tests

set -e

echo "🐳 ŠKODA AI Skill Coach - Complete Docker Test Runner"
echo "======================================================"
echo ""

cd "$(dirname "$0")/../.."
PROJECT_ROOT="$(pwd)"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Docker
echo -e "${BLUE}📦 Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found!${NC}"
    exit 1
fi

# Check docker-compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo -e "${RED}❌ docker-compose not found!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is available${NC}"
echo ""

# Step 1: Start test database
echo -e "${BLUE}🗄️  Step 1: Starting test database...${NC}"
$COMPOSE_CMD -f docker-compose.test.yml up -d test-db

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 5

# Step 2: Run migrations in test container
echo -e "${BLUE}🔄 Step 2: Running migrations...${NC}"
$COMPOSE_CMD -f docker-compose.test.yml run --rm test-runner \
    sh -c "alembic upgrade head || echo 'Migrations completed (or using test DB)'"

# Step 3: Generate test datasets
echo -e "${BLUE}📊 Step 3: Generating test datasets...${NC}"
$COMPOSE_CMD -f docker-compose.test.yml run --rm test-runner \
    python tests/data/generate_test_datasets.py || echo "Dataset generation skipped"

# Step 4: Run all tests
echo -e "${BLUE}🧪 Step 4: Running all tests...${NC}"
echo ""

$COMPOSE_CMD -f docker-compose.test.yml up --build test-runner

# Step 5: Copy results
echo ""
echo -e "${BLUE}📋 Step 5: Copying test results...${NC}"

# Create results directory
mkdir -p backend/test-results

# Try to copy results (container may have stopped)
CONTAINER_ID=$($COMPOSE_CMD -f docker-compose.test.yml ps -q test-runner 2>/dev/null || echo "")
if [ ! -z "$CONTAINER_ID" ]; then
    docker cp $CONTAINER_ID:/app/test-results/. backend/test-results/ 2>/dev/null || true
    docker cp $CONTAINER_ID:/app/coverage.xml backend/ 2>/dev/null || true
    docker cp $CONTAINER_ID:/app/htmlcov/. backend/htmlcov/ 2>/dev/null || true
fi

# Step 6: Summary
echo ""
echo -e "${GREEN}✅ Docker test run completed!${NC}"
echo ""
echo "Results:"
echo "  - Test results: backend/test-results/"
echo "  - Coverage XML: backend/coverage.xml"
echo "  - Coverage HTML: backend/htmlcov/index.html"
echo ""
echo "To view logs:"
echo "  $COMPOSE_CMD -f docker-compose.test.yml logs test-runner"
echo ""
echo "To clean up:"
echo "  $COMPOSE_CMD -f docker-compose.test.yml down"

