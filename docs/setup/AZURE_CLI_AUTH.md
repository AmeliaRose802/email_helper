# Azure CLI Authentication Setup

## Overview

The Go backend prefers Azure CLI authentication (`az login`) over API key authentication for better security. This guide explains how to switch from API key to Azure CLI authentication.

## Benefits of Azure CLI Authentication

- ✅ **No secrets in config files** - Credentials managed by Azure CLI
- ✅ **Automatic token rotation** - Azure CLI handles token refresh
- ✅ **Better security** - Follows Azure SDK guidelines
- ✅ **Multi-environment support** - Easy switching between subscriptions
- ✅ **Audit trail** - Authentication events tracked by Azure AD

## Prerequisites

1. Install [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
2. Access to Azure OpenAI subscription

## Setup Steps

### 1. Install Azure CLI

**Windows:**
```powershell
winget install -e --id Microsoft.AzureCLI
```

**Mac:**
```bash
brew install azure-cli
```

**Linux:**
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

### 2. Login to Azure

```bash
az login
```

This opens a browser window for authentication. Sign in with your Azure account.

### 3. Set Active Subscription

If you have multiple subscriptions:

```bash
# List subscriptions
az account list --output table

# Set active subscription
az account set --subscription "<subscription-id-or-name>"
```

### 4. Verify Access to Azure OpenAI

```bash
# List Azure OpenAI accounts
az cognitiveservices account list --query "[?kind=='OpenAI']"
```

### 5. Update Backend Configuration

Edit `backend-go/.env`:

```dotenv
# Remove or comment out the API key
# AZURE_OPENAI_API_KEY=your-api-key-here

# Keep endpoint and other settings
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-01
```

**Important:** Set `AZURE_OPENAI_API_KEY` to empty string or remove it entirely.

### 6. Restart Backend

```powershell
cd backend-go
.\start-go-backend.ps1
```

You should see:
```
🔐 Using Azure DefaultCredential authentication (az login)
✅ Azure OpenAI client authenticated via az login
```

## Troubleshooting

### Error: "failed to create Azure credential"

**Cause:** Not logged in to Azure CLI

**Solution:**
```bash
az login
az account show  # Verify login
```

### Error: "No subscriptions found"

**Cause:** Azure account has no active subscriptions

**Solution:**
1. Verify subscription access in Azure Portal
2. Contact your Azure administrator

### Still seeing "Using API key authentication" warning

**Cause:** API key is still set in `.env`

**Solution:**
```dotenv
# Option 1: Remove the line
# AZURE_OPENAI_API_KEY=...

# Option 2: Set to empty string
AZURE_OPENAI_API_KEY=

# Option 3: Comment it out
# AZURE_OPENAI_API_KEY=your-old-key
```

### Error: "endpoint ... not found"

**Cause:** Wrong endpoint format or network issue

**Solution:**
1. Verify endpoint in Azure Portal
2. Use `.cognitiveservices.azure.com` instead of `.openai.azure.com`
3. Check firewall/network settings

## Azure Role Requirements

Your Azure account needs these roles on the Azure OpenAI resource:

- **Cognitive Services OpenAI User** - Minimum required
- **Cognitive Services OpenAI Contributor** - For full access

**Grant role in Azure Portal:**
1. Navigate to Azure OpenAI resource
2. Go to **Access Control (IAM)**
3. Click **Add role assignment**
4. Select **Cognitive Services OpenAI User**
5. Assign to your user account

## Security Best Practices

1. ✅ **Use az login** - Preferred authentication method
2. ❌ **Avoid API keys** - Only use for automated scripts where az login isn't available
3. ✅ **Rotate credentials** - az login tokens auto-rotate
4. ✅ **Use separate subscriptions** - Dev/Test/Prod separation
5. ✅ **Enable Azure AD logging** - Track authentication events

## FAQ

**Q: Can I use API keys for development?**

A: Yes, but not recommended. API keys don't expire and are harder to rotate securely.

**Q: How long do az login sessions last?**

A: Typically 90 days, but Azure CLI automatically refreshes tokens.

**Q: What if I need to authenticate in CI/CD?**

A: Use Service Principal authentication:
```bash
az login --service-principal -u <app-id> -p <password> --tenant <tenant-id>
```

**Q: Do I need to run az login every time?**

A: No, Azure CLI caches credentials. Only re-login if session expires.

## Verification

Test authentication is working:

```bash
# Verify Azure CLI auth
az account show

# Test Go backend
cd backend-go
go run cmd/api/main.go

# Should see: "🔐 Using Azure DefaultCredential authentication (az login)"
```

## Related Documentation

- [Azure CLI Installation](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- [Azure Identity SDK](https://pkg.go.dev/github.com/Azure/azure-sdk-for-go/sdk/azidentity)
- [Azure RBAC Roles](https://docs.microsoft.com/en-us/azure/role-based-access-control/built-in-roles)
