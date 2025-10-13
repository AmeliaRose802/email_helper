# Email Helper - Quick Start Guide

## 🚀 One-Command Startup

You can now start both the frontend and backend with a single command:

```bash
npm start
```

This will start:
- **Frontend (React)**: http://localhost:3000/
- **Backend (API)**: http://localhost:8001/

## 📋 Available Commands

### Main Commands
- `npm start` - Start both frontend and backend (recommended)
- `npm run start:full` - Start with full backend (FastAPI with auth)
- `npm run dev` - Development mode with restart capabilities
- `npm run setup` - Install all dependencies

### Individual Services
- `npm run frontend` - Start only React frontend
- `npm run simple-api` - Start only simple API backend  
- `npm run backend` - Start only full FastAPI backend
- `npm run gui` - Start Python GUI application

### Utilities
- `npm run build` - Build frontend for production
- `npm run test` - Run frontend tests
- `npm run lint` - Lint frontend code
- `npm run health` - Check if services are running

## ⚡ Quick Start (Windows)

You can also use the batch file for Windows:

```cmd
start.bat
```

Or for Linux/Mac:

```bash
./start.sh
```

## 🔧 Configuration

### API Endpoints
The frontend automatically proxies API calls to the backend:
- Frontend: `http://localhost:3000`
- API calls: Automatically routed to `http://localhost:8001`

### Port Configuration
- Frontend: Port 3000 (or 3001 if 3000 is busy)
- Simple API: Port 8001
- Full Backend: Port 8000

## 🏗️ Architecture

```
Email Helper Application
├── npm start
│   ├── Frontend (React + Vite) → Port 3000
│   └── Backend (Simple API) → Port 8001
├── Automatic Proxy Configuration
├── Hot Reload for Development
└── Graceful Error Handling
```

## 🛠️ Development Features

- **Hot Reload**: Both frontend and backend restart on file changes
- **Concurrent Execution**: Both services run simultaneously
- **Error Handling**: If one service fails, both stop (fail-safe)
- **Color Coding**: Different colors for API and WEB logs
- **Automatic Dependencies**: Checks and installs missing packages

## 📱 Access Points

1. **Web Application**: http://localhost:3000/
2. **API Documentation**: http://localhost:8001/docs (when using simple-api)
3. **Health Check**: http://localhost:8001/api/health
4. **GUI Application**: `npm run gui` (Python desktop app)

## 🚨 Troubleshooting

### Common Issues

1. **Port Already in Use**: Frontend will automatically try port 3001
2. **Node.js Version Warning**: Vite shows warning but still works
3. **Python Dependencies**: Run `npm run setup` to install everything

### Reset Everything
```bash
# Stop all processes
taskkill /F /IM python.exe
taskkill /F /IM node.exe

# Clean and reinstall
npm run setup
npm start
```

## ✅ Ready to Go!

Once you run `npm start`, you'll see:
- ✅ Frontend running on http://localhost:3000/
- ✅ Backend API running on http://localhost:8001/  
- ✅ Hot reload enabled for development
- ✅ Proxy configured for seamless API calls

Your Email Helper application is now ready for development and testing! 🎊