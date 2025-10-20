# Email Helper - Electron Desktop Application

This directory contains the Electron wrapper that turns the Email Helper React web application into a native desktop application.

## 🚀 Quick Start

### Start the Desktop App
```bash
# From electron directory
.\start-app.ps1
```

This will:
1. Start the Python FastAPI backend (port 8000)
2. Start the React frontend (port 3000) 
3. Launch the Electron desktop app

### Development Mode
```bash
.\start-clean.ps1
```

For a clean startup without backend/frontend (if they're already running).

## 📦 What's Integrated

The Electron app packages:
- ✅ React frontend with Dashboard, Email List, Task management
- ✅ Python FastAPI backend with real email processing
- ✅ Native desktop window with system integration
- ✅ Automatic backend/frontend startup

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  Electron Main Process (main.js)       │
│  - Window management                    │
│  - System integration                   │
└────────────┬────────────────────────────┘
             │
             ├─> Python Backend (localhost:8000)
             │   └─> Real email processing & AI
             │
             └─> React Frontend (localhost:3000)
                 └─> Dashboard, EmailList, TaskList
```

## ✅ Current Features

### Window Management
- Native desktop window with proper title bar
- System tray integration (when icon available)
- Standard keyboard shortcuts (Ctrl+Q, Ctrl+R, etc.)
- Development tools integration

### Backend Integration  
- Connects to real FastAPI backend (not mock)
- Real email processing through COM interface
- AI-powered email analysis and categorization
- Task management and persistence

### Frontend Integration
- Full React Dashboard with statistics
- Email List with filtering and search
- Task management with Kanban board
- Responsive design optimized for desktop

## 📋 Prerequisites

- Node.js 18+ installed
- Python 3.12+ with requirements.txt dependencies
- Microsoft Outlook installed (for COM interface)

## 🛠️ Setup

1. **Install Electron dependencies:**
   ```bash
   cd electron
   npm install
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install React dependencies:**
   ```bash
   cd frontend
   npm install
   ```

4. **Run the app:**
   ```bash
   cd electron
   .\start-app.ps1
   ```

## 🗂️ File Structure

```
electron/
├── main.js              # Electron main process (updated for React)
├── preload.js           # Security boundary preload script
├── package.json         # Electron config and build settings
├── start-app.ps1        # Complete startup script
├── start-clean.ps1      # Clean Electron-only startup
├── assets/              # App icons (optional, uses defaults)
└── README.md            # This file
```

## ⚙️ Configuration

### Environment
- Backend: http://localhost:8000 (FastAPI with real services)
- Frontend: http://localhost:3000 (React with Vite dev server)
- Electron loads React app directly

### Build Configuration
Edit `package.json` "build" section for:
- Application ID and metadata
- Target platforms (Windows, macOS, Linux)
- Icon paths and installer options

## 🔧 Development

### Running Components Separately

```bash
# Terminal 1: Backend API
python run_backend.py

# Terminal 2: React Frontend  
cd frontend && npm run dev

# Terminal 3: Electron (after services start)
cd electron && npx electron .
```

### Debugging

**Main Process (Electron):**
- Logs appear in PowerShell terminal
- Add console.log() in main.js

**Renderer (React):**
- F12 opens Chrome DevTools (in dev mode)
- React DevTools available
- Standard browser debugging

**Backend:**
- Logs in terminal/backend console
- Check runtime_data/logs/ for detailed logs

## 🚀 Building for Distribution

```bash
# Install dependencies
cd electron && npm install

# Build React frontend first
cd ../frontend && npm run build

# Build Electron app
cd ../electron && npm run build
```

Creates:
- Windows: EmailHelper Setup.exe + Portable version
- Cross-platform: Configure package.json for other platforms

## ✅ Current Status

- ✅ Electron app loads React frontend correctly
- ✅ Connects to real backend API (port 8000)
- ✅ Dashboard shows real statistics
- ✅ Email processing works through COM interface
- ✅ Task management integrated
- ✅ Startup scripts handle all services
- ⚠️ Using default icons (custom icons optional)
- ⚠️ Build process needs testing for distribution

## 🐛 Troubleshooting

**App won't start:**
- Check if ports 8000/3000 are free
- Ensure Python dependencies installed
- Verify Outlook is installed and configured

**Backend connection failed:**
- Check if run_backend.py starts successfully
- Verify port 8000 is not blocked by firewall
- Look for Python/import errors in console

**Frontend not loading:**
- Ensure `npm run dev` works in frontend directory
- Check if port 3000 is available
- Verify React build completed successfully

**COM errors:**
- Ensure Outlook is installed and configured
- Try opening Outlook manually first
- Check Windows Event Viewer for COM errors

This is a complete, working desktop application with full functionality!
