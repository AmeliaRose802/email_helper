# Deployment Scripts

This directory contains automation scripts for deploying and managing the Email Helper application.

## 📜 Available Scripts

### deploy.sh

Main deployment script that handles building and deploying to different environments.

**Usage:**
```bash
./deployment/scripts/deploy.sh [environment]
```

**Environments:**
- `dev` - Local development with Docker Compose
- `staging` - Azure staging environment
- `production` - Azure production environment

**Examples:**
```bash
# Deploy locally for development
./deployment/scripts/deploy.sh dev

# Deploy to staging
./deployment/scripts/deploy.sh staging

# Deploy to production
./deployment/scripts/deploy.sh production
```

**What it does:**
1. Validates prerequisites (Docker, Azure CLI, Terraform)
2. Builds Docker images
3. Tags images appropriately
4. Deploys to target environment
5. Runs health checks
6. Reports deployment status

### health-check.sh

Comprehensive health check script that verifies all services are running correctly.

**Usage:**
```bash
./deployment/scripts/health-check.sh [environment] [backend_url] [frontend_url]
```

**Examples:**
```bash
# Check local development environment
./deployment/scripts/health-check.sh dev

# Check staging environment
./deployment/scripts/health-check.sh staging https://backend-staging.azurewebsites.net https://frontend-staging.azurewebsites.net

# Check production
./deployment/scripts/health-check.sh production https://api.yourdomain.com https://yourdomain.com
```

**Checks performed:**
- Backend health endpoint (`/health`)
- Backend API documentation (`/docs`)
- Frontend health endpoint (`/health.html`)
- Frontend main page (`/`)
- Docker container status (dev only)
- Recent logs (dev only)

### backup.sh (Create this for production use)

Database backup script.

**Usage:**
```bash
./deployment/scripts/backup.sh [environment]
```

**Features:**
- Creates timestamped database backups
- Supports both SQLite and PostgreSQL
- Uploads to Azure Blob Storage (production)
- Retains last 7 backups locally

### restore.sh (Create this for production use)

Database restore script.

**Usage:**
```bash
./deployment/scripts/restore.sh [backup_file] [environment]
```

**Features:**
- Restores from local or remote backup
- Validates backup before restore
- Creates safety backup before restore

## 🔧 Configuration

### Environment Variables

Scripts use environment variables from:
1. `.env` file in project root
2. Environment-specific variables (from Azure, CI/CD)
3. Command-line arguments

### Required Variables

**For Azure deployment:**
```bash
AZURE_SUBSCRIPTION_ID=...
AZURE_TENANT_ID=...
AZURE_CLIENT_ID=...
AZURE_CLIENT_SECRET=...
```

**For application:**
```bash
SECRET_KEY=...
DATABASE_URL=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
```

## 📋 Pre-requisites

### For Local Development
- Docker and Docker Compose
- Bash shell
- curl (for health checks)

### For Cloud Deployment
- Azure CLI (`az`)
- Terraform
- Docker
- Git

## 🚀 Deployment Workflows

### Development Workflow

```bash
# 1. Make code changes
vim backend/main.py

# 2. Build and deploy locally
./deployment/scripts/deploy.sh dev

# 3. Run tests
docker-compose exec backend pytest

# 4. Check health
./deployment/scripts/health-check.sh dev
```

### Staging Deployment

```bash
# 1. Merge to main branch
git checkout main
git merge feature-branch

# 2. Push to trigger CI/CD
git push origin main

# Or deploy manually:
./deployment/scripts/deploy.sh staging

# 3. Verify deployment
./deployment/scripts/health-check.sh staging \
  https://email-helper-staging.azurewebsites.net
```

### Production Deployment

```bash
# 1. Create release tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# CI/CD automatically deploys to production

# Or deploy manually (not recommended):
./deployment/scripts/deploy.sh production
```

## 🔍 Troubleshooting

### Script Fails with "Permission Denied"

```bash
# Make scripts executable
chmod +x deployment/scripts/*.sh
```

### Azure Login Issues

```bash
# Clear Azure CLI cache
az account clear
az login

# Verify subscription
az account show
```

### Docker Build Fails

```bash
# Check Docker daemon
docker ps

# Clean up Docker
docker system prune -a

# Rebuild images
docker-compose build --no-cache
```

### Health Checks Fail

```bash
# View logs
docker-compose logs backend frontend

# Check service status
docker-compose ps

# Test endpoints manually
curl -v http://localhost:8000/health
```

## 📝 Creating Custom Scripts

### Template for New Scripts

```bash
#!/bin/bash
# Script description

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Main logic
main() {
    print_info "Starting script..."
    # Your code here
}

# Run main function
main "$@"
```

## 🔒 Security Notes

- **Never commit secrets** to version control
- **Use Azure Key Vault** for production secrets
- **Rotate credentials** regularly
- **Audit script access** and usage
- **Use service principals** for CI/CD, not personal accounts

## 📚 Additional Resources

- [Deployment Guide](../PRODUCTION_DEPLOYMENT.md)
- [Monitoring Setup](../MONITORING.md)
- [Docker Documentation](https://docs.docker.com/)
- [Azure CLI Documentation](https://docs.microsoft.com/en-us/cli/azure/)
- [Terraform Documentation](https://www.terraform.io/docs/)

## 🆘 Getting Help

If scripts are not working:

1. Check the script's inline comments
2. Review the troubleshooting section above
3. Check application logs
4. Verify prerequisites are installed
5. Open a GitHub issue with:
   - Script name and command used
   - Error messages
   - Environment details
   - Steps to reproduce

---

**Maintained by**: DevOps Team  
**Last Updated**: 2024
