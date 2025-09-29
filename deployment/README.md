# Email Helper Deployment Guide

This directory contains deployment configurations for the Email Helper application.

## 📁 Contents

- **terraform/** - Infrastructure as Code (Terraform) for Azure deployment
- **scripts/** - Deployment and management scripts
- **docs/** - Detailed deployment documentation

## 🚀 Quick Start

### Local Development with Docker

```bash
# 1. Copy environment file
cp .env.docker .env

# 2. Configure your environment variables in .env
# Edit .env with your Azure OpenAI keys and other settings

# 3. Start all services
docker-compose up -d

# 4. Check service health
docker-compose ps
curl http://localhost:8000/health  # Backend
curl http://localhost/health.html   # Frontend

# 5. View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# 6. Stop services
docker-compose down
```

### Production Deployment to Azure

```bash
# 1. Install Terraform
# Download from: https://www.terraform.io/downloads

# 2. Login to Azure
az login

# 3. Configure Terraform variables
cd deployment/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# 4. Initialize Terraform
terraform init

# 5. Plan deployment
terraform plan

# 6. Apply deployment
terraform apply

# 7. Get outputs
terraform output
```

## 🏗️ Architecture

### Components

1. **Backend (FastAPI)**
   - REST API endpoints
   - JWT authentication
   - Email processing with Microsoft Graph API
   - AI integration with Azure OpenAI
   - Background job processing with Celery

2. **Frontend (React)**
   - Single-page application
   - Modern UI with TypeScript
   - Redux state management
   - Served via Nginx

3. **Database**
   - SQLite for development
   - PostgreSQL for production (optional)

4. **Redis**
   - Job queue for Celery
   - Caching layer
   - Session storage

5. **Azure Services**
   - App Service for hosting
   - Application Insights for monitoring
   - Key Vault for secrets
   - Container Registry for images

### Networking

```
User → Frontend (Nginx) → Backend API → Azure Services
                              ↓
                           Database
                              ↓
                           Redis
                              ↓
                        Celery Worker
```

## 🔧 Environment Configuration

### Required Environment Variables

#### Backend
- `SECRET_KEY` - JWT secret key (generate with `openssl rand -hex 32`)
- `DATABASE_URL` - Database connection string
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint
- `AZURE_OPENAI_API_KEY` - Azure OpenAI API key
- `GRAPH_CLIENT_ID` - Microsoft Graph API client ID
- `GRAPH_CLIENT_SECRET` - Microsoft Graph API client secret
- `GRAPH_TENANT_ID` - Azure AD tenant ID
- `REDIS_URL` - Redis connection string

#### Frontend
- `VITE_API_BASE_URL` - Backend API URL

## 🐳 Docker Configuration

### Building Images

```bash
# Backend
docker build -t email-helper-backend:latest ./backend

# Frontend
docker build -t email-helper-frontend:latest ./frontend
```

### Pushing to Container Registry

```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Tag and push backend
docker tag email-helper-backend:latest ghcr.io/USERNAME/email-helper-backend:latest
docker push ghcr.io/USERNAME/email-helper-backend:latest

# Tag and push frontend
docker tag email-helper-frontend:latest ghcr.io/USERNAME/email-helper-frontend:latest
docker push ghcr.io/USERNAME/email-helper-frontend:latest
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflows

1. **CI Workflow** (`.github/workflows/ci.yml`)
   - Runs on push and PR
   - Backend tests (Python)
   - Frontend tests (React)
   - Security scanning (Trivy)
   - Docker build validation

2. **CD Workflow** (`.github/workflows/cd.yml`)
   - Builds and pushes Docker images
   - Deploys to Azure environments
   - Runs health checks

### Required GitHub Secrets

- `AZURE_CREDENTIALS_DEV` - Azure service principal for development
- `AZURE_CREDENTIALS_STAGING` - Azure service principal for staging
- `AZURE_CREDENTIALS_PROD` - Azure service principal for production
- `SECRET_KEY_DEV` - JWT secret for development
- `DATABASE_URL_DEV` - Database URL for development
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint
- `AZURE_OPENAI_API_KEY` - Azure OpenAI API key
- `GRAPH_CLIENT_SECRET_DEV` - Graph API secret for development

## 📊 Monitoring and Logging

### Health Checks

- Backend: `GET /health`
- Frontend: `GET /health.html`

### Application Insights

Azure Application Insights is automatically configured for:
- Request tracking
- Performance monitoring
- Error logging
- Custom events

### Accessing Logs

```bash
# Docker logs
docker-compose logs -f [service_name]

# Azure logs
az webapp log tail --name email-helper-backend --resource-group email-helper-prod-rg
```

## 🔐 Security Best Practices

1. **Secrets Management**
   - Use Azure Key Vault for production secrets
   - Never commit secrets to version control
   - Rotate credentials regularly

2. **Network Security**
   - Enable HTTPS only
   - Configure appropriate CORS origins
   - Use managed identities for Azure services

3. **Access Control**
   - Implement least privilege principle
   - Use Azure RBAC for resource access
   - Enable MFA for admin accounts

## 🔄 Database Migrations

### Development
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

### Production
Migrations are applied automatically during deployment via CD pipeline.

## 📈 Scaling

### Manual Scaling
```bash
# Scale App Service
az webapp scale --name email-helper-backend --resource-group email-helper-prod-rg --instance-count 3
```

### Auto-scaling
Auto-scaling is configured in Terraform for production environment based on:
- CPU usage > 70%
- Memory usage > 80%
- Request count thresholds

## 🔙 Backup and Recovery

### Database Backups
- Automated daily backups (7-day retention)
- Point-in-time restore available
- Geo-redundant backups for production

### Disaster Recovery
1. Infrastructure is code - can be recreated from Terraform
2. Database backups are stored in Azure Storage
3. Container images are versioned in GitHub Container Registry
4. Configuration is version controlled

## 🐛 Troubleshooting

### Common Issues

**Backend won't start**
```bash
# Check logs
docker-compose logs backend

# Verify database connection
docker-compose exec backend python -c "from backend.database.connection import db_manager; print(db_manager.db_path)"
```

**Frontend can't reach backend**
```bash
# Check nginx configuration
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf

# Test backend from frontend container
docker-compose exec frontend curl http://backend:8000/health
```

**Database connection errors**
- Verify DATABASE_URL is correct
- Check network connectivity
- Ensure database is running

## 📚 Additional Resources

- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [Docker Documentation](https://docs.docker.com/)
- [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review application logs
3. Check Azure service health
4. Open an issue on GitHub
