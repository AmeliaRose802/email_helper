# Email Helper - React Web Application

React web application frontend for the Email Helper system with complete backend API integration.

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

The application automatically proxies API calls:
- `/auth/*` → `http://localhost:8000/auth/*`
- `/api/*` → `http://localhost:8000/api/*`

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

### Common Issues

**Backend Connection Errors**
```bash
# Ensure backend is running
cd ../backend && python main.py
# Backend should be accessible at http://localhost:8000/health
```

**Build Errors**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

**Type Errors**
```bash
# Run type checking
npx tsc --noEmit
```

## 📝 Environment Variables

Create `.env.local` for local development:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=Email Helper
```

## 🔗 Related Documentation

- [Backend API Documentation](../backend/README.md)
- [Project Architecture](../docs/)
- [Testing Guide](./src/test/README.md)

---

**Status**: ✅ **T5 Complete** - React web application foundation ready for T6-T8 implementation with full backend integration.
