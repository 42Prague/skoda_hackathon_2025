#!/bin/bash
# Quick test script for API endpoints with authentication

# Get token from environment or .env file
if [ -z "$DEMO_API_TOKEN" ]; then
    if [ -f .env ]; then
        export DEMO_API_TOKEN=$(grep "^DEMO_API_TOKEN" .env | cut -d '=' -f2 | tr -d '"' | tr -d "'")
    else
        echo "ERROR: DEMO_API_TOKEN not found in environment or .env file"
        echo "Please set DEMO_API_TOKEN in .env or export it:"
        echo "  export DEMO_API_TOKEN='your-token-here'"
        exit 1
    fi
fi

# Check if backend is running
if ! curl -s http://localhost:8000/healthz > /dev/null 2>&1; then
    echo "ERROR: Backend not running at http://localhost:8000"
    echo "Please start the backend: docker compose up -d backend"
    exit 1
fi

# API Base URL
BASE_URL="http://localhost:8000"

echo "==================================="
echo "API Testing with Authentication"
echo "==================================="
echo "Token: ${DEMO_API_TOKEN:0:8}... (masked)"
echo "Base URL: $BASE_URL"
echo ""

# Test 1: Health Check (No Auth)
echo "Test 1: Health Check (No Auth Required)"
echo "----------------------------------------"
curl -s -X GET "$BASE_URL/healthz" | jq '.' || echo "Response received"
echo ""
echo ""

# Test 2: Employee Intel (Auth Required)
echo "Test 2: Employee Intel (Auth Required)"
echo "--------------------------------------"
EMPLOYEE_ID="4241"
curl -s -X GET "$BASE_URL/api/ai/employee-intel/$EMPLOYEE_ID" \
  -H "Authorization: Bearer $DEMO_API_TOKEN" \
  -H "Content-Type: application/json" | jq '.' || echo "Response received"
echo ""
echo ""

# Test 3: Team Intel (Auth Required)
echo "Test 3: Team Intel (Auth Required)"
echo "-----------------------------------"
DEPARTMENT="SE"
curl -s -X GET "$BASE_URL/api/ai/team-intel/$DEPARTMENT" \
  -H "Authorization: Bearer $DEMO_API_TOKEN" \
  -H "Content-Type: application/json" | jq '.' || echo "Response received"
echo ""
echo ""

# Test 4: Career Chat (Auth Required)
echo "Test 4: Career Chat (Auth Required)"
echo "------------------------------------"
curl -s -X POST "$BASE_URL/api/ai/career-chat" \
  -H "Authorization: Bearer $DEMO_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "4241",
    "message": "What skills should I develop?",
    "context": {}
  }' | jq '.' || echo "Response received"
echo ""
echo ""

echo "==================================="
echo "Testing Complete"
echo "==================================="
echo ""
echo "If you see 401 errors, check your DEMO_API_TOKEN"
echo "If you see 200 responses, authentication is working!"
echo ""
echo "To view all available endpoints, visit:"
echo "  $BASE_URL/docs"

