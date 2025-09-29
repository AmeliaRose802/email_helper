#!/bin/bash
# Health check script for Email Helper application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
ENVIRONMENT=${1:-dev}
BACKEND_URL=${2:-http://localhost:8000}
FRONTEND_URL=${3:-http://localhost}

echo -e "${GREEN}=== Email Helper Health Check ===${NC}"
echo "Environment: $ENVIRONMENT"
echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo ""

# Function to check service health
check_service() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $name... "
    
    response=$(curl -s -w "\n%{http_code}" "$url" || echo "000")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}OK${NC} (HTTP $http_code)"
        return 0
    else
        echo -e "${RED}FAILED${NC} (HTTP $http_code)"
        echo "Response: $body"
        return 1
    fi
}

# Initialize status
all_healthy=true

# Backend health check
if ! check_service "Backend Health" "$BACKEND_URL/health" 200; then
    all_healthy=false
fi

# Backend API documentation
if ! check_service "Backend Docs" "$BACKEND_URL/docs" 200; then
    all_healthy=false
fi

# Frontend health check
if ! check_service "Frontend Health" "$FRONTEND_URL/health.html" 200; then
    all_healthy=false
fi

# Frontend main page
if ! check_service "Frontend Home" "$FRONTEND_URL/" 200; then
    all_healthy=false
fi

# Additional checks for development
if [ "$ENVIRONMENT" = "dev" ]; then
    echo ""
    echo "Docker container status:"
    docker-compose ps
    
    echo ""
    echo "Recent logs:"
    echo "--- Backend logs (last 10 lines) ---"
    docker-compose logs --tail=10 backend
    echo ""
    echo "--- Frontend logs (last 10 lines) ---"
    docker-compose logs --tail=10 frontend
fi

# Final status
echo ""
if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}✓ All health checks passed${NC}"
    exit 0
else
    echo -e "${RED}✗ Some health checks failed${NC}"
    exit 1
fi
