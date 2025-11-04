# COM Threading Fix - Complete Solution

## Problem Summary

When running FastAPI with Uvicorn in development mode, multiple critical issues occurred:

1. **"Terminate batch job (Y/N)?" prompts** - Uvicorn's auto-reload blocking the terminal
2. **COM threading errors** - `"The application called an interface that was marshalled for a different thread"`
3. **Unicode encoding errors** - `'charmap' codec can't encode characters`
4. **Infinite reload loops** - WatchFiles triggering on files that shouldn't cause reloads

## Root Causes

### 1. Auto-Reload Issues
- Uvicorn's WatchFiles detects file changes and attempts to reload
- Spawns new worker processes via multiprocessing
- Can prompt for confirmation with "Terminate batch job (Y/N)?"
- Watches too many directories (runtime_data, frontend, logs, etc.)

### 2. COM Threading Violations
- COM objects are **apartment-threaded** - they MUST be created and accessed from the same thread
- FastAPI/Uvicorn uses thread pools for request handling
- When COM objects created in main thread are accessed from worker threads → crash
- Each thread needs its own COM initialization (`CoInitialize`)

### 3. Windows Console Encoding
- Windows console defaults to 'cp1252' (charmap) encoding
- Unicode characters in email content/errors → `UnicodeEncodeError`
- `print()` statements fail when outputting non-ASCII characters

## Complete Solution

### 1. Disable Auto-Reload by Default

**File: `package.json`**

```json
"scripts": {
  "backend": "pwsh -NoProfile -Command \".venv/Scripts/python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 --reload-exclude '*.log' --reload-exclude 'runtime_data/*' --reload-exclude '.beads/*' --reload-exclude 'frontend/*'\"",
  "backend:noreload": "pwsh -NoProfile -Command \".venv/Scripts/python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000\"",
  "dev": "concurrently -k -s first \"npm run backend:noreload\" \"npm run frontend\" --names \"API,WEB\" --prefix-colors \"blue,green\" --kill-others-on-fail",
  "dev:reload": "concurrently -k -s first \"npm run backend\" \"npm run frontend\" --names \"API,WEB\" --prefix-colors \"blue,green\" --kill-others-on-fail"
}
```

**Key changes:**
- `-NoProfile` flag prevents PowerShell profile from interfering
- `--reload-exclude` patterns prevent unnecessary reloads
- `--kill-others-on-fail` ensures clean shutdown on errors
- Default `dev` uses no-reload mode (use `dev:reload` if you need hot-reload)

### 2. Fix COM Threading

**Created: `backend/core/com_threading.py`**

Provides thread-safe COM utilities:

```python
import threading
import pythoncom

_thread_local = threading.local()

def ensure_com_initialized() -> None:
    """Ensure COM is initialized for the current thread."""
    if not hasattr(_thread_local, 'com_initialized'):
        pythoncom.CoInitialize()
        _thread_local.com_initialized = True
```

**Updated: `backend/services/outlook/adapters/outlook_email_adapter.py`**

All methods that access COM objects now:
1. Call `ensure_com_initialized()` at the start
2. Wrap print statements in try/except to handle Unicode errors

```python
def get_emails(self, folder_name: str = "Inbox", count: int = 50, offset: int = 0):
    if not self.connected:
        raise RuntimeError("Not connected to Outlook. Call connect() first.")
    
    # Initialize COM on this thread
    ensure_com_initialized()
    
    try:
        emails = self.outlook_manager.get_recent_emails(...)
        # ... rest of method
    except Exception as e:
        try:
            print(f"Error: {e}")
        except UnicodeEncodeError:
            pass  # Ignore encoding errors in error messages
```

### 3. Fix Unicode Encoding

**Updated: `backend/main.py`**

Configure UTF-8 encoding at application startup:

```python
import sys

# Configure console encoding FIRST to prevent Unicode errors
try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass  # Ignore if reconfigure not available
```

**Strategy:**
- Set UTF-8 encoding for stdout/stderr globally
- Use `errors='replace'` to replace unencodable characters with '?'
- Wrap all print statements in try/except blocks as fallback

### 4. Safe Shutdown

**Updated: `backend/main.py` lifespan handler**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Email Helper API...")
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down...")
    try:
        # Check method exists before calling
        if hasattr(db_manager, 'close_all_connections'):
            db_manager.close_all_connections()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
```

**Why:** Prevents `AttributeError` if the method doesn't exist.

## Usage

### Normal Development (No Hot-Reload)
```powershell
npm run dev
# or
npm start
```

**Advantages:**
- ✅ No "Terminate batch job" prompts
- ✅ No COM threading errors
- ✅ No infinite reload loops
- ✅ Faster startup
- ✅ More stable

**Disadvantage:**
- ❌ Must manually restart after code changes

### Development with Hot-Reload (Use Sparingly)
```powershell
npm run dev:reload
```

**Use when:**
- Actively developing and need instant feedback
- Working on backend API code only
- Have Outlook closed (COM errors less likely)

**Avoid when:**
- Outlook is running and COM operations are active
- Working on frontend (frontend has its own hot-reload)
- In production or demo scenarios

## Testing the Fix

### 1. Start the app
```powershell
npm run dev
```

### 2. Verify no prompts appear
- Should see clean startup with no "Terminate batch job" prompts
- Both API and WEB services start cleanly

### 3. Test COM operations
```powershell
# In another terminal
curl http://localhost:8000/api/emails?limit=50000
```

Should return emails without:
- Threading errors
- Unicode encoding errors
- Marshalling errors

### 4. Test shutdown
Press `Ctrl+C` once - should shut down cleanly with no hanging.

## When COM Errors Still Occur

If you still see COM threading errors:

1. **Restart Outlook** - COM state can get corrupted
2. **Check for multiple Python processes** - Kill all Python.exe processes
3. **Verify COM initialization** - Add logging to `ensure_com_initialized()`
4. **Use production mode** - Disable reload entirely

## Production Deployment

For production (Electron app or server deployment):

```json
"scripts": {
  "start:prod": "pwsh -NoProfile -Command \".venv/Scripts/python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1\""
}
```

**CRITICAL:** Use `--workers 1` for COM operations. Multiple workers = multiple processes = COM threading hell.

## Why Not Switch Languages?

Python + COM + FastAPI is absolutely viable when configured correctly:

✅ **Proper threading** - COM initialization per-thread
✅ **Single worker** - One process for COM state consistency  
✅ **No auto-reload in production** - Disable file watching
✅ **Unicode handling** - Configure encoding properly

Languages like C# or Rust would have COM threading challenges too - the solution is understanding COM's threading model, not changing languages.

## References

- [Microsoft COM Threading Models](https://learn.microsoft.com/en-us/windows/win32/com/processes--threads--and-apartments)
- [Python COM Documentation](https://github.com/mhammond/pywin32)
- [Uvicorn Workers Configuration](https://www.uvicorn.org/deployment/)
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)

## Summary

This fix addresses COM threading by:
1. **Per-thread COM initialization** - Each thread initializes COM independently
2. **No auto-reload by default** - Prevents multiprocessing complexity  
3. **UTF-8 console encoding** - Handles Unicode in error messages
4. **Safe print statements** - Catch and ignore encoding errors
5. **Clean shutdown** - Graceful resource cleanup

The app should now run stably without prompts, threading errors, or encoding crashes.
