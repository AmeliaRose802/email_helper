#!/bin/bash
# Email Helper Deployment Script
# Automated deployment to production/staging environments

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-staging}"
IMAGE_TAG="${2:-latest}"

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    print_info "Checking deployment requirements..."
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if kubectl is installed (for k8s deployments)
    if ! command -v kubectl &> /dev/null; then
        print_warning "kubectl is not installed. Kubernetes deployments will not be available."
    fi
    
    print_info "Requirements check passed."
}

build_docker_image() {
    print_info "Building Docker image..."
    
    cd "$PROJECT_ROOT"
    
    docker build -t email-helper:$IMAGE_TAG \
        --target production \
        --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
        --build-arg VCS_REF=$(git rev-parse --short HEAD) \
        .
    
    print_info "Docker image built successfully: email-helper:$IMAGE_TAG"
}

deploy_docker_compose() {
    print_info "Deploying with Docker Compose..."
    
    cd "$PROJECT_ROOT"
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from .env.example..."
        cp .env.example .env
        print_warning "Please update .env file with your configuration before running."
        exit 1
    fi
    
    # Pull latest images
    docker-compose pull || true
    
    # Start services
    docker-compose up -d
    
    print_info "Services started. Waiting for health checks..."
    sleep 10
    
    # Check health
    if docker-compose ps | grep -q "Up (healthy)"; then
        print_info "Deployment successful!"
    else
        print_warning "Some services may not be healthy. Check with: docker-compose ps"
    fi
    
    print_info "Access the API at: http://localhost:8000"
    print_info "Access the API docs at: http://localhost:8000/docs"
}

deploy_kubernetes() {
    print_info "Deploying to Kubernetes ($ENVIRONMENT)..."
    
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed. Cannot deploy to Kubernetes."
        exit 1
    fi
    
    cd "$PROJECT_ROOT"
    
    # Update image tag in manifests
    sed -i.bak "s|IMAGE_TAG|$IMAGE_TAG|g" "k8s/$ENVIRONMENT/deployment.yaml"
    
    # Apply manifests
    kubectl apply -f "k8s/$ENVIRONMENT/deployment.yaml"
    
    # Restore original file
    mv "k8s/$ENVIRONMENT/deployment.yaml.bak" "k8s/$ENVIRONMENT/deployment.yaml"
    
    # Wait for rollout
    print_info "Waiting for deployment rollout..."
    kubectl rollout status deployment/email-helper-api -n email-helper-$ENVIRONMENT --timeout=5m
    
    print_info "Kubernetes deployment successful!"
}

run_smoke_tests() {
    print_info "Running smoke tests..."
    
    # Basic health check
    API_URL="${API_URL:-http://localhost:8000}"
    
    if curl -f -s "$API_URL/health" > /dev/null; then
        print_info "Health check passed!"
    else
        print_error "Health check failed!"
        exit 1
    fi
    
    # Test API documentation
    if curl -f -s "$API_URL/docs" > /dev/null; then
        print_info "API documentation accessible!"
    else
        print_warning "API documentation may not be accessible"
    fi
    
    print_info "Smoke tests completed successfully!"
}

rollback() {
    print_warning "Rolling back deployment..."
    
    if [ "$DEPLOYMENT_TYPE" == "kubernetes" ]; then
        kubectl rollout undo deployment/email-helper-api -n email-helper-$ENVIRONMENT
        print_info "Rollback initiated for Kubernetes deployment"
    elif [ "$DEPLOYMENT_TYPE" == "docker-compose" ]; then
        docker-compose down
        print_info "Docker Compose services stopped"
    fi
}

# Main deployment flow
main() {
    print_info "Starting Email Helper deployment..."
    print_info "Environment: $ENVIRONMENT"
    print_info "Image Tag: $IMAGE_TAG"
    
    check_requirements
    
    # Determine deployment type
    DEPLOYMENT_TYPE="${DEPLOYMENT_TYPE:-docker-compose}"
    
    if [ "$DEPLOYMENT_TYPE" == "kubernetes" ]; then
        deploy_kubernetes
    else
        build_docker_image
        deploy_docker_compose
    fi
    
    # Run smoke tests
    sleep 5
    run_smoke_tests
    
    print_info "Deployment completed successfully! 🚀"
}

# Handle errors
trap 'print_error "Deployment failed! Use rollback if needed."; exit 1' ERR

# Run main function
main

# Usage information
usage() {
    echo "Usage: $0 [environment] [image-tag]"
    echo ""
    echo "Arguments:"
    echo "  environment   Deployment environment (staging/production, default: staging)"
    echo "  image-tag     Docker image tag (default: latest)"
    echo ""
    echo "Environment Variables:"
    echo "  DEPLOYMENT_TYPE   Type of deployment (docker-compose/kubernetes, default: docker-compose)"
    echo "  API_URL          API URL for smoke tests (default: http://localhost:8000)"
    echo ""
    echo "Examples:"
    echo "  $0 staging v1.0.0"
    echo "  DEPLOYMENT_TYPE=kubernetes $0 production v1.0.0"
}

# Show usage if --help is passed
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    usage
    exit 0
fi
