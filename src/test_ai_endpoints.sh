#!/bin/bash
# Comprehensive AI Endpoints Test Script
# Tests all AI-powered endpoints to verify fixes

BASE_URL="http://localhost:8000"
echo "=========================================="
echo "AI ENDPOINTS TEST SUITE"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    
    echo "Testing: $name"
    echo "  Endpoint: $method $endpoint"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME:%{time_total}" "${BASE_URL}${endpoint}")
    else
        response=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME:%{time_total}" -X "$method" "${BASE_URL}${endpoint}" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
    time_total=$(echo "$response" | grep "TIME" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE/d' | sed '/TIME/d')
    
    # Check if response is valid JSON
    echo "$body" | python3 -m json.tool > /dev/null 2>&1
    is_json=$?
    
    # Check for success indicators
    has_success=$(echo "$body" | grep -i "success" || true)
    has_error=$(echo "$body" | grep -i "\"error\"" || true)
    has_data=$(echo "$body" | grep -i "\"data\"" || true)
    
    echo "  HTTP Code: $http_code"
    echo "  Response Time: ${time_total}s"
    
    if [ "$http_code" = "200" ]; then
        if [ "$is_json" -eq 0 ]; then
            if [ -n "$has_error" ]; then
                echo -e "  Status: ${RED}FAILED${NC} - Response contains error"
                echo "  Response: $(echo "$body" | head -3)"
                FAILED=$((FAILED + 1))
            elif [ -n "$has_success" ] || [ -n "$has_data" ]; then
                echo -e "  Status: ${GREEN}PASSED${NC}"
                echo "  Response preview: $(echo "$body" | head -1 | cut -c1-100)..."
                PASSED=$((PASSED + 1))
            else
                echo -e "  Status: ${YELLOW}WARNING${NC} - No clear success indicator"
                echo "  Response preview: $(echo "$body" | head -1 | cut -c1-100)..."
                PASSED=$((PASSED + 1))
            fi
        else
            echo -e "  Status: ${RED}FAILED${NC} - Invalid JSON"
            echo "  Response: $(echo "$body" | head -3)"
            FAILED=$((FAILED + 1))
        fi
    else
        echo -e "  Status: ${RED}FAILED${NC} - HTTP $http_code"
        echo "  Response: $(echo "$body" | head -3)"
        FAILED=$((FAILED + 1))
    fi
    echo ""
}

echo "1. TESTING SKILL ANALYSIS (Was failing with truncation)"
echo "--------------------------------------------------------"
test_endpoint "Skill Analysis - Employee 9186" "GET" "/api/skills/analysis/9186"
test_endpoint "Skill Analysis - Employee 14607" "GET" "/api/skills/analysis/14607"
echo ""

echo "2. TESTING HACKATHON AI ENDPOINTS (Have fallback)"
echo "--------------------------------------------------------"
test_endpoint "Career Path - Employee 9186" "GET" "/api/hackathons/employee/9186/career-path"
test_endpoint "5-Year Forecast" "GET" "/api/hackathons/forecast/skills-5y"
echo ""

echo "3. TESTING OTHER AI ENDPOINTS"
echo "--------------------------------------------------------"
test_endpoint "Team Intel - SE" "GET" "/api/ai/team-intel/SE"
test_endpoint "Employee Intel - 9186" "GET" "/api/ai/employee-intel/9186"
test_endpoint "Succession Intel - SE" "GET" "/api/ai/succession-intel/SE"
echo ""

echo "4. TESTING CAREER COACH CHAT"
echo "--------------------------------------------------------"
test_endpoint "Career Chat" "POST" "/api/ai/career-chat" '{"message": "What skills should I develop?"}'
echo ""

echo "=========================================="
echo "TEST RESULTS"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo "Total: $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}ALL TESTS PASSED! ✅${NC}"
    exit 0
else
    echo -e "${RED}SOME TESTS FAILED! ❌${NC}"
    exit 1
fi

