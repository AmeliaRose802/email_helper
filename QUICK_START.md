# 🚀 Email Helper - Quick Start Guide

## Starting the Application

**Run this ONE command:**

```powershell
cd C:\Users\ameliapayne\email_helper\electron
.\start-app.ps1
```

This script will:
1. ✅ Clean up old processes
2. ✅ Start the Python backend (port 8000)
3. ✅ Start the React frontend (port 3000)
4. ✅ Launch the Electron desktop app
5. ✅ Open DevTools automatically for debugging

## What Should Happen

- **Terminal**: Shows startup progress and service status
- **Main Window**: Email Helper Dashboard with buttons
- **DevTools Window**: Separate window for debugging (can be closed)

## Current Known Issues

### ❌ Buttons Don't Work
**Symptoms:** Clicking buttons does nothing, no alerts appear

**Cause:** JavaScript error: `ReferenceError: dragEvent is not defined`

**Debug Steps:**
1. Open the app with `.\start-app.ps1`
2. DevTools opens automatically
3. Click on the "Console" tab in DevTools
4. Click a button (e.g., "📥 Process New Emails")
5. Check console for error messages

### 🔍 How to Debug

In the **DevTools Console** (not terminal), you should see:
- ✅ `Γ£à App component rendering` - Good, React is loading
- ✅ `[API Debug] API Request Headers` - API calls are being made
- ❌ `ReferenceError: dragEvent is not defined` - **This is the problem!**

## Troubleshooting

### App Won't Start
```powershell
# Kill all processes and try again
Get-Process python,node,electron -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 3
cd C:\Users\ameliapayne\email_helper\electron
.\start-app.ps1
```

### Backend API Not Responding
```powershell
# Test backend manually
curl http://localhost:8000/health
# Should return: {"status":"healthy",...}
```

### Frontend Not Loading
```powershell
# Test frontend manually
curl http://localhost:3000
# Should return HTML content
```

### Ports Already in Use
```powershell
# Free ports 8000 and 3000
@(8000, 3000) | ForEach-Object {
    Get-NetTCPConnection -LocalPort $_ -ErrorAction SilentlyContinue | 
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}
```

## Architecture

```
Email Helper Desktop App
│
├── Backend (Python FastAPI)
│   └── http://localhost:8000
│       ├── /health - Health check
│       ├── /api/emails - Email endpoints
│       └── /api/tasks - Task endpoints
│
├── Frontend (React + Vite)
│   └── http://localhost:3000
│       └── Served by Vite dev server
│
└── Electron Wrapper
    └── Desktop window that loads frontend
        └── Communicates with backend via HTTP
```

## Next Steps

1. **Fix the `dragEvent` error** - This is blocking button clicks
2. **Implement actual API calls** - Currently shows alerts
3. **Test with real Outlook data** - Verify email processing works

## Support

If you encounter issues:
1. Check the DevTools Console for errors
2. Check terminal for backend/frontend logs
3. Verify all three components are running
4. Try the diagnostic page: Open DevTools and navigate to `file:///.../electron/diagnostic.html`
