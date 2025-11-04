# Clean Shutdown Implementation

## Overview

The Email Helper application implements graceful shutdown handling to ensure all services stop cleanly without error noise when you press Ctrl+C or otherwise terminate the application.

## Components

### 1. Backend (FastAPI/Uvicorn)

**File**: `run_backend.py`

- Registers signal handlers for `SIGINT` (Ctrl+C), `SIGTERM` (kill), and `SIGBREAK` (Windows Ctrl+Break)
- Catches `KeyboardInterrupt` exceptions
- Logs shutdown status clearly
- Exits with status code 0 on clean shutdown

**File**: `backend/main.py`

- Uses FastAPI's `lifespan` context manager for startup/shutdown
- Closes database connections gracefully on shutdown
- Logs all shutdown steps

### 2. Frontend (Vite/React)

The Vite dev server handles Ctrl+C gracefully by default. No special configuration needed.

### 3. Concurrently Configuration

**File**: `package.json`

The npm scripts use concurrently with these flags:
- `-k` or `--kill-others`: Kill all processes when one exits
- `-s first` or `--success first`: Return exit code of first process to exit

This ensures when you press Ctrl+C:
1. Signal is sent to all child processes
2. All processes shut down together
3. No orphaned processes remain

### 4. Electron App

**File**: `electron/main.js`

- Uses `SIGTERM` for graceful backend shutdown
- Implements 2-second timeout before forcing `SIGKILL`
- Handles cleanup on `will-quit` event

**File**: `electron/start-app.ps1`

- Defines `Cleanup` function to stop all services
- Waits for Electron process to exit
- Calls cleanup automatically when Electron closes

### 5. Development Script

**File**: `start-dev.ps1`

A PowerShell wrapper that:
- Cleans up existing processes and ports before starting
- Registers cleanup on PowerShell exit
- Catches interrupts and runs cleanup
- Uses proper `Stop-Process` cmdlets (no prompts!)

## Usage

### Development Mode

**Option 1: npm run dev (recommended)**
```powershell
npm run dev
```
Press Ctrl+C to stop. Both backend and frontend will shut down cleanly.

**Option 2: PowerShell wrapper (even cleaner)**
```powershell
.\start-dev.ps1
```
Provides better cleanup and status messages.

### Electron App

```powershell
cd electron
.\start-app.ps1
```
Close the Electron window or press Ctrl+C in the terminal. All services will shut down cleanly.

## What Happens on Shutdown

1. **Signal received** - Ctrl+C sends SIGINT to all processes
2. **Backend shutdown**:
   - Signal handler catches SIGINT
   - Logs "Shutdown signal received"
   - FastAPI lifespan manager runs cleanup
   - Database connections closed
   - Logs "Shutdown complete"
   - Exits with code 0
3. **Frontend shutdown**:
   - Vite dev server receives signal
   - Closes HTTP server
   - Exits cleanly
4. **Concurrently**:
   - Detects child process exit
   - Sends signals to other children
   - Waits for all to exit
   - Returns exit code

## Troubleshooting

### Still seeing error noise?

1. **Check you're using the updated scripts**:
   - `npm run dev` should have `-k -s first` flags
   - `run_backend.py` should have signal handlers

2. **Verify signal handling**:
   ```powershell
   # Start the app
   npm run dev
   
   # In another terminal, check processes
   Get-Process python,node | Select-Object Id,ProcessName,Path
   
   # Send SIGTERM manually (should be clean)
   Stop-Process -Name python -ErrorAction SilentlyContinue
   ```

3. **Check for orphaned processes**:
   ```powershell
   # After stopping, verify nothing is running
   Get-Process python,node -ErrorAction SilentlyContinue
   ```

### Port conflicts after shutdown

If ports 8000 or 3001 are still in use after shutdown:

```powershell
# Check what's using the ports
Get-NetTCPConnection -LocalPort 8000,3001 -ErrorAction SilentlyContinue

# Force cleanup
.\start-dev.ps1  # This script cleans up ports automatically
```

## Implementation Notes

### Why not taskkill?

**Never use `taskkill` in PowerShell scripts!**

❌ `taskkill /IM python.exe /F` - Can prompt for confirmation, blocks execution

✅ `Get-Process -Name python | Stop-Process -Force` - Never prompts, always works

### Signal handling priorities

1. **SIGINT** (Ctrl+C) - Caught by signal handlers, cleanest shutdown
2. **SIGTERM** (kill) - Caught by signal handlers, graceful shutdown
3. **SIGKILL** (kill -9) - Cannot be caught, immediate termination (use as last resort)

### Platform differences

- **Windows**: SIGINT, SIGTERM, and SIGBREAK are handled
- **Unix/Linux**: SIGINT and SIGTERM are standard
- **macOS**: Same as Unix, plus special handling in Electron for app lifecycle

## Best Practices

1. **Always use npm scripts or PowerShell wrappers** - They handle cleanup properly
2. **Don't manually kill processes** unless necessary
3. **Check for orphaned processes** after development sessions
4. **Use the cleanup functions** in scripts when adding new services
5. **Test shutdown behavior** when adding new components

## Related Files

- `package.json` - npm script configuration
- `run_backend.py` - Backend startup with signal handling
- `backend/main.py` - FastAPI lifespan management
- `electron/main.js` - Electron process management
- `electron/start-app.ps1` - Electron startup with cleanup
- `start-dev.ps1` - Development wrapper script
