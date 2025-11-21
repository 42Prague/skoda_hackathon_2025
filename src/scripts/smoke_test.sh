#!/bin/bash
# ŠKODA AI Skill Coach - Complete Smoke Test Script
# Tests entire system with Docker, fake data, and fallback AI mode

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:5173"
TEST_TIMEOUT=30
MAX_RETRIES=10

# Test results
PASSED=0
FAILED=0
SKIPPED=0

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((SKIPPED++))
}

wait_for_service() {
    local url=$1
    local service_name=$2
    local retries=0
    
    log_info "Waiting for $service_name to be ready..."
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            log_success "$service_name is ready"
            return 0
        fi
        ((retries++))
        sleep 2
    done
    
    log_error "$service_name failed to start after $((MAX_RETRIES * 2)) seconds"
    return 1
}

test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_status=${4:-200}
    
    local url="${BACKEND_URL}${endpoint}"
    local response
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url" || echo -e "\n000")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
            -H "Content-Type: application/json" \
            -d "$data" || echo -e "\n000")
    else
        log_error "Unsupported method: $method"
        return 1
    fi
    
    local body=$(echo "$response" | head -n -1)
    local status_code=$(echo "$response" | tail -n 1)
    
    if [ "$status_code" = "$expected_status" ]; then
        log_success "$method $endpoint -> $status_code"
        echo "$body" | jq . > /dev/null 2>&1 && log_success "  Valid JSON response" || log_warning "  Non-JSON response"
        return 0
    else
        log_error "$method $endpoint -> $status_code (expected $expected_status)"
        echo "Response: $body" | head -c 200
        return 1
    fi
}

# ============================================================================
# SECTION 1: Start Docker System
# ============================================================================
echo "============================================================================"
echo "SECTION 1: Starting Docker System"
echo "============================================================================"

log_info "Copying .env.smoke-test to .env..."
cp -f .env.smoke-test .env 2>/dev/null || log_warning ".env.smoke-test not found, using defaults"

log_info "Building and starting Docker containers..."
docker compose down -v 2>/dev/null || true
docker compose build --no-cache
docker compose up -d

log_info "Waiting for services to start..."
sleep 10

# Wait for database
wait_for_service "$BACKEND_URL/healthz" "Backend" || exit 1

log_success "Docker system started successfully"

# ============================================================================
# SECTION 2: Verify AI Fallback Mode
# ============================================================================
echo ""
echo "============================================================================"
echo "SECTION 2: Verifying AI Fallback Mode"
echo "============================================================================"

log_info "Checking AI_FORCE_FALLBACK configuration..."
backend_env=$(docker exec skoda-skill-coach-backend env | grep AI_FORCE_FALLBACK || echo "")
if echo "$backend_env" | grep -q "AI_FORCE_FALLBACK=true"; then
    log_success "AI_FORCE_FALLBACK is enabled"
else
    log_error "AI_FORCE_FALLBACK is not enabled"
fi

# ============================================================================
# SECTION 3: Generate and Ingest Fake Dataset
# ============================================================================
echo ""
echo "============================================================================"
echo "SECTION 3: Generating and Ingesting Fake Dataset"
echo "============================================================================"

log_info "Generating fake dataset..."
python3 scripts/generate_fake_dataset.py 80 fake_skoda_dataset.csv || {
    log_error "Failed to generate fake dataset"
    exit 1
}

log_info "Ingesting dataset..."
INGEST_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/api/ingestion/ingest" \
    -F "file=@fake_skoda_dataset.csv" || echo '{"success":false}')

DATASET_ID=$(echo "$INGEST_RESPONSE" | jq -r '.data.dataset_id // empty')

if [ -z "$DATASET_ID" ] || [ "$DATASET_ID" = "null" ]; then
    log_error "Dataset ingestion failed"
    echo "Response: $INGEST_RESPONSE"
    exit 1
fi

log_success "Dataset ingested: $DATASET_ID"

log_info "Loading employees from dataset..."
LOAD_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/api/ingestion/load-employees/${DATASET_ID}" \
    -H "Content-Type: application/json" \
    -d '{"employee_id_column": "employee_id", "department_column": "department"}' || echo '{"success":false}')

if echo "$LOAD_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
    EMPLOYEES_LOADED=$(echo "$LOAD_RESPONSE" | jq -r '.data.total_loaded // 0')
    log_success "Loaded $EMPLOYEES_LOADED employees"
else
    log_error "Failed to load employees"
    echo "Response: $LOAD_RESPONSE"
fi

# ============================================================================
# SECTION 4: Smoke Test Backend Endpoints
# ============================================================================
echo ""
echo "============================================================================"
echo "SECTION 4: Smoke Testing Backend Endpoints"
echo "============================================================================"

# Analytics Endpoints
test_endpoint "GET" "/api/dashboard/overview"
test_endpoint "GET" "/api/dashboard/heatmap"
test_endpoint "GET" "/api/analytics/global"
test_endpoint "GET" "/api/analytics/succession/Engineering"
test_endpoint "GET" "/api/analytics/employees/EMP-001"
test_endpoint "GET" "/api/analytics/forecast?months=6"

# AI Endpoints (should use fallback)
test_endpoint "GET" "/api/ai/employee-intel/EMP-001"
test_endpoint "POST" "/api/ai/career-chat" '{"employee_id": "EMP-001", "user_message": "Hello"}'
test_endpoint "POST" "/api/ai/training-plan" '{"employee_id": "EMP-001", "desired_role": "Senior Engineer"}'

# Skills Endpoints
test_endpoint "GET" "/api/skills/analysis/EMP-001"
test_endpoint "GET" "/api/skills/recommendations/skills/EMP-001"

# ============================================================================
# SECTION 5: Test Frontend (if available)
# ============================================================================
echo ""
echo "============================================================================"
echo "SECTION 5: Testing Frontend"
echo "============================================================================"

if curl -s -f "$FRONTEND_URL" > /dev/null 2>&1; then
    log_success "Frontend is accessible at $FRONTEND_URL"
else
    log_warning "Frontend is not accessible (may still be building)"
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "============================================================================"
echo "SMOKE TEST SUMMARY"
echo "============================================================================"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "Skipped: $SKIPPED"
echo ""

if [ $FAILED -eq 0 ]; then
    log_success "All smoke tests passed!"
    exit 0
else
    log_error "Some smoke tests failed"
    exit 1
fi

