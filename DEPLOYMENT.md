# Email Helper - Complete Deployment Package

Welcome to the Email Helper deployment documentation! This package contains everything you need to deploy and maintain the Email Helper application in production.

## 📦 What's Included

This deployment package provides:

- **Docker Configuration** - Multi-stage Dockerfiles for optimized production builds
- **Docker Compose** - Local development and testing environment
- **CI/CD Pipelines** - GitHub Actions workflows for automated testing and deployment
- **Infrastructure as Code** - Terraform configurations for Azure deployment
- **Deployment Scripts** - Automated deployment and health check scripts
- **Monitoring Setup** - Application Insights configuration and alerting
- **Production Guides** - Comprehensive deployment and operational documentation

## 🚀 Quick Start Guides

### For Developers (Local Development)

```bash
# 1. Clone repository
git clone https://github.com/AmeliaRose802/email_helper.git
cd email_helper

# 2. Set up environment
cp .env.docker .env
# Edit .env with your configuration

# 3. Start services
docker-compose up -d

# 4. Access the application
# Backend:  http://localhost:8000
# Frontend: http://localhost
# API Docs: http://localhost:8000/docs
```

**See**: [Local Development Guide](#local-development)

### For DevOps (Production Deployment)

```bash
# 1. Configure Azure credentials
az login

# 2. Deploy infrastructure
cd deployment/terraform
terraform init
terraform apply

# 3. Deploy application
./deployment/scripts/deploy.sh production
```

**See**: [deployment/PRODUCTION_DEPLOYMENT.md](./deployment/PRODUCTION_DEPLOYMENT.md)

## 📂 Repository Structure

```
email_helper/
├── backend/                      # FastAPI backend application
│   ├── Dockerfile               # Multi-stage Docker build
│   ├── requirements.txt         # Python dependencies
│   ├── .dockerignore           # Docker build exclusions
│   ├── api/                    # REST API endpoints
│   ├── core/                   # Configuration and settings
│   ├── database/               # Database management
│   ├── models/                 # Data models
│   ├── services/               # Business logic services
│   └── workers/                # Background job workers
│
├── frontend/                     # React web application
│   ├── Dockerfile               # Multi-stage Docker build
│   ├── nginx.conf              # Nginx web server config
│   ├── .dockerignore           # Docker build exclusions
│   ├── src/                    # React source code
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/              # Page components
│   │   ├── services/           # API integration
│   │   ├── store/              # Redux state management
│   │   └── types/              # TypeScript definitions
│   └── package.json            # Node dependencies
│
├── deployment/                   # Deployment configurations
│   ├── README.md               # Deployment overview (this file)
│   ├── PRODUCTION_DEPLOYMENT.md # Production deployment checklist
│   ├── MONITORING.md           # Monitoring and alerting guide
│   ├── terraform/              # Infrastructure as Code
│   │   ├── main.tf            # Main Terraform configuration
│   │   └── terraform.tfvars.example  # Configuration template
│   └── scripts/                # Deployment automation
│       ├── deploy.sh          # Main deployment script
│       └── health-check.sh    # Health verification script
│
├── .github/workflows/            # CI/CD pipelines
│   ├── ci.yml                  # Continuous Integration
│   └── cd.yml                  # Continuous Deployment
│
├── docker-compose.yml           # Local development environment
├── .env.docker                 # Environment template
└── .gitignore                  # Version control exclusions
```

## 🏗️ Architecture Overview

### Application Stack

```
┌─────────────────────────────────────────────────────────┐
│                       User Browser                       │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Frontend (React + Nginx)                    │
│  - Single Page Application                              │
│  - TypeScript + Redux                                   │
│  - Responsive UI                                        │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTPS
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Backend (FastAPI + Python)                  │
│  - REST API Endpoints                                   │
│  - JWT Authentication                                   │
│  - Email Processing                                     │
│  - AI Integration                                       │
└─────┬───────────────┬───────────────┬───────────────────┘
      │               │               │
      ▼               ▼               ▼
┌──────────┐   ┌─────────────┐   ┌────────────────┐
│ Database │   │    Redis    │   │ Azure Services │
│ (SQLite/ │   │  - Cache    │   │ - OpenAI       │
│  Postgres)│   │  - Jobs     │   │ - Graph API   │
└──────────┘   └─────────────┘   └────────────────┘
                      │
                      ▼
              ┌──────────────┐
              │Celery Worker │
              │ - Background │
              │   Processing │
              └──────────────┘
```

### Deployment Environments

| Environment | Purpose | URL Pattern | Auto-Deploy |
|-------------|---------|-------------|-------------|
| **Development** | Local testing | localhost | Manual |
| **Staging** | Pre-production testing | *-staging.azurewebsites.net | On push to `main` |
| **Production** | Live application | *.azurewebsites.net | On release tag |

## 🐳 Docker Configuration

### Backend Dockerfile

**Features:**
- Multi-stage build for optimization
- Python 3.11 slim base image
- Minimal runtime dependencies
- Health check integration
- Non-root user execution

**Build:**
```bash
docker build -t email-helper-backend:latest -f backend/Dockerfile .
```

### Frontend Dockerfile

**Features:**
- Node.js 20 for build stage
- Nginx Alpine for production
- Static asset optimization
- Gzip compression
- Security headers configured

**Build:**
```bash
docker build -t email-helper-frontend:latest -f frontend/Dockerfile frontend/
```

### Docker Compose

**Services:**
- `backend` - FastAPI application
- `frontend` - React web app
- `database` - PostgreSQL (optional, SQLite by default)
- `redis` - Caching and job queue
- `worker` - Celery background processor

**Usage:**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

## 🔄 CI/CD Pipeline

### Continuous Integration (`.github/workflows/ci.yml`)

**Triggers:**
- Push to any branch
- Pull requests to `main` or `develop`

**Jobs:**
1. **Backend Tests** - Python unit tests, coverage reporting
2. **Frontend Tests** - React component tests, TypeScript checks
3. **Security Scan** - Trivy vulnerability scanning
4. **Docker Build** - Validate Docker images build successfully

**Required for Merge:** All CI checks must pass

### Continuous Deployment (`.github/workflows/cd.yml`)

**Triggers:**
- Push to `main` → Deploy to staging
- Git tags `v*` → Deploy to production
- Manual workflow dispatch

**Jobs:**
1. **Build & Push** - Build Docker images, push to GitHub Container Registry
2. **Deploy Development** - Deploy to dev environment
3. **Deploy Staging** - Deploy to staging environment
4. **Deploy Production** - Deploy to production (tags only)
5. **Health Check** - Verify deployment success

## ☁️ Azure Infrastructure

### Terraform Configuration

The `deployment/terraform/` directory contains Infrastructure as Code for:

- **Resource Group** - Logical container for all resources
- **App Service Plan** - Hosting for web applications
- **App Service** - Backend and frontend hosting
- **Application Insights** - Monitoring and telemetry
- **Redis Cache** - Session storage and job queue
- **Key Vault** - Secrets management
- **PostgreSQL** - Production database (optional)

**Deployment:**
```bash
cd deployment/terraform
terraform init
terraform workspace select production
terraform apply
```

### Required Azure Secrets

Store in Azure Key Vault:
- `secret-key` - JWT secret key
- `azure-openai-key` - Azure OpenAI API key
- `graph-client-secret` - Microsoft Graph API secret
- `redis-connection-string` - Redis connection string

## 📊 Monitoring and Alerting

### Built-in Monitoring

- **Application Insights** - Request tracking, performance, errors
- **Health Checks** - Automated endpoint monitoring
- **Log Aggregation** - Centralized logging with structured JSON
- **Metrics Dashboard** - CPU, memory, request rates

### Alert Configuration

**Critical Alerts:**
- Application down (2+ minutes)
- High error rate (>5% for 5 minutes)
- Database connection failures

**Warning Alerts:**
- High response time (>1s p95)
- High CPU/memory usage (>80%)
- Job queue backlog

**See**: [deployment/MONITORING.md](./deployment/MONITORING.md)

## 🔐 Security Best Practices

### Secrets Management

✅ **DO:**
- Store secrets in Azure Key Vault
- Use managed identities for Azure services
- Rotate credentials regularly
- Use strong, random secret keys

❌ **DON'T:**
- Commit secrets to version control
- Share credentials via email/chat
- Use default or weak passwords
- Hard-code API keys

### Network Security

- HTTPS enforced (HTTP redirects)
- CORS configured per environment
- Firewall rules on database
- Private networking for Azure services

### Application Security

- JWT token-based authentication
- Password hashing with bcrypt
- Input validation on all endpoints
- SQL injection protection (ORM)
- XSS protection headers

## 🔧 Configuration Management

### Environment Variables

**Backend** (`.env`):
```bash
# Required
SECRET_KEY=...
DATABASE_URL=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...

# Optional
DEBUG=false
CORS_ORIGINS=["https://yourdomain.com"]
```

**Frontend** (`.env.local`):
```bash
VITE_API_BASE_URL=https://api.yourdomain.com
```

### Per-Environment Configuration

- **Development**: Debug mode enabled, verbose logging
- **Staging**: Production-like, but with test data
- **Production**: Optimized, minimal logging, strict CORS

## 📈 Scaling Strategy

### Horizontal Scaling

```bash
# Manual scaling
az webapp scale --name email-helper-backend \
  --resource-group email-helper-prod-rg \
  --instance-count 3

# Auto-scaling (configured in Terraform)
# Triggers:
# - CPU > 70% → Scale up
# - CPU < 30% → Scale down
# - Max instances: 10
```

### Database Scaling

- **Read Replicas**: For read-heavy workloads
- **Connection Pooling**: Configured in application
- **Query Optimization**: Indexes on frequently accessed columns

## 🔄 Backup and Recovery

### Automated Backups

- **Database**: Daily backups, 7-day retention
- **Configuration**: Version controlled in Git
- **Secrets**: Key Vault soft-delete enabled

### Disaster Recovery

1. **Infrastructure**: Recreate from Terraform
2. **Database**: Restore from latest backup
3. **Application**: Redeploy from Docker images
4. **RTO**: 1 hour | **RPO**: 24 hours

## 🐛 Troubleshooting

### Common Issues

**Backend won't start:**
```bash
# Check logs
docker-compose logs backend

# Verify environment variables
docker-compose exec backend env | grep SECRET_KEY

# Test database connection
docker-compose exec backend python -c "from backend.database.connection import db_manager; print('OK')"
```

**Frontend can't reach backend:**
```bash
# Check nginx config
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf

# Test from frontend container
docker-compose exec frontend curl http://backend:8000/health
```

**Database connection errors:**
```bash
# Check database is running
docker-compose ps database

# Verify connection string
echo $DATABASE_URL
```

### Debug Mode

Enable debug logging:
```bash
# Edit .env
DEBUG=true

# Restart services
docker-compose restart backend
```

## 📚 Additional Documentation

- [Production Deployment Checklist](./deployment/PRODUCTION_DEPLOYMENT.md)
- [Monitoring and Alerting Guide](./deployment/MONITORING.md)
- [Backend API Documentation](../backend/README.md)
- [Frontend Documentation](../frontend/README.md)

## 🆘 Support and Resources

### Documentation Links

- [Docker Documentation](https://docs.docker.com/)
- [Azure App Service](https://docs.microsoft.com/en-us/azure/app-service/)
- [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [GitHub Actions](https://docs.github.com/en/actions)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)

### Getting Help

1. Check this documentation
2. Review [troubleshooting section](#troubleshooting)
3. Check application logs
4. Open GitHub issue
5. Contact DevOps team

## 📝 License

This deployment configuration is part of the Email Helper project.

---

**Last Updated**: 2024
**Maintained By**: Email Helper Team
**Version**: 1.0.0
