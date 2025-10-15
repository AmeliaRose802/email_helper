# Troubleshooting Guide

This guide helps you diagnose and resolve common issues when running Email Helper on localhost. If you're setting up for the first time, see the [Localhost Setup Guide](./LOCALHOST_SETUP.md) first.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Backend Issues](#backend-issues)
- [Frontend Issues](#frontend-issues)
- [Outlook COM Issues](#outlook-com-issues)
- [Azure OpenAI Issues](#azure-openai-issues)
- [CORS Issues](#cors-issues)
- [Database Issues](#database-issues)
- [Performance Issues](#performance-issues)
- [Log Files and Debugging](#log-files-and-debugging)
- [Getting Help](#getting-help)

## Quick Diagnostics

Run these quick checks first to identify the problem area:

### 1. Check if Backend is Running

```bash
curl http://localhost:8000/health
```

✅ **If it works:** Backend is healthy, skip to [Frontend Issues](#frontend-issues)  
❌ **If it fails:** Continue to [Backend Issues](#backend-issues)

### 2. Check if Frontend is Running

Open http://localhost:5173/ (or http://localhost:3000/) in your browser.

✅ **If it loads:** Frontend is running, check browser console for errors  
❌ **If it fails:** Continue to [Frontend Issues](#frontend-issues)

### 3. Check Outlook Status

Open Microsoft Outlook manually and verify it launches without errors.

✅ **If Outlook opens:** COM interface should work  
❌ **If Outlook fails:** Fix Outlook first, then retry

### 4. Check Ports

```bash
# Windows - check if ports are in use
netstat -ano | findstr :8000
netstat -ano | findstr :3000
netstat -ano | findstr :5173
```

If ports show results, they're in use. See [Port Already in Use](#port-already-in-use).

## Backend Issues

### Backend Won't Start

#### Symptom: `ModuleNotFoundError` or Import Errors

**Cause:** Missing Python dependencies

**Solution:**

```bash
# Reinstall dependencies
pip install -r requirements.txt

# If still failing, upgrade pip first
python -m pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
pip list | findstr fastapi
pip list | findstr pywin32
```

#### Symptom: `Cannot connect to database`

**Cause:** Missing database directory or permissions

**Solution:**

```bash
# Create the directory
mkdir runtime_data

# Check permissions (Windows)
icacls runtime_data

# If running, try removing the database and starting fresh
rm runtime_data/email_helper_history.db
python run_backend.py
```

#### Symptom: `Port 8000 is already in use`

**Cause:** Another process is using port 8000

**Solution:**

```bash
# Windows - find and kill the process
netstat -ano | findstr :8000
# Note the PID from the output
taskkill /PID <process_id> /F

# Or change the port in .env file
PORT=8001
```

Then restart the backend.

#### Symptom: `pywin32` Import Error on Windows

**Cause:** pywin32 not properly installed or registered

**Solution:**

```bash
# Uninstall and reinstall pywin32
pip uninstall pywin32
pip install pywin32

# Run post-install script (important!)
python Scripts/pywin32_postinstall.py -install

# If Scripts folder not found, try:
python -m pip install --upgrade pywin32
python -c "import win32com; print('pywin32 works!')"
```

#### Symptom: `SECRET_KEY not set` Error

**Cause:** Missing or invalid `.env` file

**Solution:**

```bash
# Copy example file
cp .env.localhost.example .env

# Verify file exists
ls -la .env

# Windows
dir .env
```

Edit `.env` and ensure `SECRET_KEY` is set.

#### Symptom: Backend Starts but Crashes Immediately

**Cause:** Configuration error or missing dependencies

**Solution:**

Check the error message carefully. Common issues:

1. **Invalid DATABASE_URL**: Ensure path is correct
   ```bash
   DATABASE_URL=sqlite:///./runtime_data/email_helper_history.db
   ```

2. **Invalid CORS_ORIGINS**: Must be valid JSON array
   ```bash
   CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
   ```

3. **Missing required files**: Check if critical files exist
   ```bash
   ls backend/main.py
   ls backend/core/config.py
   ```

### Backend Runs but Returns Errors

#### Symptom: `503 Service Unavailable` for All Endpoints

**Cause:** Backend started but core services failed to initialize

**Solution:**

1. Check backend terminal for startup errors
2. Verify Outlook is running
3. Check database connection:
   ```bash
   python -c "from backend.core.database import get_db; print('DB OK')"
   ```

#### Symptom: `500 Internal Server Error`

**Cause:** Unhandled exception in backend code

**Solution:**

1. Enable debug mode in `.env`:
   ```bash
   DEBUG=true
   ```

2. Restart backend and check detailed error traces

3. Check backend logs for stack traces

## Frontend Issues

### Frontend Won't Start

#### Symptom: `npm install` Fails

**Cause:** Node.js version incompatibility or network issues

**Solution:**

```bash
# Check Node.js version (must be 18+)
node --version

# Clear npm cache
npm cache clean --force

# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# If still failing, try with legacy peer deps
npm install --legacy-peer-deps
```

#### Symptom: `EADDRINUSE: Port 5173 already in use`

**Cause:** Port conflict

**Solution:**

```bash
# Option 1: Use different port
npm run dev -- --port 3001

# Option 2: Kill process using the port (Windows)
netstat -ano | findstr :5173
taskkill /PID <process_id> /F

# Option 3: Change default port in vite.config.ts
# Edit: server: { port: 3001 }
```

#### Symptom: `Module not found` or TypeScript Errors

**Cause:** Missing dependencies or incorrect imports

**Solution:**

```bash
# Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install

# Check TypeScript compilation
npx tsc --noEmit

# Clear Vite cache
rm -rf node_modules/.vite
```

### Frontend Connection Issues

#### Symptom: `Network Error` or `Failed to Fetch`

**Cause:** Backend not running or URL misconfigured

**Solution:**

1. Verify backend is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check frontend `.env.local`:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```

3. Verify URL matches backend's HOST and PORT in backend `.env`

4. **Restart frontend** after changing environment variables

#### Symptom: `Cannot GET /api/...` (404 Errors)

**Cause:** API endpoint doesn't exist or incorrect URL

**Solution:**

1. Check API documentation: http://localhost:8000/docs
2. Verify endpoint exists in backend
3. Check for typos in frontend API calls
4. Ensure frontend is using correct base URL

### Frontend Displays but Has Errors

#### Symptom: Blank Page or White Screen

**Cause:** JavaScript error preventing app from rendering

**Solution:**

1. Open browser DevTools (F12) and check Console for errors
2. Check Network tab for failed requests
3. Verify `.env.local` file exists and has correct values
4. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
5. Try incognito/private browsing mode

#### Symptom: Components Not Loading

**Cause:** Build issue or missing assets

**Solution:**

```bash
# Rebuild the application
npm run build

# Start fresh dev server
npm run dev
```

## Outlook COM Issues

### Cannot Connect to Outlook

#### Symptom: `Could not connect to Outlook` Error

**Cause:** Outlook not running or COM interface unavailable

**Solution:**

1. **Start Outlook manually** and ensure it opens without errors
2. Verify Outlook is configured with at least one email account
3. Check if Outlook is in a modal dialog state (close all dialogs)
4. Restart Outlook and try again
5. Run the backend with administrator privileges:
   ```bash
   # Right-click Command Prompt -> "Run as Administrator"
   python run_backend.py
   ```

#### Symptom: `pywintypes.com_error: (-2147221005, 'Invalid class string', None, None)`

**Cause:** Outlook not properly registered in Windows COM

**Solution:**

```bash
# Re-register Outlook
# Run as Administrator:
cd "C:\Program Files\Microsoft Office\root\Office16"
outlook.exe /regserver

# Verify Outlook version
outlook.exe /?
```

Note: Adjust Office16 path to match your Outlook version (Office14, Office15, Office16, etc.)

#### Symptom: `Access Denied` or Permission Errors

**Cause:** Outlook security settings blocking COM access

**Solution:**

1. Open Outlook → File → Options → Trust Center → Trust Center Settings
2. Go to "Programmatic Access"
3. Select "Never warn me about suspicious activity"
4. Click OK and restart Outlook
5. Try connecting again

**Security Note:** Only use this setting on trusted development machines.

#### Symptom: Outlook Connection Works but Emails Don't Load

**Cause:** Folder access or account issues

**Solution:**

1. Verify email account is connected in Outlook
2. Check if Inbox folder exists and has emails
3. Try using a different folder:
   ```python
   # Test with different folder in API call
   /api/emails?folder=Sent
   ```

4. Check Outlook is not in offline mode

### Outlook Crashes or Freezes

#### Symptom: Outlook Stops Responding

**Cause:** COM operation taking too long or Outlook overload

**Solution:**

1. Reduce batch size in email queries:
   ```env
   # In backend code or configuration
   MAX_EMAILS_PER_REQUEST=50  # Instead of 500
   ```

2. Close other applications using Outlook
3. Restart Outlook and backend
4. Check Windows Event Viewer for Outlook errors

## Azure OpenAI Issues

### Authentication Failures

#### Symptom: `401 Unauthorized` from Azure OpenAI

**Cause:** Invalid or expired API key

**Solution:**

1. Verify API key in `.env`:
   ```bash
   AZURE_OPENAI_API_KEY=your-actual-key-here
   ```

2. Check key hasn't expired in Azure Portal
3. Regenerate key if necessary:
   - Azure Portal → Your OpenAI Resource → Keys and Endpoint → Regenerate Key

4. Verify endpoint URL is correct:
   ```bash
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   ```

#### Symptom: `403 Forbidden` from Azure OpenAI

**Cause:** Insufficient permissions or wrong tenant

**Solution:**

1. Verify your Azure account has "Cognitive Services OpenAI User" role
2. Check if you're logged into correct Azure tenant:
   ```bash
   az account show
   az account list
   # Switch tenant if needed
   az login --tenant YOUR_TENANT_ID
   ```

3. Verify the resource allows your IP address (check firewall settings)

#### Symptom: `Resource Not Found` (404)

**Cause:** Incorrect deployment name or endpoint

**Solution:**

1. Verify deployment name in Azure Portal
2. Update `.env`:
   ```bash
   AZURE_OPENAI_DEPLOYMENT=your-actual-deployment-name
   ```

3. Check endpoint format (must include trailing slash):
   ```bash
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   ```

### Rate Limiting and Quota Issues

#### Symptom: `429 Too Many Requests`

**Cause:** Exceeded Azure OpenAI rate limits

**Solution:**

1. Reduce frequency of AI requests
2. Implement caching for repeated queries
3. Check quota in Azure Portal:
   - Azure OpenAI Resource → Quotas → Manage Quotas
4. Request quota increase if needed
5. Add retry logic with exponential backoff

#### Symptom: AI Responses are Slow

**Cause:** High load or quota limits

**Solution:**

1. Use a more powerful deployment (increase TPM)
2. Cache AI responses for common queries
3. Process emails in smaller batches
4. Consider using async processing for large batches

## CORS Issues

### Browser Shows CORS Errors

#### Symptom: `Access-Control-Allow-Origin` Error in Browser Console

**Cause:** Backend CORS configuration doesn't include frontend URL

**Solution:**

1. Check backend `.env` file:
   ```bash
   CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
   ```

2. Ensure frontend URL is in the list
3. Verify proper JSON array format (double quotes, not single)
4. **Restart backend** after changing CORS settings
5. Clear browser cache (Ctrl+Shift+R)

#### Symptom: CORS Error for Some Endpoints but Not Others

**Cause:** Missing CORS headers for specific routes or methods

**Solution:**

1. Check backend CORS configuration allows all required methods:
   ```bash
   CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
   ```

2. Ensure preflight OPTIONS requests are handled
3. Check browser DevTools Network tab for OPTIONS requests
4. Verify headers are allowed:
   ```bash
   CORS_ALLOW_HEADERS=["*"]
   ```

#### Symptom: CORS Works in Postman but Not Browser

**Cause:** Browser enforces CORS; Postman doesn't

**Solution:**

This is expected behavior. Fix the backend CORS configuration as described above. Postman bypasses CORS, so it's not a reliable test.

For development, you can temporarily disable CORS security:

```bash
# Backend .env (DEVELOPMENT ONLY)
CORS_ORIGINS=["*"]
```

**Warning:** Never use `["*"]` in production!

## Database Issues

### Database Locked

#### Symptom: `database is locked` Error

**Cause:** Multiple processes accessing SQLite database

**Solution:**

1. Stop all backend instances:
   ```bash
   # Windows - find processes using port 8000
   netstat -ano | findstr :8000
   taskkill /PID <process_id> /F
   ```

2. Check for orphaned SQLite connections:
   ```bash
   # Remove lock files
   rm runtime_data/*.db-lock
   rm runtime_data/*.db-shm
   rm runtime_data/*.db-wal
   ```

3. Restart backend

### Database Corruption

#### Symptom: `database disk image is malformed`

**Cause:** SQLite database corrupted

**Solution:**

1. **Backup current database:**
   ```bash
   cp runtime_data/email_helper_history.db runtime_data/email_helper_history.db.backup
   ```

2. **Try to recover:**
   ```bash
   sqlite3 runtime_data/email_helper_history.db
   .recover
   .quit
   ```

3. **If recovery fails, start fresh:**
   ```bash
   rm runtime_data/email_helper_history.db
   # Backend will recreate on next start
   python run_backend.py
   ```

### Migration Issues

#### Symptom: Schema Version Mismatch

**Cause:** Database schema outdated

**Solution:**

1. Backup database first
2. Run migrations (if available):
   ```bash
   python backend/migrations/run_migrations.py
   ```

3. Or start fresh if in development:
   ```bash
   rm runtime_data/email_helper_history.db
   python run_backend.py
   ```

## Performance Issues

### Slow Email Loading

**Cause:** Large number of emails or slow COM operations

**Solution:**

1. Reduce initial email load count
2. Implement pagination on frontend
3. Cache email list
4. Index frequently accessed fields in database
5. Close unnecessary Outlook folders

### High CPU Usage

**Cause:** Intensive AI processing or too many simultaneous requests

**Solution:**

1. Reduce AI batch sizes
2. Implement request queuing
3. Add rate limiting
4. Check for infinite loops in logs
5. Monitor with Task Manager (Ctrl+Shift+Esc)

### High Memory Usage

**Cause:** Large email content or memory leaks

**Solution:**

1. Process emails in smaller batches
2. Restart backend periodically during heavy use
3. Clear email cache
4. Check for memory leaks in custom code
5. Upgrade Python to latest patch version

## Log Files and Debugging

### Backend Logs

**Location:** Backend logs appear in the terminal where you ran `python run_backend.py`

**Enable detailed logging:**

```bash
# In .env file
DEBUG=true
LOG_LEVEL=DEBUG
```

**Capture logs to file:**

```bash
# Windows
python run_backend.py > backend.log 2>&1

# View logs
type backend.log
```

### Frontend Logs

**Location:** Browser DevTools Console (F12 → Console tab)

**Enable debug logging:**

```env
# In frontend/.env.local
VITE_DEBUG_LOGGING=true
```

**View network requests:**

1. Open DevTools (F12)
2. Go to Network tab
3. Perform the action that's failing
4. Check failed requests for status codes and error messages

### Outlook COM Logs

**Enable COM debugging:**

```python
# In backend code, add this to com_email_provider.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Windows Event Viewer:**

1. Open Event Viewer (Win+X → Event Viewer)
2. Windows Logs → Application
3. Filter for "Outlook" or "COM" errors

### Azure OpenAI Logs

**Check API request/response:**

```bash
# Enable debug in backend
DEBUG=true
```

**View in Azure Portal:**

1. Azure OpenAI Resource → Monitoring → Logs
2. Query: `requests | where target == "your-deployment"`

### Common Error Codes

| Code | Meaning | Where to Look |
|------|---------|---------------|
| 400 | Bad Request | Check request format, backend logs |
| 401 | Unauthorized | Check API keys, authentication |
| 403 | Forbidden | Check permissions, Azure role |
| 404 | Not Found | Check endpoint URL, routing |
| 429 | Rate Limited | Check Azure quota, slow down |
| 500 | Server Error | Check backend logs, stack trace |
| 503 | Service Unavailable | Check backend startup, services |

### Debugging Tools

**Backend debugging with VS Code:**

1. Create `.vscode/launch.json`:
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Python: FastAPI",
         "type": "python",
         "request": "launch",
         "module": "uvicorn",
         "args": ["backend.main:app", "--reload"],
         "jinja": true
       }
     ]
   }
   ```

2. Set breakpoints and press F5

**Frontend debugging:**

1. Browser DevTools (F12)
2. Sources tab → set breakpoints in TypeScript files
3. Use `debugger;` statements in code
4. Console for variable inspection

**Network debugging:**

Use browser DevTools Network tab to:
- Inspect request/response headers
- View request payload
- Check timing information
- Export HAR file for analysis

## Getting Help

If you've tried the troubleshooting steps and still have issues:

### 1. Gather Information

Before asking for help, collect:

- **Error messages** (exact text from logs)
- **Steps to reproduce** the issue
- **Environment info:**
  ```bash
  python --version
  node --version
  pip list > installed_packages.txt
  ```
- **Configuration** (sanitized `.env` files without secrets)
- **Logs** (backend terminal output, browser console)

### 2. Check Existing Resources

- [Localhost Setup Guide](./LOCALHOST_SETUP.md)
- [Backend README](../backend/README.md)
- [Frontend README](../frontend/README.md)
- [GitHub Issues](https://github.com/AmeliaRose802/email_helper/issues)

### 3. Search for Similar Issues

- Search GitHub Issues for keywords from your error
- Check closed issues - solution might already exist
- Search Stack Overflow for generic errors (e.g., pywin32, FastAPI)

### 4. Ask for Help

**Create a GitHub Issue:**

1. Go to [Issues page](https://github.com/AmeliaRose802/email_helper/issues)
2. Click "New Issue"
3. Provide:
   - Clear title describing the problem
   - Detailed description with error messages
   - Steps to reproduce
   - Your environment (OS, Python version, etc.)
   - What you've already tried

**Include in your issue:**

```markdown
## Problem Description
[Brief description of the issue]

## Environment
- OS: Windows 11
- Python: 3.12.0
- Node.js: 18.16.0
- Outlook: Microsoft 365

## Steps to Reproduce
1. Step one
2. Step two
3. Error occurs

## Error Message
```
[Paste exact error message here]
```

## What I've Tried
- [List troubleshooting steps you've already attempted]

## Additional Context
[Any other relevant information]
```

### 5. Emergency Workarounds

If you need the application running urgently:

**Skip AI features:**
```bash
# Remove Azure OpenAI credentials from .env
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
```

**Use mock data:**
```bash
# Start simple API with mock data instead
python simple_api.py
```

**Reset everything:**
```bash
# Complete fresh start (saves backups)
cp runtime_data runtime_data.backup -r
rm -rf runtime_data node_modules frontend/node_modules
mkdir runtime_data
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

## Preventive Measures

Avoid common issues by following these practices:

### Regular Maintenance

1. **Update dependencies regularly:**
   ```bash
   pip install --upgrade -r requirements.txt
   cd frontend && npm update
   ```

2. **Clear caches periodically:**
   ```bash
   rm -rf runtime_data/*.cache
   rm -rf frontend/node_modules/.vite
   ```

3. **Backup database:**
   ```bash
   cp runtime_data/email_helper_history.db backups/backup_$(date +%Y%m%d).db
   ```

### Best Practices

- **Always use virtual environments** for Python
- **Don't commit `.env` files** with secrets
- **Keep Outlook updated** to latest version
- **Restart services** after configuration changes
- **Monitor disk space** for database growth
- **Test after updates** before doing important work

### Health Monitoring

Create a simple health check script:

```bash
# health_check.sh
#!/bin/bash
echo "Checking backend..."
curl -s http://localhost:8000/health || echo "❌ Backend down"

echo "Checking frontend..."
curl -s http://localhost:5173/ || echo "❌ Frontend down"

echo "✅ All services running"
```

Run regularly to catch issues early.

## Summary

This troubleshooting guide covers the most common issues with Email Helper on localhost. Remember:

1. **Start simple** - check if services are running first
2. **Read error messages carefully** - they often indicate the exact problem
3. **Check logs** - backend terminal and browser console
4. **One change at a time** - easier to identify what fixed the issue
5. **Ask for help** - don't struggle alone if you're stuck

For additional assistance, refer to the [Localhost Setup Guide](./LOCALHOST_SETUP.md) or create an issue on GitHub.

Happy troubleshooting! 🔧
