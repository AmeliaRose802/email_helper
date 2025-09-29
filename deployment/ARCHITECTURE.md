# Email Helper - Deployment Architecture

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         End Users                                │
│                    (Web Browser / API Clients)                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Azure Front Door                            │
│                   (Optional - CDN & WAF)                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
            ▼                             ▼
┌──────────────────────┐      ┌──────────────────────┐
│  Frontend Container  │      │  Backend Container   │
│  (Nginx + React)     │      │  (FastAPI + Python)  │
│                      │      │                      │
│  • React 19 + TS     │◄────►│  • REST API          │
│  • Redux Toolkit     │      │  • JWT Auth          │
│  • Static Assets     │      │  • Email Processing  │
│  • Health: /health   │      │  • AI Integration    │
│  Port: 80            │      │  Port: 8000          │
└──────────────────────┘      └──────────┬───────────┘
                                         │
                         ┌───────────────┼───────────────┐
                         │               │               │
                         ▼               ▼               ▼
              ┌──────────────┐ ┌─────────────┐ ┌──────────────┐
              │   Database   │ │    Redis    │ │Celery Worker │
              │  (SQLite/    │ │             │ │              │
              │  PostgreSQL) │ │ • Cache     │ │• Background  │
              │              │ │ • Sessions  │ │  Jobs        │
              │• User Data   │ │ • Job Queue │ │• Email Proc  │
              │• Emails      │ │             │ │• AI Tasks    │
              │• Tasks       │ │             │ │              │
              └──────────────┘ └─────────────┘ └──────────────┘
                         │               │               │
                         └───────────────┼───────────────┘
                                         │
                                         ▼
                           ┌──────────────────────┐
                           │   Azure Services     │
                           ├──────────────────────┤
                           │ • OpenAI (GPT-4)     │
                           │ • Graph API (Email)  │
                           │ • Key Vault          │
                           │ • App Insights       │
                           └──────────────────────┘
```

## 📦 Container Architecture

### Production Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure App Service Plan                    │
│                   (Linux Container Hosting)                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────┐         ┌────────────────────┐     │
│  │ Backend App        │         │ Frontend App       │     │
│  │ Service            │         │ Service            │     │
│  ├────────────────────┤         ├────────────────────┤     │
│  │ Docker Image:      │         │ Docker Image:      │     │
│  │ ghcr.io/user/      │         │ ghcr.io/user/      │     │
│  │ backend:latest     │         │ frontend:latest    │     │
│  │                    │         │                    │     │
│  │ Resources:         │         │ Resources:         │     │
│  │ • CPU: 2 cores     │         │ • CPU: 1 core      │     │
│  │ • RAM: 2GB         │         │ • RAM: 512MB       │     │
│  │ • Storage: 10GB    │         │ • Storage: 5GB     │     │
│  │                    │         │                    │     │
│  │ Health Check:      │         │ Health Check:      │     │
│  │ GET /health        │         │ GET /health.html   │     │
│  │                    │         │                    │     │
│  │ Auto-scale:        │         │ Auto-scale:        │     │
│  │ 1-10 instances     │         │ 1-5 instances      │     │
│  └────────────────────┘         └────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
          │                                   │
          └───────────┬───────────────────────┘
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│ Azure Redis      │    │ Azure PostgreSQL │
│ Cache            │    │ Flexible Server  │
├──────────────────┤    ├──────────────────┤
│ • Standard       │    │ • B1ms (Basic)   │
│ • 256MB          │    │ • 32GB Storage   │
│ • TLS 1.2+       │    │ • 7-day Backup   │
│ • Persistence    │    │ • Auto-failover  │
└──────────────────┘    └──────────────────┘
```

## 🔄 CI/CD Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Repository                         │
│                 (Source Code + Workflows)                    │
└────────────┬────────────────────────────────────────────────┘
             │
             │ Push / PR
             ▼
┌─────────────────────────────────────────────────────────────┐
│                   GitHub Actions - CI                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Backend      │  │ Frontend     │  │ Security     │     │
│  │ Tests        │  │ Tests        │  │ Scan         │     │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤     │
│  │• Pytest      │  │• Vitest      │  │• Trivy       │     │
│  │• Coverage    │  │• TypeCheck   │  │• Dependency  │     │
│  │• Linting     │  │• ESLint      │  │  Audit       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────┬────────────────────────────────────────────────┘
             │ All Tests Pass ✓
             ▼
