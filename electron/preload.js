/**
 * Electron Preload Script
 * 
 * This script runs in the renderer process before web content loads.
 * It safely exposes select Node.js and Electron APIs to the renderer.
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to renderer process
contextBridge.exposeInMainWorld('electron', {
  // Get backend API URL
  getBackendUrl: () => ipcRenderer.invoke('get-backend-url'),
  
  // Restart backend server
  restartBackend: () => ipcRenderer.invoke('restart-backend'),
  
  // Platform info
  platform: process.platform,
  
  // Check if running in Electron
  isElectron: true,
});

console.log('Preload script loaded');
