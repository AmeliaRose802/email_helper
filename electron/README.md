# Email Helper - Electron Desktop Application

This directory contains the Electron wrapper that turns the Email Helper web application into a native desktop application.

## 🚀 Quick Start

### Development Mode
```bash
# From project root
npm run electron:dev
```

### Production Build
```bash
# Build the desktop application
npm run electron:build

# The installer will be in electron/dist/
```

## 📦 What Gets Built

The Electron app packages:
- ✅ React frontend (built from `frontend/`)
- ✅ Python FastAPI backend (from `backend/` and `src/`)
- ✅ All email processing services
- ✅ Embedded Python runtime (when using PyInstaller)

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  Electron Main Process (main.js)       │
│  - Window management                    │
│  - Python backend lifecycle             │
│  - System tray integration              │
└────────────┬────────────────────────────┘
             │
             ├─> Python Backend (localhost:8000)
             │   └─> COM → Outlook
             │
             └─> Electron Renderer (BrowserWindow)
                 └─> React Frontend
```

## 🎯 Features

### Window Management
- Native desktop window with system integration
- Minimize to system tray
- Remember window size and position
- Standard keyboard shortcuts (Ctrl+Q, Ctrl+R, etc.)

### Backend Integration
- Automatically starts Python backend on launch
- Manages backend lifecycle
- Graceful shutdown handling
- Backend restart capability

### Development
- Hot reload support in dev mode
- Chrome DevTools integration
- Console logging for debugging

## 📋 Prerequisites

### For Development
- Node.js 18+ installed
- Python 3.12+ installed
- Microsoft Outlook installed (for COM interface)
- All dependencies from `requirements.txt`

### For Building
- All development prerequisites
- Windows: NSIS installer (optional, for installer creation)
- macOS: Xcode command line tools
- Linux: Standard build tools

## 🛠️ Setup

1. **Install Electron dependencies:**
   ```bash
   cd electron
   npm install
   ```

2. **Build the frontend:**
   ```bash
   cd ../frontend
   npm install
   npm run build
   ```

3. **Run in development mode:**
   ```bash
   cd ../electron
   npm run dev
   ```

## 📦 Building for Distribution

### Windows
```bash
# From electron directory
npm run build

# Or from project root
npm run electron:build
```

This creates:
- `EmailHelper Setup 1.0.0.exe` - Installer
- `EmailHelper-Portable-1.0.0.exe` - Portable version (no installation)

### macOS
```bash
npm run build:mac
```

Creates:
- `.dmg` - macOS disk image
- `.zip` - Archived application

### Linux
```bash
npm run build:linux
```

Creates:
- `.AppImage` - Universal Linux binary
- `.deb` - Debian package

## 🗂️ File Structure

```
electron/
├── main.js              # Electron main process
├── preload.js           # Preload script (security boundary)
├── package.json         # Electron dependencies and build config
├── assets/              # Application icons and resources
│   ├── icon.png         # Application icon (Windows/Linux)
│   ├── icon.ico         # Windows icon
│   └── icon.icns        # macOS icon
└── dist/                # Build output (created by electron-builder)
```

## ⚙️ Configuration

### Environment Variables

The Electron app sets these environment variables for the backend:

- `PORT=8000` - Backend server port
- `DEBUG=true` - Enable debug mode (dev only)
- `REQUIRE_AUTHENTICATION=false` - Disable auth for localhost
- `USE_COM_BACKEND=true` - Use COM interface to Outlook
- `EMAIL_PROVIDER=com` - Specify COM provider

### Build Configuration

Edit `electron/package.json` under the `"build"` section to customize:

- Application ID and name
- Target platforms and formats
- Icon paths
- Installer options
- File inclusions/exclusions

## 🔧 Development Tips

### Running with Frontend Dev Server

For fastest development with hot reload:

```bash
# Terminal 1: Start Vite dev server
cd frontend
npm run dev

# Terminal 2: Start Electron in dev mode
cd electron
npm run dev
```

The Electron app will load from `http://localhost:3000` in dev mode.

### Debugging

**Main Process:**
- Console output appears in the terminal
- Add `console.log()` statements in `main.js`

**Renderer Process:**
- DevTools open automatically in dev mode
- Use browser console (F12)
- React DevTools available

**Backend:**
- Backend logs appear in main process console with `[Backend]` prefix
- Check `runtime_data/logs/` for detailed logs

### Common Issues

**Backend won't start:**
- Ensure Python is in PATH
- Check `requirements.txt` dependencies are installed
- Verify Outlook is installed and configured

**Window doesn't show:**
- Check console for errors
- Ensure frontend built successfully (`frontend/dist/` exists)
- Try `npm run dev` for better error messages

**COM errors:**
- Ensure Outlook is installed
- Try running Outlook manually first
- Check Windows Event Viewer for COM errors

## 🚀 Distribution

### Before Distributing

1. **Test thoroughly:**
   ```bash
   npm run build
   # Test the installer on a clean machine
   ```

2. **Update version:**
   - Edit `electron/package.json` version
   - Update `CHANGELOG.md`

3. **Create icons:**
   - Windows: 256x256 PNG → convert to `.ico`
   - macOS: Create `.icns` from 1024x1024 PNG
   - Linux: 512x512 PNG

### Installer Options

**NSIS Installer (Windows):**
- Traditional installer with Start Menu shortcuts
- Allows custom installation directory
- Desktop shortcut creation option
- Uninstaller included

**Portable (Windows):**
- Single executable, no installation
- Perfect for USB drives
- Settings stored in app directory

## 📝 Scripts Reference

From project root:
- `npm run electron:dev` - Run Electron in development mode
- `npm run electron:build` - Build for current platform
- `npm run electron:install` - Install Electron dependencies

From `electron/` directory:
- `npm start` - Run Electron (production mode)
- `npm run dev` - Run Electron (development mode)
- `npm run build` - Build Windows installer
- `npm run build:mac` - Build macOS app
- `npm run build:linux` - Build Linux packages

## 🎨 Customization

### Application Icon

Replace icons in `electron/assets/`:
- `icon.png` - Base icon (512x512 or 1024x1024)
- `icon.ico` - Windows icon
- `icon.icns` - macOS icon

Use tools like:
- [electron-icon-builder](https://www.npmjs.com/package/electron-icon-builder)
- [iconverticons.com](https://iconverticons.com/online/)

### Application Menu

Edit `createMenu()` function in `main.js` to customize:
- Menu items
- Keyboard shortcuts
- Menu actions

### System Tray

Edit `createTray()` function in `main.js` to customize:
- Tray icon
- Tray menu
- Click behavior

## 📄 License

MIT License - See LICENSE file in project root

## 🤝 Contributing

See main project README for contribution guidelines.
