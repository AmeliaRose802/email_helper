# Secure Azure Authentication Setup

This project has been updated to use secure Azure authentication instead of hardcoded API keys.

## 🔐 Security Improvements

✅ **Removed all hardcoded API keys** from source code  
✅ **Added DefaultAzureCredential** support (uses `az login`)  
✅ **Environment variable fallback** with `.env` file (not committed)  
✅ **Updated .gitignore** to prevent credential leaks  

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)
```powershell
cd scripts
python secure_setup.py
```

### Option 2: Manual Setup

1. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```powershell
   # Copy template
   copy .env.template .env
   
   # Edit .env with your values
   # AZURE_OPENAI_ENDPOINT=https://ameliapayne-5039-test-e-resource.openai.azure.com/
   # AZURE_OPENAI_DEPLOYMENT=gpt-4o
   ```

3. **Choose authentication method**:

   **Option A: Azure CLI (Recommended)**
   ```powershell
   # Install Azure CLI if not already installed
   # https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
   
   # Login to Azure
   az login
   ```
   
   **Option B: API Key Fallback**
   ```powershell
   # Add to your .env file:
   # AZURE_OPENAI_API_KEY=your-api-key-here
   ```

4. **Test configuration**:
   ```powershell
   cd scripts
   python azure_config.py
   ```

## 🔧 How It Works

### Authentication Priority
1. **DefaultAzureCredential** (if available and no API key set)
   - Uses `az login` session
   - More secure, no stored credentials
   - Automatically refreshes tokens
   
2. **API Key** (fallback from `.env` file)
   - Only if `AZURE_OPENAI_API_KEY` is set
   - Still secure (not in source code)

### File Security
- `.env` file is **never committed** to git
- All prompty files use environment variables
- API keys removed from all source files

## 📁 Important Files

- `.env.template` - Template for environment variables
- `.env` - Your actual environment variables (NOT COMMITTED)
- `scripts/azure_config.py` - Secure authentication manager
- `scripts/secure_setup.py` - Automated setup script

## 🛡️ Security Best Practices

### Before First Commit
1. Verify `.env` is in `.gitignore` ✅
2. Remove any hardcoded credentials ✅
3. Test with both authentication methods ✅

### For Production
1. Use Azure Managed Identity when possible
2. Rotate API keys regularly
3. Monitor authentication logs
4. Use least privilege access

## 🔍 Troubleshooting

### "Authentication failed"
1. Check if `az login` is working: `az account show`
2. Verify your `.env` file has correct values
3. Test connection: `python scripts/azure_config.py`

### "Import azure.identity could not be resolved"
```powershell
pip install azure-identity
```

### "DefaultAzureCredential failed"
This is normal if you haven't run `az login`. The system will fall back to API key authentication.

## ⚡ Usage

After setup, run the email helper as usual:
```powershell
cd scripts
python email_manager_main.py
```

The system will automatically:
- Try Azure CLI authentication first
- Fall back to API key if needed
- Show which method is being used
