# Email Helper Desktop App - Setup Guide

This guide will help you set up and run Email Helper as a desktop application using Electron.

## 🚀 Quick Start

### Step 1: Install Electron Dependencies
```powershell
cd electron
npm install
```

### Step 2: Build the Frontend
```powershell
cd ..\frontend
npm run build
```

### Step 3: Run the Desktop App
```powershell
# From project root
npm run electron:dev

# Or from electron directory
cd electron
npm run dev
```

## 📦 What You Get

✅ **Native Desktop Application**
- Runs as a Windows application (taskbar icon, Alt+Tab, etc.)
- System tray integration (minimize to tray)
- Native window controls and menus
- Keyboard shortcuts (Ctrl+Q to quit, Ctrl+R to refresh)

✅ **Bundled Backend**
- Python backend starts automatically
- No manual server management needed
- Graceful shutdown handling
- Backend restarts if needed

✅ **No Authentication Required**
- Configured for localhost mode
- Direct access to features
- No login screen

✅ **COM Integration**
- Direct connection to Outlook via COM interface
- No cloud services required
- Works offline

## 🎯 Development Workflow

### Option 1: Full Rebuild (Slower but Safe)
```powershell
# Build frontend, then run Electron
npm run electron:dev
```

### Option 2: Development Mode (Faster)
```powershell
# Terminal 1: Keep frontend dev server running
cd frontend
npm run dev

# Terminal 2: Run Electron in dev mode
cd electron
npm run dev
```

In dev mode, Electron loads from the Vite dev server, giving you hot reload!

## 📋 Troubleshooting

### Electron Won't Start

**"Cannot find module 'electron'"**
```powershell
cd electron
npm install
```

**"Backend failed to start"**
- Ensure Python is installed and in PATH
- Install Python dependencies: `pip install -r requirements.txt`
- Check that Outlook is installed

**"Port already in use"**
- Kill any existing backend processes
- Check ports: `netstat -ano | findstr ":8000"`
- Kill process: `taskkill /PID <process_id> /F`

### Frontend Not Loading

**"Failed to load resource"**
- Build the frontend: `cd frontend && npm run build`
- Check that `frontend/dist/` directory exists
- Try cleaning and rebuilding: `rm -rf dist && npm run build`

**"White screen on startup"**
- Open DevTools (Ctrl+Shift+I in Electron window)
- Check console for errors
- Verify backend is running (check main terminal output)

### Backend Issues

**"Cannot connect to Outlook"**
- Ensure Outlook is installed
- Open Outlook manually to verify it works
- Try restarting Outlook
- Check Windows Event Viewer for COM errors

**"Module not found" errors**
- Install all Python dependencies: `pip install -r requirements.txt`
- Ensure `src/` is in Python path
- Check that `backend/` directory structure is intact

## 🔨 Building for Distribution

### Build the Installer

```powershell
# From project root
npm run electron:build
```

This creates:
- **Installer**: `electron/dist/Email Helper Setup 1.0.0.exe`
- **Portable**: `electron/dist/EmailHelper-Portable-1.0.0.exe`

### Test the Build

1. Navigate to `electron/dist/`
2. Run the installer or portable version
3. Test all features thoroughly
4. Check on a clean machine without development tools

### Distribution Checklist

- [ ] Update version in `electron/package.json`
- [ ] Create application icons (see `electron/assets/README.md`)
- [ ] Test on clean Windows machine
- [ ] Update CHANGELOG.md
- [ ] Create GitHub release
- [ ] Provide clear installation instructions

## 🎨 Customization

### Change Application Name
Edit `electron/package.json`:
```json
{
  "name": "your-app-name",
  "productName": "Your App Name",
  "build": {
    "appId": "com.yourcompany.yourapp"
  }
}
```

### Change Window Size
Edit `electron/main.js`:
```javascript
mainWindow = new BrowserWindow({
  width: 1600,  // Your preferred width
  height: 1000, // Your preferred height
  // ...
});
```

### Add Custom Icons
1. Create/obtain icons (see `electron/assets/README.md`)
2. Place in `electron/assets/`
3. Update paths in `electron/package.json` build section
4. Rebuild

### Modify Menu
Edit the `createMenu()` function in `electron/main.js`

## 📊 Architecture

```
┌─────────────────────────────────────┐
│   Electron Main Process             │
│   (Node.js + Electron APIs)         │
│                                     │
│   • Spawns Python backend          │
│   • Creates app window             │
│   • Manages lifecycle              │
└──────┬──────────────────────────────┘
       │
       ├─> Python Backend (Port 8000)
       │   └─> COM Interface → Outlook
       │
       └─> Renderer Process (Chromium)
           └─> React App (Your UI)
```

## 💡 Tips & Best Practices

### Development
- Use `npm run electron:dev` for quick iteration
- Keep DevTools open for debugging
- Check both Electron console and browser console for errors
- Test with real Outlook data regularly

### Performance
- Build frontend in production mode before distribution
- Minimize bundled files (check `electron/package.json` files section)
- Use code splitting in React app
- Consider lazy loading for heavy components

### Security
- Keep Electron updated
- Use `contextIsolation: true` (already configured)
- Don't expose Node.js APIs unnecessarily
- Validate all IPC communication

### Distribution
- Test on multiple Windows versions
- Provide clear system requirements
- Include uninstaller
- Sign your application (recommended for production)

## 🔗 Useful Links

- [Electron Documentation](https://www.electronjs.org/docs)
- [electron-builder Documentation](https://www.electron.build/)
- [Vite Documentation](https://vitejs.dev/)
- [Project GitHub](https://github.com/AmeliaRose802/email_helper)

## ❓ FAQ

**Q: Do users need Python installed?**
A: For development, yes. For distribution, you can bundle Python using PyInstaller or similar tools.

**Q: Does this work on Mac/Linux?**
A: The Electron app can run on Mac/Linux, but the COM interface requires Windows + Outlook.

**Q: Can I use this without Outlook?**
A: Not with the COM backend. You'd need to switch to the Graph API backend (cloud-based).

**Q: How big is the installer?**
A: Approximately 150-250MB depending on bundled dependencies and Python runtime.

**Q: Can I auto-update the app?**
A: Yes, you can integrate electron-updater. See electron-builder documentation.

## 📝 Next Steps

After getting the app running:

1. **Test thoroughly** with your actual Outlook data
2. **Customize** the appearance and behavior
3. **Create icons** for professional look
4. **Build installer** for easy distribution
5. **Document** any special setup steps for your users

Happy coding! 🚀
