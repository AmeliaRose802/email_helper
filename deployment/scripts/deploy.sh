#!/bin/bash
# Deployment script for Email Helper application

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${GREEN}=== Email Helper Deployment ===${NC}"
echo "Environment: $ENVIRONMENT"
echo "Project Root: $PROJECT_ROOT"
echo ""

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
print_info "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed"
    exit 1
fi

if ! command -v az &> /dev/null; then
    print_warning "Azure CLI is not installed (required for cloud deployment)"
fi

print_info "Prerequisites check complete"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    print_info "Loading environment variables from .env"
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
else
    print_warning "No .env file found. Using defaults."
fi

# Build Docker images
print_info "Building Docker images..."

cd "$PROJECT_ROOT"

# Backend image
print_info "Building backend image..."
docker build -t email-helper-backend:$ENVIRONMENT -f backend/Dockerfile .

# Frontend image
print_info "Building frontend image..."
docker build -t email-helper-frontend:$ENVIRONMENT -f frontend/Dockerfile frontend/

print_info "Docker images built successfully"

# Deploy based on environment
case $ENVIRONMENT in
    dev|development)
        print_info "Deploying to development environment (Docker Compose)..."
        docker-compose down
        docker-compose up -d
        
        # Wait for services to be healthy
        print_info "Waiting for services to be healthy..."
        sleep 10
        
        # Health checks
        print_info "Running health checks..."
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            print_info "Backend is healthy"
        else
            print_error "Backend health check failed"
            docker-compose logs backend
            exit 1
        fi
        
        if curl -f http://localhost/health.html > /dev/null 2>&1; then
            print_info "Frontend is healthy"
        else
            print_error "Frontend health check failed"
            docker-compose logs frontend
            exit 1
        fi
        
        print_info "Development deployment complete!"
        echo ""
        echo "Services are running at:"
        echo "  Backend:  http://localhost:8000"
        echo "  Frontend: http://localhost"
        echo "  API Docs: http://localhost:8000/docs"
        ;;
        
    staging|production)
        print_info "Deploying to $ENVIRONMENT environment (Azure)..."
        
        # Check Azure CLI login
        if ! az account show &> /dev/null; then
            print_error "Not logged into Azure. Run 'az login' first."
            exit 1
        fi
        
        # Tag images for container registry
        REGISTRY="emailhelper${ENVIRONMENT}.azurecr.io"
        
        print_info "Tagging images for $REGISTRY..."
        docker tag email-helper-backend:$ENVIRONMENT $REGISTRY/backend:latest
        docker tag email-helper-frontend:$ENVIRONMENT $REGISTRY/frontend:latest
        
        # Login to Azure Container Registry
        print_info "Logging into Azure Container Registry..."
        az acr login --name emailhelper${ENVIRONMENT}
        
        # Push images
        print_info "Pushing images to registry..."
        docker push $REGISTRY/backend:latest
        docker push $REGISTRY/frontend:latest
        
        # Deploy using Terraform
        print_info "Deploying infrastructure with Terraform..."
        cd "$PROJECT_ROOT/deployment/terraform"
        
        terraform init
        terraform workspace select $ENVIRONMENT || terraform workspace new $ENVIRONMENT
        terraform apply -var="environment=$ENVIRONMENT" -auto-approve
        
        # Get outputs
        BACKEND_URL=$(terraform output -raw backend_url)
        FRONTEND_URL=$(terraform output -raw frontend_url)
        
        print_info "$ENVIRONMENT deployment complete!"
        echo ""
        echo "Services are running at:"
        echo "  Backend:  $BACKEND_URL"
        echo "  Frontend: $FRONTEND_URL"
        echo "  API Docs: $BACKEND_URL/docs"
        ;;
        
    *)
        print_error "Unknown environment: $ENVIRONMENT"
        echo "Usage: $0 [dev|staging|production]"
        exit 1
        ;;
esac

echo ""
print_info "Deployment completed successfully!"
