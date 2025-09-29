# Production Deployment Checklist

This checklist guides you through deploying the Email Helper application to production.

## Pre-Deployment Checklist

### 1. Prerequisites
- [ ] Azure subscription with appropriate permissions
- [ ] Azure CLI installed and configured (`az --version`)
- [ ] Docker and Docker Compose installed
- [ ] Terraform installed (v1.0+)
- [ ] Git repository access
- [ ] Domain name (optional but recommended)

### 2. Azure Setup
- [ ] Create Azure service principal for deployments
  ```bash
  az ad sp create-for-rbac --name "email-helper-deploy" --role contributor \
    --scopes /subscriptions/{subscription-id} --sdk-auth
  ```
- [ ] Save service principal JSON output as GitHub secret `AZURE_CREDENTIALS_PROD`
- [ ] Create Azure OpenAI resource
- [ ] Set up Microsoft Graph API application registration
- [ ] Configure redirect URIs in Azure AD

### 3. GitHub Configuration
- [ ] Enable GitHub Actions in repository
- [ ] Configure GitHub Container Registry access
- [ ] Add required secrets to GitHub repository:
  - `AZURE_CREDENTIALS_PROD`
  - `AZURE_CREDENTIALS_STAGING`
  - `AZURE_CREDENTIALS_DEV`
  - `SECRET_KEY_PROD` (generate with `openssl rand -hex 32`)
  - `SECRET_KEY_STAGING`
  - `SECRET_KEY_DEV`
  - `AZURE_OPENAI_ENDPOINT`
  - `AZURE_OPENAI_API_KEY`
  - `GRAPH_CLIENT_SECRET_PROD`
  - `GRAPH_CLIENT_SECRET_STAGING`
  - `GRAPH_CLIENT_SECRET_DEV`

### 4. Environment Configuration
- [ ] Copy `.env.docker` to `.env` and configure for production
- [ ] Update `deployment/terraform/terraform.tfvars` with production values
- [ ] Review and update CORS origins in configuration
- [ ] Configure SSL/TLS certificates (handled by Azure)

## Deployment Steps

### Step 1: Build and Test Locally

```bash
# 1. Clone repository
git clone https://github.com/AmeliaRose802/email_helper.git
cd email_helper

# 2. Build Docker images
docker build -t email-helper-backend:latest -f backend/Dockerfile .
docker build -t email-helper-frontend:latest -f frontend/Dockerfile frontend/

# 3. Test locally with Docker Compose
cp .env.docker .env
# Edit .env with your configuration
docker-compose up -d

# 4. Run health checks
./deployment/scripts/health-check.sh dev

# 5. Run tests
docker-compose exec backend pytest
cd frontend && npm test
```

### Step 2: Push to Container Registry

```bash
# 1. Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# 2. Tag images
docker tag email-helper-backend:latest ghcr.io/ameliarose802/email_helper/backend:latest
docker tag email-helper-frontend:latest ghcr.io/ameliarose802/email_helper/frontend:latest

# 3. Push images
docker push ghcr.io/ameliarose802/email_helper/backend:latest
docker push ghcr.io/ameliarose802/email_helper/frontend:latest
```

### Step 3: Deploy Infrastructure with Terraform

```bash
# 1. Navigate to Terraform directory
cd deployment/terraform

# 2. Initialize Terraform
terraform init

# 3. Create production workspace
terraform workspace new production
terraform workspace select production

# 4. Review the plan
terraform plan -var="environment=production" \
  -var="backend_image=ghcr.io/ameliarose802/email_helper/backend:latest" \
  -var="frontend_image=ghcr.io/ameliarose802/email_helper/frontend:latest"

# 5. Apply the configuration
terraform apply -var="environment=production" \
  -var="backend_image=ghcr.io/ameliarose802/email_helper/backend:latest" \
  -var="frontend_image=ghcr.io/ameliarose802/email_helper/frontend:latest"

# 6. Save outputs
terraform output > ../production-outputs.txt
```

### Step 4: Configure Azure Services

```bash
# 1. Get deployment outputs
BACKEND_URL=$(terraform output -raw backend_url)
FRONTEND_URL=$(terraform output -raw frontend_url)
RESOURCE_GROUP=$(terraform output -raw resource_group_name)
KEY_VAULT=$(terraform output -raw key_vault_name)

# 2. Add secrets to Key Vault
az keyvault secret set --vault-name $KEY_VAULT --name "secret-key" --value "$(openssl rand -hex 32)"
az keyvault secret set --vault-name $KEY_VAULT --name "azure-openai-key" --value "$AZURE_OPENAI_API_KEY"
az keyvault secret set --vault-name $KEY_VAULT --name "graph-client-secret" --value "$GRAPH_CLIENT_SECRET"

# 3. Configure App Service environment variables
az webapp config appsettings set --name email-helper-production-backend \
  --resource-group $RESOURCE_GROUP \
  --settings \
    SECRET_KEY="@Microsoft.KeyVault(SecretUri=https://$KEY_VAULT.vault.azure.net/secrets/secret-key/)" \
    AZURE_OPENAI_API_KEY="@Microsoft.KeyVault(SecretUri=https://$KEY_VAULT.vault.azure.net/secrets/azure-openai-key/)" \
    GRAPH_CLIENT_SECRET="@Microsoft.KeyVault(SecretUri=https://$KEY_VAULT.vault.azure.net/secrets/graph-client-secret/)"
```

### Step 5: Database Setup

