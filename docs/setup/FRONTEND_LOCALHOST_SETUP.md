# Frontend Localhost Setup Guide

This guide walks you through setting up the Email Helper frontend for local development.

## Prerequisites

- Node.js 18+ installed
- npm (comes with Node.js)
- Backend server available (or running locally)

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Copy the example environment file:

```bash
cp .env.local.example .env.local
```

Or create `.env.local` with these settings:

```env
# Backend API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# Application Settings
VITE_APP_TITLE=Email Helper
VITE_APP_ENV=development

# Development Features
VITE_DEBUG_LOGGING=true
VITE_LOCALHOST_MODE=true
```

### 3. Start Development Server

```bash
npm run dev
```

The frontend will be available at: **http://localhost:3000**

## Connecting to the Backend

### Default Configuration

By default, the frontend connects to:
- **Backend API**: http://localhost:8000

The proxy configuration in `vite.config.ts` automatically routes:
- `/auth/*` → `http://localhost:8000/auth/*`
- `/api/*` → `http://localhost:8000/api/*`
- `/health` → `http://localhost:8000/health`

### Changing Backend URL

To connect to a different backend (e.g., Docker or remote server), update `.env.local`:

```env
# For Docker backend
VITE_API_BASE_URL=http://localhost:8002

# For remote backend
VITE_API_BASE_URL=https://api.yourdomain.com
```

**Important:** Restart the dev server after changing environment variables!

## Verifying the Setup

### 1. Check Backend Health

Before starting the frontend, verify the backend is running:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "email-helper-api",
  "version": "1.0.0",
  "database": "healthy",
  "debug": true
}
```

### 2. Check Frontend Server

After starting the frontend:

```bash
curl http://localhost:3000
```

You should see HTML content with the Vite dev server scripts.

### 3. Check Browser Console

Open your browser to http://localhost:3000 and press F12 to open DevTools.

Look for these debug messages in the console:
```
[API Config] Configuration loaded: {
  baseURL: 'http://localhost:8000',
  timeout: 30000,
  localhostMode: true,
  debugLogging: true
}
```

### 4. Test API Connectivity

In the browser console, run:

```javascript
fetch('/health')
  .then(r => r.json())
  .then(console.log)
```

This should return the backend health check response.

## Common Issues

### Issue: Backend Connection Refused

**Problem:** Frontend can't connect to backend

**Solution:**
1. Verify backend is running:
   ```bash
   cd backend
   python main.py
   ```

2. Check backend port matches `VITE_API_BASE_URL` in `.env.local`

3. Verify no firewall is blocking port 8000

### Issue: Environment Variables Not Loading

**Problem:** Config changes don't take effect

**Solution:**
1. Ensure file is named `.env.local` (not `.env.local.txt`)
2. Check file is in `frontend/` directory (not root)
3. Verify variables start with `VITE_`
4. **Restart dev server** after changes (Ctrl+C then `npm run dev`)

### Issue: CORS Errors

**Problem:** Browser shows CORS errors in console

**Solution:**
1. Check backend CORS configuration includes frontend URL:
   ```python
   # backend/core/config.py
   cors_origins = ["http://localhost:3000", "http://localhost:5173"]
   ```

2. Restart backend after configuration changes

3. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)

### Issue: Port Already in Use

**Problem:** Port 3000 is already in use

**Solution:**
Either change the port in `vite.config.ts`:
```typescript
server: {
  port: 3001,  // Change to available port
  // ...
}
```

Or run with a different port:
```bash
npm run dev -- --port 3001
```

### Issue: Module Not Found

**Problem:** Import errors or "Cannot find module" errors

**Solution:**
1. Delete and reinstall dependencies:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

2. Verify TypeScript path aliases in `tsconfig.app.json`

## Development Workflow

### Recommended Terminal Setup

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Making Changes

The frontend uses hot module replacement (HMR):
- Save any file in `src/` to see changes immediately
- No need to refresh browser for most changes
- Server automatically compiles on save

### Running Tests

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test:ui

# Run specific test file
npm run test:run src/test/config.test.ts
```

### Linting and Formatting

```bash
# Check code style
npm run lint

# Fix code style issues
npm run lint:fix

# Format code with Prettier
npm run format
```

### Building for Production

```bash
# Build optimized production bundle
npm run build

# Preview production build locally
npm run preview
```

## Configuration Files Reference

### `.env.local`
Environment variables for local development. Not tracked in git.

### `vite.config.ts`
Vite configuration including:
- Dev server settings
- Proxy configuration
- Path aliases
- Build settings

### `src/config/api.ts`
Centralized API configuration:
- Loads environment variables
- Defines API endpoints
- Provides utility functions
- Debug logging

### `tsconfig.app.json`
TypeScript configuration including path aliases.

## Accessing the Application

Once running:
- **Frontend UI**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **Backend Redoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Debug Mode

Enable comprehensive debug logging in `.env.local`:

```env
VITE_DEBUG_LOGGING=true
```

This logs:
- API configuration on startup
- Request headers for each API call
- Backend connectivity status
- Redux state changes (if Redux DevTools installed)

View logs in the browser console (F12 → Console tab).

## Browser DevTools

### Recommended Extensions

- **React Developer Tools**: Inspect React components
- **Redux DevTools**: Monitor Redux state changes
- **Network Tab**: View API requests and responses

### Inspecting API Calls

1. Open DevTools (F12)
2. Go to Network tab
3. Filter by XHR/Fetch
4. Look for requests to `/api/*` and `/auth/*`
5. Check request/response headers and payloads

## Next Steps

After successful setup:
1. Explore the codebase in `src/`
2. Review API services in `src/services/`
3. Check component structure in `src/components/`
4. Read the main [README.md](./README.md) for architecture details

## Getting Help

If you encounter issues not covered here:
1. Check the main README troubleshooting section
2. Review backend logs for errors
3. Check browser console for JavaScript errors
4. Verify all prerequisites are met
5. Try the setup on a clean environment

## Summary Checklist

Before you can successfully develop:
- [x] Node.js 18+ installed
- [x] Dependencies installed (`npm install`)
- [x] `.env.local` created with correct backend URL
- [x] Backend running on http://localhost:8000
- [x] Frontend dev server running (`npm run dev`)
- [x] Browser shows UI at http://localhost:3000
- [x] No CORS errors in console
- [x] API calls work (check Network tab)

Once all items are checked, you're ready to develop! 🚀