┌─────────────────────────────────────────────────────────────┐
│                 GitHub Actions - CD                          │
├─────────────────────────────────────────────────────────────┤
│  Step 1: Build Docker Images                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ docker build backend:latest                          │   │
│  │ docker build frontend:latest                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Step 2: Push to Container Registry                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Push to ghcr.io/user/email-helper/backend:latest    │   │
│  │ Push to ghcr.io/user/email-helper/frontend:latest   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Step 3: Deploy to Environment                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • develop branch  → Development                      │   │
│  │ • main branch     → Staging                          │   │
│  │ • v* tags         → Production                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Step 4: Health Checks                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • Verify backend health                              │   │
│  │ • Verify frontend health                             │   │
│  │ • Check API endpoints                                │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────┬────────────────────────────────────────────────┘
             │ Deployment Complete ✓
             ▼
┌─────────────────────────────────────────────────────────────┐
│                  Azure App Service                           │
│              (Running Docker Containers)                     │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Monitoring & Observability

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│     (Backend API + Frontend Web App + Worker)                │
└────────────┬─────────────────────────────────────────────────┘
             │ Telemetry Data
             ▼
┌─────────────────────────────────────────────────────────────┐
│              Azure Application Insights                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Request      │  │ Performance  │  │ Custom       │     │
│  │ Tracking     │  │ Monitoring   │  │ Events       │     │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤     │
│  │• Latency     │  │• CPU Usage   │  │• Email       │     │
│  │• Status Code │  │• Memory      │  │  Processing  │     │
│  │• Volume      │  │• Disk I/O    │  │• AI Calls    │     │
│  │• Errors      │  │• Network     │  │• User Events │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Availability │  │ Alerts       │  │ Dashboards   │     │
│  │ Tests        │  │              │  │              │     │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤     │
│  │• Health      │  │• Critical    │  │• Overview    │     │
│  │  Checks      │  │• Warning     │  │• Performance │     │
│  │• Ping Tests  │  │• Email/SMS   │  │• Errors      │     │
│  │• Multi-      │  │• Slack       │  │• Business    │     │
│  │  Region      │  │• PagerDuty   │  │  Metrics     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
└────────────┬─────────────────────────────────────────────────┘
             │ Logs & Metrics
             ▼
┌─────────────────────────────────────────────────────────────┐
│                  Log Analytics Workspace                     │
│              (Structured JSON Logs - KQL Queries)            │
└─────────────────────────────────────────────────────────────┘
```

## 🔐 Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                           │
└─────────────────────────────────────────────────────────────┘

Layer 1: Network Security
┌─────────────────────────────────────────────────────────────┐
│ • HTTPS Only (TLS 1.2+)                                      │
│ • Azure Front Door (WAF)                                     │
│ • DDoS Protection                                            │
│ • CORS Configuration                                         │
└─────────────────────────────────────────────────────────────┘

Layer 2: Application Security
┌─────────────────────────────────────────────────────────────┐
│ • JWT Authentication                                         │
│ • Password Hashing (bcrypt)                                  │
│ • Input Validation (Pydantic)                                │
│ • SQL Injection Protection (ORM)                             │
│ • XSS Protection Headers                                     │
└─────────────────────────────────────────────────────────────┘

Layer 3: Data Security
┌─────────────────────────────────────────────────────────────┐
│ • Azure Key Vault (Secrets)                                  │
│ • Managed Identities (No Hardcoded Keys)                     │
│ • Encrypted Database (TLS)                                   │
│ • Encrypted Redis (TLS)                                      │
│ • Backup Encryption                                          │
└─────────────────────────────────────────────────────────────┘

Layer 4: Compliance & Monitoring
┌─────────────────────────────────────────────────────────────┐
│ • Security Scanning (Trivy)                                  │
│ • Dependency Audits                                          │
│ • Access Logging                                             │
│ • Audit Trails                                               │
│ • Threat Detection                                           │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Deployment Environments

```
┌────────────────────────────────────────────────────────────┐
│                    Development                              │
├────────────────────────────────────────────────────────────┤
│ Location:    localhost                                     │
│ Database:    SQLite                                        │
│ Redis:       Local Docker                                  │
│ Debug:       Enabled                                       │
│ Deploy:      docker-compose up                             │
│ URL:         http://localhost                              │
└────────────────────────────────────────────────────────────┘
                        │
                        │ git push develop
                        ▼
┌────────────────────────────────────────────────────────────┐
│                      Staging                                │
├────────────────────────────────────────────────────────────┤
│ Location:    Azure East US                                 │
│ Database:    Azure PostgreSQL                              │
│ Redis:       Azure Redis Cache                             │
│ Debug:       Enabled                                       │
│ Deploy:      Automatic (CI/CD)                             │
│ URL:         email-helper-staging.azurewebsites.net        │
└────────────────────────────────────────────────────────────┘
                        │
                        │ git tag v1.0.0
                        ▼
