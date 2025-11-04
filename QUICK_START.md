# Quick Start: Running the App Without Issues

## TL;DR - Just Do This

```powershell
# Kill any existing processes
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Start the app
npm run dev
```

That's it! No more "Terminate batch job" prompts, no COM threading errors, no encoding crashes.

## What Changed?

We fixed the three major issues:

### 1. No More Prompts
- **Before:** Auto-reload prompted "Terminate batch job (Y/N)?" and blocked terminal
- **After:** Runs in no-reload mode by default (use `npm run dev:reload` if you need hot-reload)

### 2. COM Threading Fixed  
- **Before:** `"The application called an interface that was marshalled for a different thread"`
- **After:** Each thread initializes COM independently using thread-local storage

### 3. Unicode Encoding Fixed
- **Before:** `'charmap' codec can't encode characters`
- **After:** UTF-8 encoding configured globally, all print statements wrapped in error handlers

## Running the App

### Normal Development (Recommended)
```powershell
npm run dev
```

**What this does:**
- Starts backend without auto-reload
- Starts frontend with Vite hot-reload
- Both run concurrently with colored output
- Clean shutdown with Ctrl+C (no prompts!)

**When to use:** 99% of the time - stable, fast, no issues

### With Hot-Reload (Special Cases Only)
```powershell
npm run dev:reload
```

**When to use:**
- Actively developing backend API code
- Need instant feedback on Python changes
- Outlook is closed (COM not active)

**Avoid when:**
- Outlook is running
- Doing frontend work (frontend already has hot-reload)
- Demoing or testing
- In production

## If You See "Port 8000 in use"

```powershell
# Kill Python processes and free the port
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Then start again
npm run dev
```

## If You See COM Errors

```powershell
# 1. Restart Outlook completely
# Close Outlook, then reopen it

# 2. Kill all Python processes
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# 3. Start fresh
npm run dev
```

## Verification

After starting with `npm run dev`, you should see:

```
[API] INFO:     Started server process [12345]
[API] INFO:     Waiting for application startup.
[API] INFO:     Application startup complete.
[API] INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
[WEB]   VITE v7.1.10  ready in 634 ms
[WEB]   ➜  Local:   http://localhost:3001/
```

**No:**
- ❌ "Terminate batch job" prompts
- ❌ "WatchFiles detected changes" spam
- ❌ "Reloading..." loops
- ❌ COM threading error messages
- ❌ Unicode encoding errors

## Shutting Down

Just press `Ctrl+C` once. It should shut down cleanly with no prompts.

## Production / Electron

For production or Electron app:

```json
"start:prod": "pwsh -NoProfile -Command \".venv/Scripts/python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1\""
```

**Critical:** Always use `--workers 1` for COM operations!

## Technical Details

See [`docs/technical/com-threading-fix.md`](../technical/com-threading-fix.md) for the complete technical explanation.

## Help

If you still have issues after following these steps, check:

1. Is Outlook running?
2. Are there zombie Python processes? (`Get-Process -Name python`)
3. Is port 8000 free? (`Get-NetTCPConnection -LocalPort 8000`)
4. Did you pull the latest changes? (should have the fixed `package.json`)
