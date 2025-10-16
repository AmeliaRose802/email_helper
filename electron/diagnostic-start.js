const { app, BrowserWindow } = require("electron");
const path = require("path");

let mainWindow;

function createWindow() {
  console.log("🔧 Creating diagnostic Electron window...");
  
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, "preload.js")
    },
    titleBarStyle: "default",
    show: false
  });

  const frontendUrl = "http://localhost:5173";
  console.log(`🌐 Loading frontend from: ${frontendUrl}`);
  
  mainWindow.loadURL(frontendUrl).then(() => {
    console.log("✅ Frontend loaded successfully");
    mainWindow.show();
    mainWindow.webContents.openDevTools();
    
    setTimeout(() => {
      console.log("🧪 Testing button functionality...");
      
      mainWindow.webContents.executeJavaScript(`
        console.log("🔍 Checking for buttons...");
        const buttons = document.querySelectorAll("button");
        console.log("Found buttons:", buttons.length);
        
        buttons.forEach((btn, index) => {
          console.log(\`Button \${index + 1}:\`, {
            text: btn.textContent.trim(),
            disabled: btn.disabled,
            style: {
              pointerEvents: window.getComputedStyle(btn).pointerEvents,
              zIndex: window.getComputedStyle(btn).zIndex
            }
          });
          
          btn.addEventListener("click", (e) => {
            console.log("🎯 Button clicked!", btn.textContent.trim());
            btn.style.background = "green";
            setTimeout(() => btn.style.background = "", 1000);
          });
        });
        
        if (buttons.length > 0) {
          console.log("🤖 Simulating click on first button...");
          buttons[0].click();
        }
        
        return "Diagnostic complete";
      `);
    }, 3000);
    
  }).catch(err => {
    console.error("❌ Failed to load frontend:", err);
  });
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => process.platform !== "darwin" && app.quit());
setTimeout(() => app.quit(), 30000);
