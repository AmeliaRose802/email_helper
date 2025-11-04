# Email Classification Fix - Azure AD Authentication

## Problem

Email classification was not working in the Go backend because it was configured to use API keys, but the system is designed to use **Azure AD authentication** (like the Python backend).

## Changes Made

### 1. Updated Azure OpenAI Client (`pkg/azureopenai/client.go`)

- **Before:** Required API key for authentication
- **After:** Uses `DefaultAzureCredential` (Azure AD auth via `az login`)
- **Fallback:** Still supports API key if explicitly set (not recommended)

```go
// Now uses Azure Identity
import "github.com/Azure/azure-sdk-for-go/sdk/azidentity"

// Prefers DefaultAzureCredential over API key
if apiKey == "" {
    cred, err := azidentity.NewDefaultAzureCredential(nil)
    // ... authenticate with Azure AD
} else {
    // Fallback to API key
}
```

### 2. Updated Configuration Files

**`backend-go/.env`:**
```properties
# Now empty - uses az login instead of API key
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
```

**`.env` (root):**
- Updated comments to clarify Azure AD authentication is preferred

### 3. Updated Service Initialization

**`internal/services/email_service.go`:**
- Removed requirement for API key
- AI client initializes if endpoint is configured (even with empty API key)

## How to Fix Classification

### Step 1: Verify Azure Login

```powershell
az login
az account show
```

You should see your Azure account details.

### Step 2: Find Your Azure OpenAI Endpoint

Option A - If you have an Azure OpenAI resource:
```powershell
az cognitiveservices account list --query "[?kind=='OpenAI']" -o table
```

Option B - Check with your Azure admin:
- Ask for the Azure OpenAI endpoint URL
- Format: `https://your-resource.openai.azure.com/`

### Step 3: Configure the Endpoint

Edit `backend-go/.env`:
```properties
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

**Important:** Leave `AZURE_OPENAI_API_KEY` empty to use Azure AD auth.

### Step 4: Grant Access (if needed)

Your Azure account needs "Cognitive Services OpenAI User" role:

```powershell
# Get your user object ID
$userId = az ad signed-in-user show --query id -o tsv

# Assign role (replace with your resource details)
az role assignment create `
    --role "Cognitive Services OpenAI User" `
    --assignee $userId `
    --scope "/subscriptions/{subscription-id}/resourceGroups/{rg}/providers/Microsoft.CognitiveServices/accounts/{account-name}"
```

### Step 5: Rebuild and Start Backend

```powershell
cd backend-go
go build -o bin/email-helper.exe cmd/api/main.go
.\bin\email-helper.exe
```

**Expected output:**
```
🔐 Using Azure DefaultCredential authentication (az login)
✅ Azure OpenAI client authenticated via az login
```

### Step 6: Test Classification

The frontend will automatically classify emails when you open the email list. Check the browser console for classification logs.

## Troubleshooting

### "Azure OpenAI endpoint not configured"

**Problem:** `AZURE_OPENAI_ENDPOINT` is empty in `.env`

**Solution:** Set the endpoint URL (see Step 3 above)

### "failed to create Azure credential"

**Problem:** Not logged into Azure CLI

**Solution:**
```powershell
az login
```

### "Authentication failed" or "Access denied"

**Problem:** Your Azure account doesn't have permissions

**Solutions:**
1. Verify you're using the right Azure subscription:
   ```powershell
   az account set --subscription "your-subscription-name"
   ```

2. Request "Cognitive Services OpenAI User" role from your Azure admin

3. Check if your organization requires additional permissions

### Classification Still Not Working

1. **Check browser console** for error messages
2. **Check backend logs** for AI service errors
3. **Verify endpoint is correct:**
   ```powershell
   # Test the endpoint manually
   az rest --method post `
     --uri "https://your-resource.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-01" `
     --body '{"messages":[{"role":"user","content":"test"}],"max_tokens":5}'
   ```

4. **Check deployment name** - ensure `gpt-4o` (or your model) is deployed

## Why This Approach?

### Security Benefits

✅ **No secrets in code or env files** - Authentication uses your Azure identity  
✅ **Automatic token refresh** - No expired keys to update  
✅ **Audit trail** - Azure tracks who accessed OpenAI  
✅ **Easy revocation** - Remove role assignment instead of rotating keys  
✅ **Matches Python backend** - Consistent authentication across all backends  

### How It Works

1. You run `az login` once
2. Azure CLI stores credentials securely
3. Go backend uses `DefaultAzureCredential` to get tokens
4. Tokens are automatically refreshed as needed
5. No API keys needed anywhere

This is the **same authentication flow** used by the Python backend via `DefaultAzureCredential`.

## For Developers

If you're developing and need to use API keys temporarily:

1. Set `AZURE_OPENAI_API_KEY` in `.env`
2. Backend will detect it and use key-based auth
3. You'll see: `⚠️  Using API key authentication`

But for production and normal use, leave it empty and use Azure AD auth.

## Next Steps

Once classification is working:
1. Test by opening the email list in the frontend
2. Emails should show AI categories (action_item, fyi, newsletter, etc.)
3. Check the "Stats" view to see classification accuracy
4. Use "Apply to Outlook" to move emails to folders based on categories
