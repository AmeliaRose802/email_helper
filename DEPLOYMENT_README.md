# Deployment Configuration - Quick Start

This directory contains comprehensive deployment configuration for the Email Helper application.

## 📁 Directory Structure

```
.
├── Dockerfile                      # Multi-stage Docker build for FastAPI backend
├── docker-compose.yml              # Local development orchestration
├── nginx.conf                      # Reverse proxy and load balancer config
├── .dockerignore                   # Docker build exclusions
├── .env.production.template        # Production environment template
├── .github/workflows/
│   └── ci-cd.yml                  # GitHub Actions CI/CD pipeline
├── k8s/
│   ├── production/                # Production Kubernetes manifests
│   │   └── deployment.yaml
│   └── staging/                   # Staging Kubernetes manifests
│       └── deployment.yaml
├── deployment/
│   ├── sql/                       # Database initialization scripts
│   │   └── init.sql
│   └── ssl/                       # SSL certificates directory
│       └── README.md
└── scripts/
    ├── deploy.sh                  # Automated deployment script
    └── smoke-tests.sh             # Post-deployment validation
```

## 🚀 Quick Start

### Local Development

```bash
# 1. Create environment file
cp .env.example .env

# 2. Start all services
docker-compose up -d

# 3. Verify deployment
curl http://localhost:8000/health
```

### Production Deployment

```bash
# 1. Configure production environment
cp .env.production.template .env.production
# Edit .env.production with your values

# 2. Deploy with script
./scripts/deploy.sh production v1.0.0

# 3. Run smoke tests
./scripts/smoke-tests.sh production
```

## 📚 Documentation

- **[Full Deployment Guide](docs/DEPLOYMENT.md)** - Comprehensive deployment instructions
- **[GitHub Actions CI/CD](.github/workflows/ci-cd.yml)** - Automated pipeline configuration
- **[Kubernetes Guide](k8s/)** - Container orchestration setup
- **[Docker Compose Guide](docker-compose.yml)** - Local development setup

## 🔧 Key Features

### Docker Configuration
- ✅ Multi-stage builds for optimized images
- ✅ Non-root user for security
- ✅ Health checks for all services
- ✅ Multi-service orchestration

### CI/CD Pipeline
- ✅ Automated testing on pull requests
- ✅ Docker image building and publishing
- ✅ Automated deployment to staging/production
- ✅ Security scanning with Trivy

### Kubernetes Deployment
- ✅ Production-ready manifests
- ✅ Horizontal Pod Autoscaling
- ✅ Resource limits and requests
- ✅ Health checks and probes
- ✅ Secret management

### Monitoring & Operations
- ✅ Health check endpoints
- ✅ Automated smoke tests
- ✅ Deployment rollback capability
- ✅ Comprehensive logging

## 🛠️ Available Commands

### Docker Commands

```bash
# Build image
docker build -t email-helper:latest --target production .

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Scale workers
docker-compose up -d --scale worker=3
```

### Kubernetes Commands

```bash
# Deploy to production
kubectl apply -f k8s/production/deployment.yaml

# Check status
kubectl get pods -n email-helper-prod

# View logs
kubectl logs -f deployment/email-helper-api -n email-helper-prod

# Scale deployment
kubectl scale deployment/email-helper-api --replicas=5 -n email-helper-prod

# Rollback
kubectl rollout undo deployment/email-helper-api -n email-helper-prod
```

### Deployment Scripts

```bash
# Deploy with Docker Compose
./scripts/deploy.sh staging latest

# Deploy with Kubernetes
DEPLOYMENT_TYPE=kubernetes ./scripts/deploy.sh production v1.0.0

# Run smoke tests
./scripts/smoke-tests.sh production

# Help
./scripts/deploy.sh --help
```

## 🔐 Security Considerations

1. **Environment Variables**: Never commit `.env` files
2. **Secrets Management**: Use Kubernetes secrets or external vaults
3. **SSL/TLS**: Always use HTTPS in production
4. **Non-root User**: All containers run as non-root
5. **Image Scanning**: Automated security scanning in CI/CD
6. **Network Policies**: Restrict inter-service communication

## 📊 Testing

All deployment configurations are tested:

```bash
# Run deployment tests
pytest backend/tests/deployment/ -v

# Tests include:
# - Docker build validation
# - Kubernetes manifest syntax
# - Security configurations
# - Environment templates
# - CI/CD pipeline configuration
```

## 🌐 Supported Platforms

- **Container Platforms**: Docker, Kubernetes, OpenShift
- **Cloud Providers**: AWS (EKS), Azure (AKS), GCP (GKE)
- **CI/CD**: GitHub Actions (configured), adaptable to GitLab CI, Jenkins

## 📈 Scaling Strategy

- **Horizontal Scaling**: Kubernetes HPA based on CPU/memory
- **Vertical Scaling**: Adjustable resource limits
- **Database**: PostgreSQL with connection pooling
- **Caching**: Redis for improved performance
- **Load Balancing**: Nginx for API traffic distribution

## 🐛 Troubleshooting

Common issues and solutions:

```bash
# Database connection failed
docker-compose logs db
kubectl describe pod <pod-name> -n email-helper-prod

# Container crashes
docker-compose logs api
kubectl logs <pod-name> -n email-helper-prod

# Check service health
curl http://localhost:8000/health
kubectl get pods -n email-helper-prod
```

## 📝 Next Steps

1. Review [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions
2. Configure environment variables for your setup
3. Set up CI/CD secrets in GitHub
4. Deploy to staging for testing
5. Configure monitoring and alerting
6. Set up backup automation

## 🤝 Contributing

When adding new deployment configurations:

1. Update relevant documentation
2. Add tests in `backend/tests/deployment/`
3. Update CI/CD pipeline if needed
4. Test in staging before production

## 📞 Support

For deployment issues:

1. Check logs: `docker-compose logs` or `kubectl logs`
2. Run smoke tests: `./scripts/smoke-tests.sh`
3. Review [DEPLOYMENT.md](docs/DEPLOYMENT.md)
4. Open an issue on GitHub

---

**Ready to deploy!** 🚀 Start with the [Full Deployment Guide](docs/DEPLOYMENT.md) for step-by-step instructions.
