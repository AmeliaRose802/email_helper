# Deployment Guide - Email Helper

This guide provides comprehensive instructions for deploying the Email Helper application to various environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [CI/CD Pipeline](#cicd-pipeline)
- [Environment Configuration](#environment-configuration)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- **Docker** (v20.10+) - Container runtime
- **Docker Compose** (v2.0+) - Multi-container orchestration
- **kubectl** (v1.24+) - Kubernetes CLI (for K8s deployments)
- **Git** - Version control
- **Bash** - For running deployment scripts

### Cloud Requirements (for production)

- Container registry access (GitHub Container Registry, Docker Hub, or cloud provider)
- Kubernetes cluster (EKS, AKS, GKE, or self-hosted)
- PostgreSQL database (managed service recommended)
- Redis instance (managed service recommended)
- SSL certificates (for HTTPS)

## Local Development

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/AmeliaRose802/email_helper.git
   cd email_helper
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Verify deployment**
   ```bash
   curl http://localhost:8000/health
   ```

5. **Access the application**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - WebSocket: ws://localhost:8001

### Development Mode

For active development with hot-reloading:

```bash
# Start only infrastructure services
docker-compose up -d db redis

# Run the API locally
python -m uvicorn backend.main:app --reload --port 8000
```

## Docker Deployment

### Building Images

Build the production Docker image:

```bash
docker build -t email-helper:latest --target production .
```

Build with specific tag:

```bash
docker build -t email-helper:v1.0.0 --target production .
```

### Using Docker Compose

1. **Configure environment**
   ```bash
   cp .env.production.template .env.production
   # Edit .env.production with production values
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

3. **View logs**
   ```bash
   docker-compose logs -f
   ```

4. **Scale services**
   ```bash
   docker-compose up -d --scale worker=3
   ```

5. **Stop services**
   ```bash
   docker-compose down
   ```

### Manual Docker Run

Run the API container manually:

```bash
docker run -d \
  --name email-helper-api \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -e REDIS_URL="redis://host:6379" \
  -e AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/" \
  -e AZURE_OPENAI_API_KEY="your-key" \
  email-helper:latest
```

## Kubernetes Deployment

### Prerequisites

1. **Configure kubectl**
   ```bash
   # Set up your kubeconfig
   export KUBECONFIG=~/.kube/config
   
   # Verify connection
   kubectl cluster-info
   ```

2. **Create namespace**
   ```bash
   kubectl create namespace email-helper-prod
   ```

3. **Create secrets**
   ```bash
   kubectl create secret generic email-helper-secrets \
     --from-literal=database-url="postgresql://..." \
     --from-literal=redis-url="redis://..." \
     --from-literal=azure-openai-endpoint="https://..." \
     --from-literal=azure-openai-key="..." \
     -n email-helper-prod
   ```

### Deploy to Staging

```bash
# Update image tag in manifests
export IMAGE_TAG="v1.0.0"
sed -i "s|IMAGE_TAG|$IMAGE_TAG|g" k8s/staging/deployment.yaml

# Apply manifests
kubectl apply -f k8s/staging/deployment.yaml

# Check status
kubectl get pods -n email-helper-staging
kubectl rollout status deployment/email-helper-api -n email-helper-staging
```

### Deploy to Production

```bash
# Update image tag
export IMAGE_TAG="v1.0.0"
sed -i "s|IMAGE_TAG|$IMAGE_TAG|g" k8s/production/deployment.yaml

# Apply manifests
kubectl apply -f k8s/production/deployment.yaml

# Monitor rollout
kubectl rollout status deployment/email-helper-api -n email-helper-prod
kubectl get pods -n email-helper-prod -w
```

### Rollback Deployment

If something goes wrong:

```bash
# Rollback to previous version
kubectl rollout undo deployment/email-helper-api -n email-helper-prod

# Rollback to specific revision
kubectl rollout undo deployment/email-helper-api -n email-helper-prod --to-revision=2
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment/email-helper-api --replicas=5 -n email-helper-prod

# Check autoscaler status
kubectl get hpa -n email-helper-prod
```

## CI/CD Pipeline

### GitHub Actions Workflow

The CI/CD pipeline automatically:

1. **On Pull Request**: Runs tests and linting
2. **On Push to develop**: Deploys to staging
3. **On Push to main/master**: Deploys to production

### Required Secrets

Configure these in GitHub repository settings:

- `GITHUB_TOKEN` (automatically provided)
- `KUBECONFIG_STAGING` - Base64 encoded kubeconfig for staging
- `KUBECONFIG_PRODUCTION` - Base64 encoded kubeconfig for production

### Manual Workflow Trigger

Trigger deployment manually from GitHub Actions UI or:

```bash
# Using GitHub CLI
gh workflow run ci-cd.yml -f environment=production
```

### Deployment Script

Use the deployment script for automated deployments:

```bash
# Deploy to staging with Docker Compose
./scripts/deploy.sh staging latest

# Deploy to production with Kubernetes
DEPLOYMENT_TYPE=kubernetes ./scripts/deploy.sh production v1.0.0
```

## Environment Configuration

### Environment Variables

#### Required Variables

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint
- `AZURE_OPENAI_API_KEY` - Azure OpenAI API key
- `SECRET_KEY` - Application secret key (generate securely)

#### Optional Variables

- `DEBUG` - Enable debug mode (default: false)
- `LOG_LEVEL` - Logging level (default: INFO)
- `WORKER_COUNT` - Number of Uvicorn workers (default: 4)
- `MAX_CONNECTIONS` - Database connection pool size (default: 100)

### Production Configuration

1. **Create production environment file**
   ```bash
   cp .env.production.template .env.production
   ```

2. **Generate secure secret key**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Update all placeholder values**
   - Database credentials
   - Azure OpenAI credentials
   - Microsoft Graph API credentials
   - SSL certificates

### Secrets Management

#### Using Kubernetes Secrets

```bash
# Create from file
kubectl create secret generic email-helper-secrets \
  --from-file=.env.production \
  -n email-helper-prod

# Create from literal values
kubectl create secret generic email-helper-secrets \
  --from-literal=database-url="..." \
  --from-literal=redis-url="..." \
  -n email-helper-prod
```

#### Using External Secrets Manager

For production, consider using:
- **HashiCorp Vault**
- **AWS Secrets Manager**
- **Azure Key Vault**
- **Google Secret Manager**

## Monitoring and Maintenance

### Health Checks

Check application health:

```bash
# Local/Docker Compose
curl http://localhost:8000/health

# Kubernetes
kubectl exec -it <pod-name> -n email-helper-prod -- curl localhost:8000/health
```

### Logs

#### Docker Compose
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
```

#### Kubernetes
```bash
# API logs
kubectl logs -f deployment/email-helper-api -n email-helper-prod

# Worker logs
kubectl logs -f deployment/email-helper-worker -n email-helper-prod

# Tail last 100 lines
kubectl logs --tail=100 deployment/email-helper-api -n email-helper-prod
```

### Database Backups

Automated backup script (add to cron):

```bash
#!/bin/bash
# Backup PostgreSQL database
docker-compose exec -T db pg_dump -U user email_helper | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Resource Monitoring

Monitor resource usage:

```bash
# Docker
docker stats

# Kubernetes
kubectl top pods -n email-helper-prod
kubectl top nodes
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

**Symptoms**: API returns 500 errors, logs show database connection errors

**Solutions**:
- Verify `DATABASE_URL` is correct
- Check database is running: `docker-compose ps db`
- Check network connectivity
- Verify database credentials

#### 2. Redis Connection Failed

**Symptoms**: Background jobs not processing, WebSocket issues

**Solutions**:
- Verify `REDIS_URL` is correct
- Check Redis is running: `docker-compose ps redis`
- Test Redis: `redis-cli -h localhost -p 6379 ping`

#### 3. Container Crashes on Startup

**Symptoms**: Container restarts repeatedly

**Solutions**:
- Check logs: `docker-compose logs api`
- Verify all required environment variables are set
- Check for port conflicts
- Increase memory limits

#### 4. Kubernetes Pod CrashLoopBackOff

**Symptoms**: Pod keeps restarting

**Solutions**:
```bash
# Check pod status
kubectl describe pod <pod-name> -n email-helper-prod

# Check logs
kubectl logs <pod-name> -n email-helper-prod

# Check events
kubectl get events -n email-helper-prod --sort-by='.lastTimestamp'
```

#### 5. Slow API Response

**Symptoms**: High latency, timeouts

**Solutions**:
- Check resource usage: `kubectl top pods -n email-helper-prod`
- Scale horizontally: `kubectl scale deployment/email-helper-api --replicas=5`
- Review database query performance
- Check Redis cache hit rate

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Docker Compose
docker-compose up -d -e DEBUG=true

# Kubernetes
kubectl set env deployment/email-helper-api DEBUG=true -n email-helper-prod
```

### Getting Help

For issues not covered here:

1. Check application logs
2. Review GitHub Issues: https://github.com/AmeliaRose802/email_helper/issues
3. Run smoke tests: `./scripts/smoke-tests.sh`
4. Contact support team

## Security Best Practices

1. **Never commit secrets** - Use `.gitignore` for `.env` files
2. **Use secrets management** - Store sensitive data in secure vaults
3. **Enable SSL/TLS** - Always use HTTPS in production
4. **Regular updates** - Keep dependencies and base images updated
5. **Network policies** - Restrict inter-service communication
6. **RBAC** - Use role-based access control in Kubernetes
7. **Audit logs** - Enable and monitor audit logs
8. **Vulnerability scanning** - Regular security scans of images

## Performance Optimization

1. **Database connection pooling** - Configure appropriate pool size
2. **Caching** - Use Redis for frequently accessed data
3. **CDN** - Serve static assets via CDN
4. **Horizontal scaling** - Add more replicas for high load
5. **Resource limits** - Set appropriate CPU/memory limits
6. **Database indexes** - Ensure proper indexing
7. **API rate limiting** - Protect against abuse

## Next Steps

- Set up monitoring with Prometheus/Grafana
- Configure log aggregation with ELK stack
- Implement backup automation
- Set up disaster recovery procedures
- Configure auto-scaling policies
- Implement blue-green deployments
