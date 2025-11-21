#!/bin/bash
# Test Production Docker Setup
# Verifies all services are working correctly

set -e

echo "🧪 Testing Production Docker Setup"
echo "==================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0

test_check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $1"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}: $1"
        ((FAILED++))
        return 1
    fi
}

# 1. Check Docker is running
echo "1. Checking Docker..."
docker info > /dev/null 2>&1
test_check "Docker is running"

# 2. Check services are up
echo ""
echo "2. Checking services..."
docker-compose ps | grep -q "Up" || {
    echo -e "${YELLOW}⚠️  Services not running. Starting them...${NC}"
    docker-compose up -d
    sleep 10
}

# 3. Check backend health
echo ""
echo "3. Testing backend health endpoint..."
sleep 5
curl -f http://localhost:8000/healthz > /dev/null 2>&1
test_check "Backend health check"

# 4. Check API docs
echo ""
echo "4. Testing API documentation..."
curl -f http://localhost:8000/docs > /dev/null 2>&1
test_check "API documentation accessible"

# 5. Check database connection
echo ""
echo "5. Testing database connection..."
docker-compose exec -T backend python -c "
import asyncio
import asyncpg
import os

async def test():
    try:
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'db'),
            port=int(os.getenv('DB_PORT', 5432)),
            user=os.getenv('DB_USER', 'swx_user'),
            password=os.getenv('DB_PASSWORD', 'changeme'),
            database=os.getenv('DB_NAME', 'swx_db')
        )
        await conn.close()
        exit(0)
    except Exception as e:
        print(f'Error: {e}')
        exit(1)

asyncio.run(test())
" > /dev/null 2>&1
test_check "Database connection"

# 6. Check migrations
echo ""
echo "6. Checking database migrations..."
docker-compose exec -T backend alembic current > /dev/null 2>&1
test_check "Database migrations"

# 7. Test API endpoint
echo ""
echo "7. Testing API endpoint..."
curl -f http://localhost:8000/api/ingestion/datasets > /dev/null 2>&1
test_check "API endpoint (datasets)"

# 8. Check Adminer
echo ""
echo "8. Testing Adminer..."
curl -f http://localhost:8080 > /dev/null 2>&1
test_check "Adminer accessible"

# 9. Check pgAdmin
echo ""
echo "9. Testing pgAdmin..."
curl -f http://localhost:5050 > /dev/null 2>&1
test_check "pgAdmin accessible"

# Summary
echo ""
echo "==================================="
echo "📊 Test Summary"
echo "==================================="
echo -e "${GREEN}Passed: ${PASSED}${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: ${FAILED}${NC}"
    echo ""
    echo "Check logs: docker-compose logs"
    exit 1
else
    echo -e "${GREEN}Failed: ${FAILED}${NC}"
    echo ""
    echo "🎉 All tests passed! Production setup is working correctly."
    exit 0
fi

