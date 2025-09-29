#!/bin/bash
# Smoke Tests for Email Helper Deployment
# Validates critical functionality after deployment

set -e

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
ENVIRONMENT="${1:-staging}"
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
TIMEOUT=5

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

print_test() {
    echo -e "\n${YELLOW}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
}

print_fail() {
    echo -e "${RED}✗${NC} $1"
    ((TESTS_FAILED++))
}

# Test: Health endpoint
test_health() {
    print_test "Testing health endpoint..."
    
    response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$API_BASE_URL/health")
    body=$(echo "$response" | head -n -1)
    status=$(echo "$response" | tail -n 1)
    
    if [ "$status" == "200" ]; then
        # Check if response contains expected fields
        if echo "$body" | grep -q "status.*healthy"; then
            print_pass "Health endpoint responding correctly"
            return 0
        else
            print_fail "Health endpoint response missing expected fields"
            return 1
        fi
    else
        print_fail "Health endpoint returned status $status"
        return 1
    fi
}

# Test: API root endpoint
test_root() {
    print_test "Testing root endpoint..."
    
    response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$API_BASE_URL/")
    status=$(echo "$response" | tail -n 1)
    
    if [ "$status" == "200" ]; then
        print_pass "Root endpoint accessible"
        return 0
    else
        print_fail "Root endpoint returned status $status"
        return 1
    fi
}

# Test: API documentation
test_docs() {
    print_test "Testing API documentation..."
    
    status=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$API_BASE_URL/docs")
    
    if [ "$status" == "200" ]; then
        print_pass "API documentation accessible"
        return 0
    else
        print_fail "API documentation returned status $status"
        return 1
    fi
}

# Test: Database connectivity (via health check)
test_database() {
    print_test "Testing database connectivity..."
    
    response=$(curl -s --max-time $TIMEOUT "$API_BASE_URL/health")
    
    if echo "$response" | grep -q "database.*healthy"; then
        print_pass "Database connection healthy"
        return 0
    else
        print_fail "Database connection unhealthy"
        return 1
    fi
}

# Test: CORS headers
test_cors() {
    print_test "Testing CORS headers..."
    
    headers=$(curl -s -I -X OPTIONS --max-time $TIMEOUT "$API_BASE_URL/health")
    
    if echo "$headers" | grep -qi "access-control-allow"; then
        print_pass "CORS headers present"
        return 0
    else
        print_fail "CORS headers missing"
        return 1
    fi
}

# Test: Response time
test_response_time() {
    print_test "Testing response time..."
    
    time_total=$(curl -s -o /dev/null -w "%{time_total}" --max-time $TIMEOUT "$API_BASE_URL/health")
    
    # Convert to milliseconds for comparison
    time_ms=$(echo "$time_total * 1000" | bc)
    
    if (( $(echo "$time_ms < 1000" | bc -l) )); then
        print_pass "Response time acceptable: ${time_ms}ms"
        return 0
    else
        print_fail "Response time too high: ${time_ms}ms"
        return 1
    fi
}

# Test: SSL/TLS (if HTTPS)
test_ssl() {
    if [[ "$API_BASE_URL" == https://* ]]; then
        print_test "Testing SSL/TLS..."
        
        if curl -s --max-time $TIMEOUT "$API_BASE_URL/health" > /dev/null; then
            print_pass "SSL/TLS connection successful"
            return 0
        else
            print_fail "SSL/TLS connection failed"
            return 1
        fi
    else
        print_test "Skipping SSL/TLS test (HTTP endpoint)"
        return 0
    fi
}

# Test: API versioning
test_version() {
    print_test "Testing API version..."
    
    response=$(curl -s --max-time $TIMEOUT "$API_BASE_URL/")
    
    if echo "$response" | grep -q "version"; then
        version=$(echo "$response" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
        print_pass "API version: $version"
        return 0
    else
        print_fail "API version not found"
        return 1
    fi
}

# Run all tests
run_all_tests() {
    echo "======================================"
    echo "Email Helper Smoke Tests"
    echo "Environment: $ENVIRONMENT"
    echo "API URL: $API_BASE_URL"
    echo "======================================"
    
    test_health || true
    test_root || true
    test_docs || true
    test_database || true
    test_cors || true
    test_response_time || true
    test_ssl || true
    test_version || true
    
    echo ""
    echo "======================================"
    echo "Test Results:"
    echo "  Passed: $TESTS_PASSED"
    echo "  Failed: $TESTS_FAILED"
    echo "======================================"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}All tests passed! ✓${NC}"
        exit 0
    else
        echo -e "${RED}Some tests failed! ✗${NC}"
        exit 1
    fi
}

# Main execution
main() {
    run_all_tests
}

# Usage
usage() {
    echo "Usage: $0 [environment]"
    echo ""
    echo "Arguments:"
    echo "  environment   Target environment (staging/production, default: staging)"
    echo ""
    echo "Environment Variables:"
    echo "  API_BASE_URL  Base URL of the API (default: http://localhost:8000)"
    echo ""
    echo "Examples:"
    echo "  $0 staging"
    echo "  API_BASE_URL=https://api.emailhelper.com $0 production"
}

if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    usage
    exit 0
fi

main
