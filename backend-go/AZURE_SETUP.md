# Azure OpenAI Setup for Go Backend

This backend uses **Azure AD authentication** (via `az login`) instead of API keys for better security.

## Prerequisites

1. **Azure CLI** must be installed
   - Download from: https://aka.ms/azure-cli
   - Or install via: `winget install Microsoft.AzureCLI`

2. **Azure OpenAI resource** must be deployed
   - You need an Azure OpenAI service instance
   - Get your endpoint URL (e.g., `https://your-resource.openai.azure.com/`)

## Setup Steps

### 1. Login to Azure

```powershell
az login
```

This will open your browser for authentication. After logging in, you'll see your Azure subscriptions.

### 2. Configure Azure OpenAI Endpoint

Edit the `.env` file in the `backend-go` directory and set your Azure OpenAI endpoint:

```properties
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

**Important:** Leave `AZURE_OPENAI_API_KEY` empty to use Azure AD authentication.

### 3. Grant Access to Azure OpenAI

Your Azure account needs "Cognitive Services OpenAI User" role on the Azure OpenAI resource:

```powershell
# Replace with your values
$resourceGroup = "your-resource-group"
$accountName = "your-openai-account"
$userEmail = "your-email@example.com"

# Get Azure OpenAI resource ID
$resourceId = az cognitiveservices account show `
    --name $accountName `
    --resource-group $resourceGroup `
    --query id -o tsv

# Assign role
az role assignment create `
    --role "Cognitive Services OpenAI User" `
    --assignee $userEmail `
    --scope $resourceId
```

### 4. Test the Connection

Run the backend and check the logs:

```powershell
cd backend-go
go run cmd/api/main.go
```

You should see:
```
🔐 Using Azure DefaultCredential authentication (az login)
✅ Azure OpenAI client authenticated via az login
```

## Troubleshooting

### "failed to create Azure credential"

- Make sure you've run `az login`
- Check that your Azure account is active: `az account show`

### "Authentication failed"

- Verify you have the "Cognitive Services OpenAI User" role assigned
- Your subscription must have access to Azure OpenAI services

### "Endpoint not configured"

- Check that `AZURE_OPENAI_ENDPOINT` is set in `.env`
- Endpoint should be the full URL including `https://`

## Why Not Use API Keys?

Azure AD authentication is preferred because:
- ✅ No secrets stored in environment variables
- ✅ Uses your Azure account permissions
- ✅ Automatic token refresh
- ✅ Audit trail of who accessed the service
- ✅ Can be revoked without changing keys

API keys are supported as fallback but not recommended.

## Matching Python Backend

This setup matches the Python backend's authentication approach using `DefaultAzureCredential`. Both backends now use the same secure authentication method.
