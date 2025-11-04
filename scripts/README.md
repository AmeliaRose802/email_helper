# Email Helper Deployment Scripts

This directory contains one-click deployment scripts for running Email Helper on Windows localhost.

## Scripts Overview

### 🚀 start-localhost.bat
**One-click startup script for Windows**

Automatically:
- ✅ Checks all prerequisites (Python, Node.js, Outlook)
- ✅ Verifies port availability (8000, 5173)
- ✅ Installs missing dependencies
- ✅ Starts backend on http://localhost:8000
- ✅ Starts frontend on http://localhost:5173
- ✅ Opens browser to frontend
- ✅ Logs everything to `runtime_data/logs/`

**Usage:**
```batch
scripts\start-localhost.bat
```

### 🛑 stop-all.bat
**Graceful shutdown script**

Automatically:
- ✅ Finds and stops backend processes (port 8000)
- ✅ Finds and stops frontend processes (port 5173)
- ✅ Closes Email Helper windows
- ✅ Cleans up orphaned processes
- ✅ Logs shutdown process

**Usage:**
```batch
scripts\stop-all.bat
```

### 🔍 check-prerequisites.ps1
**Environment validation script**

Checks:
- ✅ Python 3.10+ installed
- ✅ Node.js 18+ installed
- ✅ Microsoft Outlook COM registered
- ✅ Port 8000 and 5173 availability
- ✅ Python dependencies (FastAPI, Uvicorn)
- ✅ Node dependencies installed
- ✅ Required directories exist

**Usage:**
```powershell
powershell -ExecutionPolicy Bypass -File scripts\check-prerequisites.ps1
```

### 🧪 verify_dependencies.py
**Python dependency verification script**

Checks:
- ✅ All required Python packages are installed
- ✅ Packages can be imported successfully
- ✅ No package dependency conflicts
- ✅ Reports missing or broken packages

**Usage:**
```bash
python scripts\verify_dependencies.py
```

**When to use:**
- After fresh checkout or clone
- After updating requirements.txt
- When encountering import errors
- Before starting development
- During troubleshooting

## Quick Start

1. **First time setup:**
   ```batch
   scripts\start-localhost.bat
   ```
   This will automatically install all dependencies and start the application.

2. **Daily use:**
   ```batch
   scripts\start-localhost.bat
   ```
   Quick start with prerequisite checking.

3. **Troubleshooting:**
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\check-prerequisites.ps1
   ```
   See detailed diagnostics.

4. **Shutdown:**
   ```batch
   scripts\stop-all.bat
   ```
   Clean shutdown of all services.

## Features

### Color-Coded Output
- 🟢 **Green**: Success messages
- 🟡 **Yellow**: Warnings
- 🔴 **Red**: Errors
- 🔵 **Cyan**: Info messages

### Logging
All operations are logged to:
```
runtime_data/logs/startup_<timestamp>.log
runtime_data/logs/shutdown_<timestamp>.log
```

Old log files are automatically cleaned up (keeps last 10).

### Port Conflict Handling
If ports 8000 or 5173 are in use:
1. Scripts detect the conflict
2. Show process ID using the port
3. Provide command to kill the process
4. Exit gracefully with error message

### Prerequisite Validation
Before starting:
- Checks Python version (3.10+)
- Checks Node.js version (18+)
- Verifies Outlook COM registration
- Validates port availability
- Confirms dependencies installed

### Graceful Shutdown
`stop-all.bat` performs:
1. Graceful termination (SIGTERM)
2. Waits 2 seconds
3. Forced termination if needed (SIGKILL)
4. Cleans up orphaned processes
5. Verifies ports are freed

## Common Issues

### "Port already in use"
**Problem:** Port 8000 or 5173 is occupied

**Solution:**
```batch
REM Find process using port
netstat -ano | findstr :8000

REM Kill process
taskkill /PID <process_id> /F
```

Or run `stop-all.bat` to clean up all processes.

### "Outlook COM not available"
**Problem:** Outlook not registered

**Solution:**
```batch
REM Run as Administrator
cd "C:\Program Files\Microsoft Office\root\Office16"
outlook.exe /regserver
```

### "Python/Node not found"
**Problem:** Python or Node.js not in PATH

**Solution:**
1. Install Python 3.10+ from https://python.org
2. Install Node.js 18+ from https://nodejs.org
3. Ensure "Add to PATH" is checked during installation
4. Restart command prompt

### Scripts won't run
**Problem:** PowerShell execution policy

**Solution:**
```powershell
REM Run as Administrator
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Requirements

- **OS:** Windows 10/11
- **Python:** 3.10 or higher
- **Node.js:** 18 or higher
- **Outlook:** Microsoft Outlook installed and configured
- **Ports:** 8000 and 5173 available

## Development Mode

For development with auto-reload:

**Backend (Terminal 1):**
```batch
python run_backend.py
```

**Frontend (Terminal 2):**
```batch
cd frontend
npm run dev
```

This gives you:
- Backend auto-reload on code changes
- Frontend hot module replacement
- Better debugging output
- Separate terminal windows for logs

## See Also

- [Localhost Setup Guide](../docs/LOCALHOST_SETUP.md) - Detailed setup instructions
- [Troubleshooting Guide](../docs/TROUBLESHOOTING.md) - Common issues and solutions
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when running)

## Support

If you encounter issues:
1. Check prerequisite script output
2. Review log files in `runtime_data/logs/`
3. Consult [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
4. Check backend and frontend terminal windows for errors
