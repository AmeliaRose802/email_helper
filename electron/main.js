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
const isDev = process.env.NODE_ENV === 'development';

let mainWindow = null;
let backendProcess = null;
let tray = null;

// Backend server configuration
const BACKEND_PORT = 8001;
const BACKEND_HOST = 'localhost';

/**
 * Start the Python FastAPI backend server
 */
function startBackend() {
  console.log('Starting Python backend server...');
  
  const pythonExecutable = process.platform === 'win32' ? 'python' : 'python3';
  const backendScript = path.join(app.getAppPath(), '..', 'simple_api.py');
  
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
    backendProcess.kill();
    backendProcess = null;
  }
}

/**
 * Create the main application window
 */
async function createWindow() {
  // Don't start backend - it's started externally by the PowerShell script

  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    title: 'Email Helper Dashboard',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      zoomFactor: 1.0,
      enableRemoteModule: false,
      devTools: true, // Enable dev tools for debugging
      webSecurity: false, // Allow cross-origin requests for development
      allowRunningInsecureContent: true
    },
    titleBarStyle: 'default', // Ensure proper title bar for Windows
    frame: true, // Use standard frame for proper click handling
    show: false,
  });

  // Force zoom level to 100%
  mainWindow.webContents.setZoomFactor(1.0);

  // Load the frontend with timeout
  const frontendUrl = 'http://localhost:5173/test-simple.html';
  console.log('Loading frontend from:', frontendUrl);
  
  const loadWithTimeout = (url, timeoutMs = 10000) => {
    return Promise.race([
      mainWindow.loadURL(url),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Load timeout')), timeoutMs)
      )
    ]);
  };
  
  try {
    await loadWithTimeout(frontendUrl, 8000);
    console.log('Frontend loaded successfully');
  } catch (error) {
    console.error('Failed to load frontend from', frontendUrl, error);
    // Fallback: try to load test page
    const fallbackUrl = 'http://localhost:5173/test-simple.html';
    console.log('Trying fallback:', fallbackUrl);
    try {
      await loadWithTimeout(fallbackUrl, 5000);
    } catch (fallbackError) {
      console.error('Fallback also failed, loading local file:', fallbackError);
      // Last resort: load a local file
      const localFile = path.join(__dirname, '..', 'test-dashboard.html');
      try {
        await mainWindow.loadFile(localFile);
      } catch (localError) {
        console.error('Even local file failed:', localError);
      }
    }
  }
  
  // Enable dev tools for debugging button issues
  mainWindow.webContents.openDevTools();
  
  // Inject button debugging script with timeout protection
  setTimeout(() => {
    mainWindow.webContents.executeJavaScript(`
      console.log('🔧 Injecting button debug helpers...');
      
      // Wait for React to load with timeout
      const debugTimeout = setTimeout(() => {
        console.log('Debug injection timeout, trying anyway...');
        debugButtons();
      }, 5000);
      
      function debugButtons() {
        try {
          const buttons = document.querySelectorAll('button, .action-button');
          console.log('Found buttons:', buttons.length);
          
          buttons.forEach((btn, index) => {
            console.log(\`Button \${index + 1}:\`, {
              text: btn.textContent?.trim(),
              disabled: btn.disabled,
              style: {
                pointerEvents: window.getComputedStyle(btn).pointerEvents,
                zIndex: window.getComputedStyle(btn).zIndex,
                position: window.getComputedStyle(btn).position
              }
            });
            
            // Force enable clicking
            btn.style.pointerEvents = 'auto';
            btn.style.zIndex = '9999';
            btn.style.position = 'relative';
            
            // Add visual debug on hover
            btn.addEventListener('mouseenter', () => {
              btn.style.border = '2px solid red';
              console.log('🐭 Mouse over:', btn.textContent?.trim());
            });
            
            btn.addEventListener('mouseleave', () => {
              btn.style.border = '';
            });
            
            // Log all click events
            btn.addEventListener('click', (e) => {
              console.log('🎯 BUTTON CLICKED!', btn.textContent?.trim());
              btn.style.background = 'lime';
              setTimeout(() => btn.style.background = '', 2000);
            }, true);
          });
          
          clearTimeout(debugTimeout);
        } catch (error) {
          console.error('Error in button debug:', error);
        }
      }
      
      setTimeout(debugButtons, 2000);
    `).catch(err => {
      console.error('Failed to inject debug script:', err);
    });
  }, 1000);

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    console.log('Window shown');
  });

  // Log any loading errors
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('Failed to load:', errorCode, errorDescription);
  });

  mainWindow.webContents.on('console-message', (event, level, message) => {
    // Always log console messages for debugging
    const levelName = ['', 'INFO', 'WARNING', 'ERROR'][level] || 'LOG';
    console.log(`[Renderer ${levelName}] ${message}`);
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
