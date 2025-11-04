/**
 * Electron Main Process
 * 
 * This file handles:
 * - Window creation and management
 * - Backend Python process lifecycle
 * - System tray integration
 * - IPC communication between renderer and main process
 */

const { app, BrowserWindow, Menu, Tray, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
// Always enable dev mode when running from source (not packaged)
const isDev = !app.isPackaged;

let mainWindow = null;
let backendProcess = null;
let tray = null;

// Backend server configuration
const BACKEND_PORT = 8000;
const BACKEND_HOST = 'localhost';

/**
 * Start the Python FastAPI backend server
 */
function startBackend() {
  console.log('Starting Python backend server...');
  
  const pythonExecutable = process.platform === 'win32' ? 'python' : 'python3';
  const backendScript = path.join(app.getAppPath(), '..', 'run_backend.py');
  
  backendProcess = spawn(pythonExecutable, [backendScript], {
    cwd: path.join(app.getAppPath(), '..'),
    env: {
      ...process.env,
      PORT: BACKEND_PORT.toString(),
      DEBUG: isDev ? 'true' : 'false',
      PYTHONIOENCODING: 'utf-8',  // Force UTF-8 encoding
    },
  });

  backendProcess.stdout.on('data', (data) => {
    const output = data.toString().trim();
    // Remove emoji characters that cause encoding issues
    const cleanOutput = output.replace(/[\u{1F600}-\u{1F9FF}]/gu, '');
    console.log(`[Backend] ${cleanOutput}`);
  });

  backendProcess.stderr.on('data', (data) => {
    const output = data.toString().trim();
    const cleanOutput = output.replace(/[\u{1F600}-\u{1F9FF}]/gu, '');
    console.error(`[Backend Error] ${cleanOutput}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
    backendProcess = null;
  });

  backendProcess.on('error', (err) => {
    console.error('Failed to start backend process:', err);
  });

  // Give backend time to start with timeout
  return new Promise((resolve) => {
    const timeout = setTimeout(() => {
      console.log('Backend startup timeout reached, continuing anyway...');
      resolve();
    }, 5000); // 5 second timeout
    
    setTimeout(() => {
      clearTimeout(timeout);
      resolve();
    }, 3000);
  });
}

/**
 * Stop the Python backend server
 */
function stopBackend() {
  if (backendProcess) {
    console.log('Stopping Python backend server...');
    
    // Send SIGTERM for graceful shutdown
    try {
      if (process.platform === 'win32') {
        // Windows: try graceful shutdown first
        backendProcess.kill('SIGTERM');
        
        // Give it 2 seconds to shut down gracefully
        setTimeout(() => {
          if (backendProcess && !backendProcess.killed) {
            console.log('Backend did not stop gracefully, forcing shutdown...');
            backendProcess.kill('SIGKILL');
          }
        }, 2000);
      } else {
        // Unix: SIGTERM should work
        backendProcess.kill('SIGTERM');
      }
    } catch (err) {
      console.error('Error stopping backend:', err);
      // Force kill if graceful shutdown fails
      try {
        backendProcess.kill('SIGKILL');
      } catch (e) {
        // Already dead
      }
    }
    
    backendProcess = null;
  }
}

/**
 * Create the main application window
 */
async function createWindow() {
  // Don't start backend - it's started externally by the PowerShell script

  // Set app icon
  const iconPath = path.join(__dirname, 'assets', 'icon.png');
  
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    title: 'Email Helper Dashboard',
    icon: iconPath, // Set window icon
    center: true, // Center the window on screen
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      zoomFactor: 1.0,
      enableRemoteModule: false,
      devTools: isDev, // Only enable dev tools in development
      webSecurity: true, // Enable web security
      allowRunningInsecureContent: false // Disable insecure content
    },
    titleBarStyle: 'default', // Ensure proper title bar for Windows
    frame: true, // Use standard frame for proper click handling
    show: false, // Hide until ready
    backgroundColor: '#ffffff', // White background while loading
  });

  // Force zoom level to 100%
  mainWindow.webContents.setZoomFactor(1.0);

  // Register event listeners BEFORE loading URL (critical!)
  mainWindow.webContents.on('did-finish-load', () => {
    console.log('✅ Page finished loading, showing window immediately');
    mainWindow.show();
    mainWindow.focus();
    
    // Open DevTools for debugging
    if (isDev) {
      console.log('🔧 Opening DevTools for debugging...');
      mainWindow.webContents.openDevTools({ mode: 'detach' });
    }
  });

  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('❌ Failed to load:', errorCode, errorDescription);
    // Show window anyway so user can see the error
    if (mainWindow && !mainWindow.isVisible()) {
      console.log('Showing window despite load failure');
      mainWindow.show();
    }
  });

  mainWindow.webContents.on('console-message', (event, level, message) => {
    const levelName = ['', 'INFO', 'WARNING', 'ERROR'][level] || 'LOG';
    console.log(`[Renderer ${levelName}] ${message}`);
  });

  // Absolute safety fallback: Show window after 5 seconds no matter what
  setTimeout(() => {
    if (mainWindow && !mainWindow.isVisible()) {
      console.log('⏰ SAFETY TIMEOUT: Forcing window to show after 5 seconds');
      mainWindow.show();
      mainWindow.focus();
      if (isDev) {
        mainWindow.webContents.openDevTools({ mode: 'detach' });
      }
    }
  }, 5000);

  // Load the React frontend - simple approach, no complex error handling
  const reactDevUrl = 'http://localhost:3001';
  console.log('Loading React frontend from:', reactDevUrl);
  
  mainWindow.loadURL(reactDevUrl).catch(error => {
    console.error('Load URL failed:', error);
    mainWindow.show(); // Show window even on error
  });

  // Handle window close
  mainWindow.on('close', (event) => {
    if (app.quitting) {
      mainWindow = null;
    } else {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Create application menu
  createMenu();
}

/**
 * Create application menu
 */
function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Refresh',
          accelerator: 'CmdOrCtrl+R',
          click: () => {
            if (mainWindow) mainWindow.reload();
          },
        },
        { type: 'separator' },
        {
          label: 'Quit',
          accelerator: 'CmdOrCtrl+Q',
          click: () => {
            app.quitting = true;
            app.quit();
          },
        },
      ],
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
      ],
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About Email Helper',
          click: async () => {
            const { shell } = require('electron');
            await shell.openExternal('https://github.com/AmeliaRose802/email_helper');
          },
        },
      ],
    },
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

/**
 * Create system tray icon
 */
function createTray() {
  const iconPath = path.join(__dirname, 'assets', 'icon.png');
  
  // Check if icon exists, if not skip tray creation
  const fs = require('fs');
  if (!fs.existsSync(iconPath)) {
    console.log('⚠️  Tray icon not found, skipping tray creation');
    console.log('   Add icon.png to electron/assets/ for system tray support');
    return;
  }
  
  tray = new Tray(iconPath);

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show Email Helper',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
        }
      },
    },
    {
      label: 'Quit',
      click: () => {
        app.quitting = true;
        app.quit();
      },
    },
  ]);

  tray.setToolTip('Email Helper');
  tray.setContextMenu(contextMenu);

  tray.on('click', () => {
    if (mainWindow) {
      mainWindow.show();
    }
  });
}

// App lifecycle events
app.whenReady().then(() => {
  createWindow();
  createTray();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    } else if (mainWindow) {
      mainWindow.show();
    }
  });
});

app.on('window-all-closed', () => {
  // On macOS, keep app running until explicit quit
  if (process.platform !== 'darwin') {
    app.quitting = true;
    app.quit();
  }
});

app.on('before-quit', () => {
  app.quitting = true;
});

app.on('will-quit', () => {
  stopBackend();
});

// IPC Handlers
ipcMain.handle('get-backend-url', () => {
  return `http://${BACKEND_HOST}:${BACKEND_PORT}`;
});

ipcMain.handle('restart-backend', async () => {
  stopBackend();
  await startBackend();
  return true;
});

// Auto-quit safety timeout to prevent infinite hanging
setTimeout(() => {
  console.log('⏰ Safety timeout reached, auto-quitting to prevent blocking...');
  app.quit();
}, 300000); // 5 minutes max runtime

// Error handling
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
  // Don't let uncaught exceptions block the app
  setTimeout(() => process.exit(1), 1000);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled rejection at:', promise, 'reason:', reason);
  // Don't let unhandled rejections block the app
});