┌────────────────────────────────────────────────────────────┐
│                    Production                               │
├────────────────────────────────────────────────────────────┤
│ Location:    Azure Multi-Region                            │
│ Database:    Azure PostgreSQL (Geo-Replicated)             │
│ Redis:       Azure Redis Cache (Premium)                   │
│ Debug:       Disabled                                      │
│ Deploy:      Automatic (CI/CD with Approval)               │
│ URL:         email-helper.azurewebsites.net                │
│ Custom:      api.yourdomain.com (optional)                 │
└────────────────────────────────────────────────────────────┘
```

## 📁 File Structure Overview

```
email_helper/
│
├── Docker Configuration
│   ├── backend/Dockerfile              # Backend container (multi-stage)
│   ├── backend/.dockerignore           # Backend build exclusions
│   ├── backend/requirements.txt        # Python dependencies
│   ├── frontend/Dockerfile             # Frontend container (multi-stage)
│   ├── frontend/.dockerignore          # Frontend build exclusions
│   ├── frontend/nginx.conf             # Nginx configuration
│   ├── docker-compose.yml              # Development orchestration
│   └── docker-compose.prod.yml         # Production overrides
│
├── CI/CD Pipelines
│   ├── .github/workflows/ci.yml        # Continuous Integration
│   └── .github/workflows/cd.yml        # Continuous Deployment
│
├── Infrastructure as Code
│   ├── deployment/terraform/
│   │   ├── main.tf                     # Azure infrastructure
│   │   └── terraform.tfvars.example    # Configuration template
│   │
│   ├── deployment/scripts/
│   │   ├── deploy.sh                   # Deployment automation
│   │   ├── health-check.sh             # Health verification
│   │   └── backup.sh                   # Database backup
│   │
│   └── Makefile                        # Common operations
│
├── Documentation
│   ├── DEPLOYMENT.md                   # Master deployment guide
│   ├── QUICKSTART.md                   # Quick setup guide
│   ├── deployment/README.md            # Deployment overview
│   ├── deployment/PRODUCTION_DEPLOYMENT.md  # Production checklist
│   ├── deployment/MONITORING.md        # Monitoring guide
│   └── deployment/T10_SUMMARY.md       # Implementation summary
│
└── Configuration
    ├── .env.docker                     # Environment template
    └── .gitignore                      # Enhanced exclusions
```

## 🚀 Quick Commands Reference

```bash
# Development
make setup        # Initial setup
make up           # Start all services
make down         # Stop services
make logs         # View logs
make test         # Run tests
make health       # Health checks
make backup       # Backup database

# Deployment
make deploy                              # Deploy to production
./deployment/scripts/deploy.sh dev       # Deploy locally
./deployment/scripts/deploy.sh staging   # Deploy to staging
./deployment/scripts/deploy.sh production # Deploy to production

# Terraform
cd deployment/terraform
terraform init                           # Initialize
terraform plan                           # Preview changes
terraform apply                          # Apply changes
terraform output                         # View outputs

# Health Checks
./deployment/scripts/health-check.sh dev
./deployment/scripts/health-check.sh staging https://backend-staging.azurewebsites.net
curl http://localhost:8000/health        # Backend
curl http://localhost/health.html        # Frontend
```

## 📊 Resource Sizing Recommendations

### Development
- **Backend**: 1 vCPU, 1GB RAM
- **Frontend**: 0.5 vCPU, 512MB RAM
- **Database**: SQLite (file-based)
- **Redis**: 256MB
- **Cost**: ~$0/month (local)

### Staging
- **Backend**: 1 vCPU, 2GB RAM (B1)
- **Frontend**: 1 vCPU, 1GB RAM (B1)
- **Database**: Azure PostgreSQL Basic
- **Redis**: Azure Redis Basic
- **Cost**: ~$50-100/month

### Production
- **Backend**: 2 vCPU, 4GB RAM (P1v3)
- **Frontend**: 1 vCPU, 2GB RAM (P1v3)
- **Database**: Azure PostgreSQL Standard (with replica)
- **Redis**: Azure Redis Standard
- **Application Insights**: Standard
- **Cost**: ~$200-400/month

## 🎯 Success Metrics

- ✅ All services containerized
- ✅ CI/CD pipeline functional
- ✅ Infrastructure as Code complete
- ✅ Multi-environment deployment
- ✅ Monitoring and alerting configured
- ✅ Security best practices implemented
- ✅ Comprehensive documentation
- ✅ Automated backups configured
- ✅ Health checks operational
- ✅ Production-ready deployment

---

**Created**: 2024  
**Status**: Production Ready ✅  
**Version**: 1.0.0
