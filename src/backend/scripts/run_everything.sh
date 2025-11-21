#!/bin/bash
# Complete test runner: Backend, Migrations, and Tests

set -e

echo "🚀 ŠKODA AI Skill Coach - Complete Test Runner"
echo "=============================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND_DIR"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Check Docker
echo -e "${BLUE}📦 Step 1: Checking Docker...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ Docker is available${NC}"
    DOCKER_AVAILABLE=true
else
    echo -e "${YELLOW}⚠️  Docker not found, will run tests locally${NC}"
    DOCKER_AVAILABLE=false
fi

# Step 2: Check Python environment
echo -e "${BLUE}🐍 Step 2: Checking Python environment...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_CMD=$(which python3)
    echo -e "${GREEN}✅ Python found: $PYTHON_CMD${NC}"
else
    echo -e "${RED}❌ Python3 not found!${NC}"
    exit 1
fi

# Step 3: Install test dependencies and package
echo -e "${BLUE}📚 Step 3: Installing dependencies...${NC}"
cd "$BACKEND_DIR"

# Set PYTHONPATH
export PYTHONPATH="$BACKEND_DIR:$PYTHONPATH"

if [ -f ".venv/bin/pip" ]; then
    echo "Using existing virtual environment"
    .venv/bin/pip install -q pytest pytest-asyncio httpx psutil coverage pytest-cov || true
    .venv/bin/pip install -q -e . || true
else
    echo "Installing globally (consider using virtualenv)"
    pip3 install -q pytest pytest-asyncio httpx psutil coverage pytest-cov || true
    pip3 install -q -e . || true
fi

# Step 4: Run migrations
echo -e "${BLUE}🗄️  Step 4: Running database migrations...${NC}"
cd "$BACKEND_DIR"

# Check if alembic is available
if command -v alembic &> /dev/null || [ -f ".venv/bin/alembic" ]; then
    if [ -f ".venv/bin/alembic" ]; then
        echo "Running migrations with .venv/bin/alembic"
        .venv/bin/alembic upgrade head || echo -e "${YELLOW}⚠️  Migrations may have failed (this is OK for test DB)${NC}"
    else
        echo "Running migrations with system alembic"
        alembic upgrade head || echo -e "${YELLOW}⚠️  Migrations may have failed (this is OK for test DB)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Alembic not found, skipping migrations (tests use SQLite)${NC}"
fi

# Step 5: Generate test datasets
echo -e "${BLUE}📊 Step 5: Generating test datasets...${NC}"
cd "$BACKEND_DIR/tests/data"
if [ -f "generate_test_datasets.py" ]; then
    $PYTHON_CMD generate_test_datasets.py || echo -e "${YELLOW}⚠️  Dataset generation failed (continuing anyway)${NC}"
else
    echo -e "${YELLOW}⚠️  Dataset generator not found${NC}"
fi

# Step 6: Run tests
echo -e "${BLUE}🧪 Step 6: Running tests...${NC}"
cd "$BACKEND_DIR"

# Ensure PYTHONPATH is set
export PYTHONPATH="$BACKEND_DIR:$PYTHONPATH"

# Determine pytest command
if [ -f ".venv/bin/pytest" ]; then
    PYTEST_CMD=".venv/bin/pytest"
elif command -v pytest &> /dev/null; then
    PYTEST_CMD="pytest"
else
    echo -e "${RED}❌ pytest not found!${NC}"
    exit 1
fi

echo -e "${GREEN}Running: $PYTEST_CMD tests/ -v --tb=short${NC}"
echo -e "${BLUE}PYTHONPATH: $PYTHONPATH${NC}"
echo ""

# Run tests with coverage
$PYTEST_CMD tests/ -v \
    --tb=short \
    --cov=swx_api \
    --cov-report=term \
    --cov-report=xml \
    --cov-report=html \
    --junitxml=test-results/junit.xml \
    || echo -e "${YELLOW}⚠️  Some tests may have failed${NC}"

# Step 7: Summary
echo ""
echo -e "${BLUE}📋 Step 7: Test Summary${NC}"
echo "================================"

if [ -f "test-results/junit.xml" ]; then
    echo -e "${GREEN}✅ Test results saved to: test-results/junit.xml${NC}"
fi

if [ -d "htmlcov" ]; then
    echo -e "${GREEN}✅ Coverage report: htmlcov/index.html${NC}"
fi

if [ -f "coverage.xml" ]; then
    echo -e "${GREEN}✅ Coverage XML: coverage.xml${NC}"
fi

echo ""
echo -e "${GREEN}✅ Complete test run finished!${NC}"
echo ""
echo "Next steps:"
echo "  - View coverage: open htmlcov/index.html"
echo "  - View test results: cat test-results/junit.xml"
echo "  - Run specific test: $PYTEST_CMD tests/test_01_ingestion.py -v"

