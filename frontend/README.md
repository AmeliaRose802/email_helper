# Email Helper - React Web Application

React web application frontend for the Email Helper system with complete backend API integration.

## 🚀 Quick Start - Localhost Development

Get the frontend running locally in 3 steps:

### Prerequisites
- **Node.js 18+** and npm ([download](https://nodejs.org/))
- **Backend server** running on http://localhost:8000 (see [Backend README](../backend/README.md))

### Setup
```bash
# 1. Install dependencies
npm install

# 2. Configure environment
cp .env.local.example .env.local

# 3. Start development server
npm run dev
```

The frontend will be accessible at **http://localhost:3000** or **http://localhost:5173**

> **📖 Detailed Setup:** See [Frontend Localhost Setup](./LOCALHOST_SETUP.md) for comprehensive instructions and troubleshooting.

### Verify Setup
- ✅ Backend running at http://localhost:8000 ([verify health](http://localhost:8000/health))
- ✅ `.env.local` file exists with `VITE_API_BASE_URL=http://localhost:8000`
- ✅ Browser console shows no CORS errors
- ✅ Network tab shows API calls succeeding

## 🚀 Features

- **Modern React Stack**: React 19 with TypeScript, Vite, and ES modules
- **State Management**: Redux Toolkit with RTK Query for efficient API calls and caching
- **Routing**: React Router v6 with protected routes and TypeScript support
- **Backend Integration**: Complete integration with T1-T4 APIs:
  - **T1**: Authentication API (`/auth/*`) with JWT token management
  - **T2**: Email API (`/api/emails/*`) with Microsoft Graph integration
  - **T3**: AI Processing API (`/api/ai/*`) with classification and analysis
  - **T4**: Task Management API (`/api/tasks/*`) with full CRUD operations
- **Development Tools**: ESLint, Prettier, Vitest testing framework
- **Responsive Design**: Mobile-friendly UI with modern styling

## 📋 Prerequisites

- Node.js 18+ and npm
- Backend server running on `http://localhost:8000` (T1-T4 APIs)

## 🛠️ Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Access application at http://localhost:3000
```

## 🧪 Testing

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test:ui

# Run tests once
npm run test:run

# Run integration tests (requires backend)
npm run test -- --testPathPattern=integration
```

## 🔧 Development

```bash
# Lint code
npm run lint
npm run lint:fix

# Format code
npm run format

# Build for production
npm run build

# Preview production build
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── Layout.tsx      # Main app layout with navigation
│   │   └── ProtectedRoute.tsx # Authentication guard
│   ├── pages/              # Page components
│   │   ├── Dashboard.tsx   # Main dashboard with stats
│   │   ├── EmailList.tsx   # Email list interface (T7 ready)
│   │   ├── TaskList.tsx    # Task management interface (T8 ready)
│   │   ├── Login.tsx       # Authentication page (T6 ready)
│   │   └── Settings.tsx    # Application settings
│   ├── router/             # React Router configuration
│   │   └── AppRouter.tsx   # Main router setup
│   ├── store/              # Redux store and slices
│   │   ├── store.ts        # Store configuration
│   │   └── authSlice.ts    # Authentication state
│   ├── services/           # API services (RTK Query)
│   │   ├── api.ts          # Base API configuration
│   │   ├── authApi.ts      # T1: Authentication API
│   │   ├── emailApi.ts     # T2: Email API
│   │   ├── aiApi.ts        # T3: AI Processing API
│   │   └── taskApi.ts      # T4: Task Management API
│   ├── types/              # TypeScript type definitions
│   │   ├── auth.ts         # Authentication types
│   │   ├── email.ts        # Email types
│   │   ├── ai.ts           # AI processing types
│   │   ├── task.ts         # Task management types
│   │   └── api.ts          # Common API types
│   ├── hooks/              # Custom React hooks
│   │   └── redux.ts        # Typed Redux hooks
│   ├── utils/              # Utility functions
│   ├── styles/             # CSS stylesheets
│   │   └── index.css       # Main styles
│   └── test/               # Test files
│       ├── App.test.tsx    # App component tests
│       ├── routes.test.tsx # Router tests
│       ├── api.test.ts     # API configuration tests
│       └── integration.test.ts # Backend integration tests
├── public/                 # Static assets
└── __tests__/             # Additional test files
```

## 🔌 API Integration

### Backend Dependencies (✅ Complete)

All backend APIs are implemented and ready:

- **T1 - Authentication**: JWT-based auth with registration, login, token refresh
- **T2 - Email Service**: Microsoft Graph API integration with email operations
- **T3 - AI Processing**: Email classification and analysis using existing AIProcessor
- **T4 - Task Management**: Full CRUD operations with filtering and statistics

### API Configuration

The application uses a centralized API configuration system:

**Configuration File**: `src/config/api.ts`
- Environment-based API URL configuration
- Centralized endpoint definitions
- Debug logging utilities
- Backend health checking

**Proxy Configuration**: The application automatically proxies API calls through Vite's dev server to avoid CORS issues:
- `/auth/*` → `http://localhost:8000/auth/*`
- `/api/*` → `http://localhost:8000/api/*`
- `/health` → `http://localhost:8000/health`

**Direct API Calls**: Services use RTK Query with the base URL set to `/` (proxy handles routing)

The proxy target is configurable via `VITE_API_BASE_URL` in `.env.local`, allowing easy switching between:
- Local backend: `http://localhost:8000` (default)
- Docker backend: `http://localhost:8002`
- Remote backend: `https://api.yourdomain.com`

### Authentication Flow

1. User logs in via `/auth/login`
2. JWT tokens stored in localStorage
3. Automatic token refresh on API calls
4. Protected routes require authentication

## 🎨 UI Components

### Current Pages

- **Dashboard**: Overview with email and task statistics
- **Email List**: Paginated email interface with filtering (T7 foundation)
- **Task List**: Task management with CRUD operations (T8 foundation)
- **Login**: Authentication interface (T6 foundation)
- **Settings**: Application configuration and system status

### Navigation

- Responsive sidebar navigation
- Protected route enforcement
- API status indicators
- User profile integration

## 🧪 Testing Strategy

### Unit Tests
- Component rendering and behavior
- Redux store configuration
- API service setup
- Route protection logic

### Integration Tests
- Backend API connectivity
- Authentication flow
- Data fetching and caching
- Error handling

### Development Tests
```bash
# Run all tests including integration
npm run test

# Run only unit tests
npm run test -- --testPathIgnorePatterns=integration

# Run only integration tests (requires backend)
npm run test -- --testPathPattern=integration
```

## 🚧 Future Development

### Ready for Implementation

- **T6**: Complete authentication flow with user management
- **T7**: Full email list interface with advanced features
- **T8**: Comprehensive task management interface

### Development Guidelines

1. **API First**: All APIs are ready - focus on UI/UX
2. **Type Safety**: Maintain strict TypeScript usage
3. **Testing**: Add tests for new components and features
4. **Responsive**: Ensure mobile compatibility
5. **Performance**: Utilize RTK Query caching effectively

## 🐛 Troubleshooting

### Quick Fixes

**Backend Connection Errors**
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check backend logs for errors
cd ../backend && python main.py

# Ensure CORS is configured correctly in backend .env
# Backend should include: CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
```

**Port Conflicts**
```bash
# Change port in vite.config.ts or run with different port
npm run dev -- --port 3001
```

**Environment Variables Not Loading**
```bash
# Verify .env.local exists in frontend directory
ls -la .env.local

# Check variable names start with VITE_
cat .env.local | grep VITE_

# Restart dev server after changes (Ctrl+C, then npm run dev)
```

### Common Issues

**Backend Connection Errors**
```bash
# 1. Verify backend is running
curl http://localhost:8000/health

# 2. Check backend logs for errors
cd ../backend && python main.py

# 3. Ensure CORS is configured correctly
# Backend should allow http://localhost:3000
```

**Port Conflicts**
```bash
# If port 3000 is already in use, change it in vite.config.ts
# or run with a different port:
npm run dev -- --port 3001
```

**Environment Variables Not Loading**
```bash
# 1. Verify .env.local exists in frontend directory
ls -la .env.local

# 2. Check variable names start with VITE_
cat .env.local | grep VITE_

# 3. Restart dev server after changes
# Press Ctrl+C to stop, then:
npm run dev

# 4. Verify variables are loaded (in browser console):
console.log(import.meta.env.VITE_API_BASE_URL)
```

**Proxy Errors / API 404s**
```bash
# Check vite.config.ts proxy configuration
# Ensure it matches your backend port

# Test direct backend access:
curl http://localhost:8000/api/emails

# If backend works but proxy doesn't:
# 1. Restart dev server
# 2. Clear browser cache (Ctrl+Shift+R)
# 3. Check browser network tab for actual request URL
```

**Build Errors**
```bash
# Clear cache and reinstall dependencies
rm -rf node_modules package-lock.json
npm install
npm run build
```

**Type Errors**
```bash
# Run type checking
npx tsc --noEmit
```

> **📖 More Help:** See the [Frontend Localhost Setup](./LOCALHOST_SETUP.md) and [Troubleshooting Guide](../docs/TROUBLESHOOTING.md) for detailed solutions.

### Localhost Development Checklist

When starting development, ensure:
- ✅ Backend is running on http://localhost:8000
- ✅ `.env.local` exists with correct `VITE_API_BASE_URL`
- ✅ Frontend dev server started with `npm run dev`
- ✅ Browser shows frontend at http://localhost:3000
- ✅ Browser console shows no CORS errors
- ✅ Network tab shows API calls going to backend

### Debug Mode

Enable debug logging in `.env.local`:
```env
VITE_DEBUG_LOGGING=true
```

This will log:
- API configuration on startup
- Request headers for each API call
- Backend health check status

Check browser console (F12) for debug output.

## 📝 Environment Variables & Localhost Configuration

### Quick Setup for Localhost Development

1. **Copy the example environment file:**
   ```bash
   cp .env.local.example .env.local
   ```

2. **Configure for your local backend:**
   ```env
   # .env.local - Basic configuration for localhost
   VITE_API_BASE_URL=http://localhost:8000
   VITE_API_TIMEOUT=30000
   VITE_APP_TITLE=Email Helper
   VITE_APP_ENV=development
   VITE_DEBUG_LOGGING=true
   VITE_LOCALHOST_MODE=true
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   Frontend will be accessible at http://localhost:3000

### Backend Connection

The frontend automatically connects to your local backend server through Vite's proxy configuration:

- **Backend API**: http://localhost:8000
- **Frontend Dev Server**: http://localhost:3000

The proxy routes the following paths to the backend:
- `/auth/*` → Authentication endpoints
- `/api/*` → API endpoints (emails, tasks, AI processing)
- `/health` → Health check endpoint

### Environment Variable Reference

All frontend environment variables must be prefixed with `VITE_` to be accessible in the browser:

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend API base URL |
| `VITE_API_TIMEOUT` | `30000` | API request timeout (ms) |
| `VITE_APP_TITLE` | `Email Helper` | Application title |
| `VITE_APP_ENV` | `development` | Environment name |
| `VITE_DEBUG_LOGGING` | `true` | Enable console debug logs |
| `VITE_LOCALHOST_MODE` | `true` | Enable localhost mode |

**Important:** Changes to `.env.local` require restarting the dev server (`npm run dev`)

### CORS Configuration

CORS is handled by the backend. Ensure your backend configuration includes the frontend URL:

```python
# backend/core/config.py
cors_origins = ["http://localhost:3000", "http://localhost:5173"]
```

The frontend uses two possible ports:
- Port 3000: Configured in `vite.config.ts`
- Port 5173: Vite's default port (fallback)

### Verifying Connection

Check that the backend is running and accessible:

```bash
# Test backend health endpoint
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "email-helper-api",
#   "version": "1.0.0",
#   "database": "healthy",
#   "debug": true
# }
```

### Configuration Files

The API configuration is centralized in:
- `src/config/api.ts` - API configuration and endpoint definitions
- `vite.config.ts` - Vite dev server and proxy configuration
- `.env.local` - Environment variables (not tracked in git)

Example usage in components:

```typescript
import { apiConfig, apiEndpoints, buildApiUrl } from '@/config/api';

// Access configuration
console.log(apiConfig.baseURL); // http://localhost:8000

// Build API URL
const healthUrl = buildApiUrl(apiEndpoints.health);

// Check backend availability
import { checkBackendHealth } from '@/config/api';
const isOnline = await checkBackendHealth();
```

## 🔗 Related Documentation

- [Backend API Documentation](../backend/README.md)
- [Project Architecture](../docs/)
- [Testing Guide](./src/test/README.md)

---

**Status**: ✅ **T5 Complete** - React web application foundation ready for T6-T8 implementation with full backend integration.
