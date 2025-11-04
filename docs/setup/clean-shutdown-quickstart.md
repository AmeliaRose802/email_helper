# Quick Reference: Clean Shutdown

## Starting the App

### Development Mode
```powershell
# Option 1: Standard npm command
npm run dev

# Option 2: Enhanced PowerShell wrapper (recommended)
.\start-dev.ps1
```

### Electron Desktop App
```powershell
cd electron
.\start-app.ps1
```

## Stopping the App

### Method 1: Keyboard Interrupt (Ctrl+C)
- Press `Ctrl+C` in the terminal
- Both backend and frontend will shut down cleanly
- No error noise!

### Method 2: Close Electron Window
- Click the X button on the Electron window
- All background services (backend/frontend) will be cleaned up automatically

### Method 3: Manual Process Kill (Emergency Only)
```powershell
# Stop all Email Helper processes
Get-Process python,node,electron -ErrorAction SilentlyContinue | Stop-Process -Force
```

## What's Different Now?

### Before (❌ Noisy)
```
^C
Traceback (most recent call last):
  File "...", line 123, in <module>
KeyboardInterrupt
[Frontend] Error: Connection refused
[Backend] Error: Interrupted
... lots more errors ...
```

### After (✅ Clean)
```
^C
[Backend] Shutdown signal received, stopping gracefully...
[Backend] Database connections closed
[Backend] Shutdown complete
[API] exited with code 0
[WEB] exited with code 0
```

## Troubleshooting

### Ports still in use after shutdown?
```powershell
# The start-dev.ps1 script automatically cleans up ports
.\start-dev.ps1
```

### Orphaned processes?
```powershell
# Check what's running
Get-Process python,node,electron -ErrorAction SilentlyContinue

# Clean up manually if needed
Get-Process python,node,electron -ErrorAction SilentlyContinue | Stop-Process -Force
```

## Key Files Changed

- `run_backend.py` - Signal handling for clean backend shutdown
- `backend/main.py` - FastAPI lifespan cleanup
- `package.json` - Concurrently with `-k -s first` flags
- `electron/main.js` - Graceful backend process termination
- `electron/start-app.ps1` - Cleanup function on exit
- `start-dev.ps1` - New development wrapper with cleanup

## Best Practices

✅ **DO**:
- Use `npm run dev` or `.\start-dev.ps1` to start
- Press Ctrl+C once to stop
- Wait 2-3 seconds for clean shutdown

❌ **DON'T**:
- Press Ctrl+C multiple times rapidly
- Use `taskkill` commands directly
- Manually kill processes unless necessary

---

For detailed technical documentation, see `docs/technical/clean-shutdown.md`
