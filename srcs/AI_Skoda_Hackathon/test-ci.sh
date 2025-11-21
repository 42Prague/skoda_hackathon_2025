#!/bin/bash

# Test script for CI/CD workflows
# This script runs basic health checks on the application

set -e

echo "🧪 Running Application Tests..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "Testing $name... "
    
    response_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
    
    if [ "$response_code" = "$expected_code" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $response_code)"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (Expected $expected_code, got $response_code)"
        ((FAILED++))
        return 1
    fi
}

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5

# Test Backend
echo ""
echo "🔧 Testing Backend API..."
test_endpoint "Health Check" "http://localhost:3000/health"
test_endpoint "API Health Check" "http://localhost:3000/api/health"
test_endpoint "API Root" "http://localhost:3000/api"

# Test Login Endpoint
echo ""
echo "🔐 Testing Authentication..."
echo -n "Testing Login Endpoint... "
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"martin.svoboda@skoda.cz","password":"password123"}')

if echo "$LOGIN_RESPONSE" | grep -q "token"; then
    echo -e "${GREEN}✓ PASSED${NC} (Login successful, token received)"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC} (No token in response)"
    ((FAILED++))
fi

# Test Frontend
echo ""
echo "🎨 Testing Frontend..."
test_endpoint "Frontend Home" "http://localhost:8080"
test_endpoint "Frontend Assets" "http://localhost:8080/assets/" 404

# Test Database
echo ""
echo "💾 Testing Database Connection..."
echo -n "Testing Database... "
DB_TEST=$(docker-compose exec -T postgres pg_isready -U skillbridge 2>&1)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PASSED${NC} (Database is ready)"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC} (Database not ready)"
    ((FAILED++))
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Results Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    exit 1
fi
