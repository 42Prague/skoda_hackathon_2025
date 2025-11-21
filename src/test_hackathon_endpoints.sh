#!/bin/bash
# Test script for all 5 hackathon endpoints

BASE_URL="http://localhost:8000"
echo "=== Testing All 5 Hackathon Endpoints ==="
echo ""

# Test 1: Team Capability
echo "1. Testing Team Capability..."
curl -s "${BASE_URL}/api/hackathons/team/SE/capability" -w "\nHTTP: %{http_code}\n" | python3 -m json.tool 2>&1 | head -50
echo ""
echo "---"
echo ""

# Test 2: Risk Radar
echo "2. Testing Risk Radar..."
curl -s "${BASE_URL}/api/hackathons/team/SE/risk-radar" -w "\nHTTP: %{http_code}\n" | python3 -m json.tool 2>&1 | head -50
echo ""
echo "---"
echo ""

# Test 3: Promotion Readiness
echo "3. Testing Promotion Readiness..."
curl -s "${BASE_URL}/api/hackathons/team/SE/promotion-readiness" -w "\nHTTP: %{http_code}\n" | python3 -m json.tool 2>&1 | head -50
echo ""
echo "---"
echo ""

# Test 4: Career Path
echo "4. Testing Career Path..."
curl -s "${BASE_URL}/api/hackathons/employee/9186/career-path" -w "\nHTTP: %{http_code}\n" | python3 -m json.tool 2>&1 | head -50
echo ""
echo "---"
echo ""

# Test 5: 5-Year Forecast
echo "5. Testing 5-Year Forecast..."
curl -s "${BASE_URL}/api/hackathons/forecast/skills-5y" -w "\nHTTP: %{http_code}\n" | python3 -m json.tool 2>&1 | head -50
echo ""
echo "---"
echo ""

# Test HTTP Status Codes
echo "=== HTTP Status Codes ==="
for endpoint in "/api/hackathons/team/SE/capability" "/api/hackathons/team/SE/risk-radar" "/api/hackathons/team/SE/promotion-readiness" "/api/hackathons/employee/9186/career-path" "/api/hackathons/forecast/skills-5y"; do
    code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}${endpoint}")
    echo "${endpoint}: HTTP ${code}"
done
echo ""

# Test Response Times
echo "=== Response Times ==="
for endpoint in "/api/hackathons/team/SE/capability" "/api/hackathons/team/SE/risk-radar" "/api/hackathons/team/SE/promotion-readiness" "/api/hackathons/employee/9186/career-path" "/api/hackathons/forecast/skills-5y"; do
    time=$(curl -s -o /dev/null -w "%{time_total}" "${BASE_URL}${endpoint}")
    echo "${endpoint}: ${time}s"
done
echo ""

echo "=== Testing Complete ==="