```bash
# If using PostgreSQL (production recommended)
# 1. Get database connection string
DB_HOST=$(az postgres flexible-server show --name email-helper-production-postgres \
  --resource-group $RESOURCE_GROUP --query "fullyQualifiedDomainName" -o tsv)

# 2. Run migrations (if needed)
docker run --rm \
  -e DATABASE_URL="postgresql://emailhelper:$DB_PASSWORD@$DB_HOST:5432/email_helper" \
  ghcr.io/ameliarose802/email_helper/backend:latest \
  alembic upgrade head
```

### Step 6: Verify Deployment

```bash
# 1. Check application health
curl -f https://$BACKEND_URL/health
curl -f https://$FRONTEND_URL/health.html

# 2. Test API endpoints
curl https://$BACKEND_URL/docs  # Should show API documentation

# 3. Check Application Insights
az monitor app-insights component show \
  --app email-helper-production-appinsights \
  --resource-group $RESOURCE_GROUP

# 4. View logs
az webapp log tail --name email-helper-production-backend \
  --resource-group $RESOURCE_GROUP
```

### Step 7: Configure DNS (Optional)

```bash
# 1. Get App Service IP
BACKEND_IP=$(az webapp show --name email-helper-production-backend \
  --resource-group $RESOURCE_GROUP --query "outboundIpAddresses" -o tsv | cut -d',' -f1)

# 2. Add custom domain
az webapp config hostname add \
  --webapp-name email-helper-production-backend \
  --resource-group $RESOURCE_GROUP \
  --hostname api.yourdomain.com

# 3. Enable SSL
az webapp config ssl bind \
  --name email-helper-production-backend \
  --resource-group $RESOURCE_GROUP \
  --certificate-thumbprint <thumbprint> \
  --ssl-type SNI
```

## Post-Deployment Checklist

### 1. Monitoring Setup
- [ ] Configure Application Insights alerts
- [ ] Set up email notifications for errors
- [ ] Configure uptime monitoring
- [ ] Review metric dashboards

### 2. Security Configuration
- [ ] Review firewall rules
- [ ] Enable threat detection
- [ ] Configure backup policies
- [ ] Review access policies in Key Vault
- [ ] Enable audit logging

### 3. Performance Tuning
- [ ] Configure auto-scaling rules
- [ ] Set up CDN for static assets (optional)
- [ ] Configure Redis cache settings
- [ ] Review App Service plan size

### 4. Documentation
- [ ] Document production URLs
- [ ] Update README with deployment information
- [ ] Create runbook for common operations
- [ ] Document rollback procedures

## Continuous Deployment via GitHub Actions

Once initial setup is complete, subsequent deployments are automatic:

1. **Push to main branch** - Triggers staging deployment
2. **Create release tag** (e.g., `v1.0.0`) - Triggers production deployment
3. **Manual deployment** - Use GitHub Actions workflow dispatch

### Creating a Release

```bash
# 1. Create and push tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 2. GitHub Actions automatically:
#    - Builds Docker images
#    - Pushes to container registry
#    - Deploys to production
#    - Runs health checks
```

## Rollback Procedures

### Quick Rollback

```bash
# 1. Identify previous working version
docker images ghcr.io/ameliarose802/email_helper/backend

# 2. Update Terraform variables to previous image
terraform apply -var="backend_image=ghcr.io/ameliarose802/email_helper/backend:v1.0.0"

# 3. Verify rollback
curl -f https://$BACKEND_URL/health
```

### Full Infrastructure Rollback

```bash
# 1. Checkout previous Terraform state
git checkout <previous-commit>

# 2. Apply previous configuration
cd deployment/terraform
terraform apply

# 3. Verify services
./deployment/scripts/health-check.sh production $BACKEND_URL $FRONTEND_URL
```

## Maintenance Tasks

### Database Backup

```bash
# Manual backup
az postgres flexible-server backup create \
  --resource-group $RESOURCE_GROUP \
  --name email-helper-production-postgres
```

### Scaling Operations

```bash
# Scale App Service
az webapp scale --name email-helper-production-backend \
  --resource-group $RESOURCE_GROUP \
  --instance-count 3

# Scale Redis
az redis update --name email-helper-production-redis \
  --resource-group $RESOURCE_GROUP \
  --sku Standard --vm-size C1
```

### Log Management

```bash
# Stream logs
az webapp log tail --name email-helper-production-backend \
  --resource-group $RESOURCE_GROUP

# Download logs
az webapp log download --name email-helper-production-backend \
  --resource-group $RESOURCE_GROUP \
  --log-file production-logs.zip
```

## Troubleshooting

### Common Issues

**Application won't start**
1. Check Application Insights for errors
2. Review environment variables in App Service
3. Verify Key Vault access policies
4. Check Docker image exists in registry

**Database connection errors**
1. Verify connection string in App Service settings
2. Check PostgreSQL firewall rules
3. Verify managed identity permissions
4. Test connection from Azure Cloud Shell

**Performance issues**
1. Review Application Insights performance metrics
2. Check Redis cache hit rates
3. Monitor database query performance
4. Scale App Service plan if needed

## Support and Resources

- **Azure Support**: https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade
- **GitHub Issues**: https://github.com/AmeliaRose802/email_helper/issues
- **Documentation**: See `/deployment/README.md`

## Emergency Contacts

- Azure Subscription Admin: [admin@yourdomain.com]
- DevOps Team: [devops@yourdomain.com]
- On-call Engineer: [oncall@yourdomain.com]
