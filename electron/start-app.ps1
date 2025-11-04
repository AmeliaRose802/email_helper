# Email Helper Startup Script - Production Ready Version
Write-Host "🚀 Starting Email Helper..." -ForegroundColor Green

# Function to cleanup on exit
function Cleanup {
    Write-Host ""
    Write-Host "🛑 Shutting down Email Helper services..." -ForegroundColor Yellow
    
    # Stop Electron
    Get-Process -Name electron -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    
    # Stop Python backend
    Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    
    # Stop Node/frontend (be careful not to kill VS Code)
    Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object {
        $_.MainWindowTitle -notlike "*Visual Studio Code*"
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Host "✓ Shutdown complete" -ForegroundColor Green
}

# Clean up any existing processes
Write-Host "🧹 Cleaning up existing processes..." -ForegroundColor Yellow
Get-Process -Name electron -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Free ports
@(8000, 3000, 5173) | ForEach-Object {
    Get-NetTCPConnection -LocalPort $_ -ErrorAction SilentlyContinue | ForEach-Object { 
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue 
    }
}

Start-Sleep 2

# Verify project structure
$ProjectRoot = "C:\Users\ameliapayne\email_helper"
if (-not (Test-Path $ProjectRoot)) {
    Write-Host "❌ Project directory not found: $ProjectRoot" -ForegroundColor Red
    exit 1
}

# Start backend API server
Write-Host "🔧 Starting Backend API..." -ForegroundColor Cyan
$BackendJob = Start-Process -FilePath "python" -ArgumentList "run_backend.py" -WorkingDirectory $ProjectRoot -WindowStyle Hidden -PassThru

# Start React frontend  
Write-Host "⚛️ Starting React Frontend..." -ForegroundColor Cyan
$FrontendJob = Start-Process -FilePath "npx" -ArgumentList "vite", "--port", "3000" -WorkingDirectory "$ProjectRoot\frontend" -WindowStyle Hidden -PassThru

# Wait for services to initialize
Write-Host "⏳ Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep 8

# Test backend with retry logic
$MaxRetries = 5
$BackendReady = $false

Write-Host "🔍 Testing Backend API..." -ForegroundColor Yellow
for ($i = 1; $i -le $MaxRetries; $i++) {
    try {
        $Health = Invoke-RestMethod "http://localhost:8000/health" -TimeoutSec 5
        if ($Health.status -eq "healthy") {
            Write-Host "✅ Backend API ready - Status: $($Health.status)" -ForegroundColor Green
            Write-Host "   Database: $($Health.database)" -ForegroundColor Gray
            Write-Host "   Version: $($Health.version)" -ForegroundColor Gray
            $BackendReady = $true
            break
        }
    } catch {
        Write-Host "⚠️ Backend API attempt $i/$MaxRetries failed, retrying..." -ForegroundColor Yellow
        Start-Sleep 3
    }
}

# Test frontend with retry logic
$FrontendReady = $false

Write-Host "🔍 Testing React Frontend..." -ForegroundColor Yellow
for ($i = 1; $i -le $MaxRetries; $i++) {
    try {
        # Test port connectivity instead of HTTP response code
        $PortTest = Test-NetConnection -ComputerName localhost -Port 3001 -InformationLevel Quiet -WarningAction SilentlyContinue
        if ($PortTest) {
            # Port is open, now try HTTP request
            try {
                $Response = Invoke-WebRequest "http://localhost:3001" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
                Write-Host "✅ React Frontend ready - Status: $($Response.StatusCode)" -ForegroundColor Green
                $FrontendReady = $true
                break
            } catch {
                # Even if HTTP request fails, if port is open and listening, frontend is likely ready
                if ($_.Exception.Message -match "404") {
                    # 404 means server is responding but route not found - Vite is running
                    Write-Host "✅ React Frontend ready - Vite dev server is running" -ForegroundColor Green
                    $FrontendReady = $true
                    break
                }
            }
        }
        Write-Host "⚠️ React Frontend attempt $i/$MaxRetries - port not ready, retrying..." -ForegroundColor Yellow
        Start-Sleep 3
    } catch {
        Write-Host "⚠️ React Frontend attempt $i/$MaxRetries failed: $($_.Exception.Message)" -ForegroundColor Yellow
        Start-Sleep 3
    }
}

# Check service status
if (-not $BackendReady) {
    Write-Host "❌ Backend API failed to start properly" -ForegroundColor Red
    Write-Host "   Check logs for errors and ensure dependencies are installed" -ForegroundColor Yellow
}

if (-not $FrontendReady) {
    Write-Host "❌ React Frontend failed to start properly" -ForegroundColor Red
    Write-Host "   Check if Node.js is installed and dependencies are ready" -ForegroundColor Yellow
}

if ($BackendReady -and $FrontendReady) {
    Write-Host ""
    Write-Host "🎉 All services ready!" -ForegroundColor Green
    Write-Host "📧 Email Helper Dashboard" -ForegroundColor Cyan
    Write-Host "   Backend API: http://localhost:8000" -ForegroundColor Gray
    Write-Host "   Frontend UI: http://localhost:3001" -ForegroundColor Gray
    Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🖥️ Launching Electron App..." -ForegroundColor Green
    
    # Start Electron in a new window (non-blocking)
    Set-Location $PSScriptRoot
    
    try {
        $ElectronProcess = Start-Process -FilePath "npx" -ArgumentList "electron", "main.js" -WorkingDirectory $PSScriptRoot -PassThru
        
        Write-Host "✅ Electron app launched (PID: $($ElectronProcess.Id))" -ForegroundColor Green
        Write-Host ""
        Write-Host "📝 Services are running in the background" -ForegroundColor Cyan
        Write-Host "   Press Ctrl+C to shut down all services cleanly" -ForegroundColor Gray
        Write-Host ""
        
        # Wait for Electron to exit
        $ElectronProcess.WaitForExit()
        
        Write-Host ""
        Write-Host "👋 Electron app closed" -ForegroundColor Yellow
        Cleanup
        
    } catch {
        Write-Host "⚠ Error running Electron: $($_.Exception.Message)" -ForegroundColor Yellow
        Cleanup
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "❌ Services failed to start properly. Please check the configuration." -ForegroundColor Red
    Write-Host ""
    Write-Host "📋 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "   1. Verify Python dependencies: pip install -r requirements.txt" -ForegroundColor Gray
    Write-Host "   2. Verify Node.js dependencies: cd frontend && npm install" -ForegroundColor Gray
    Write-Host "   3. Check port availability (8000, 3000)" -ForegroundColor Gray
    Write-Host "   4. Review error logs above" -ForegroundColor Gray
    
    # Clean up failed processes
    if ($BackendJob -and -not $BackendJob.HasExited) {
        Stop-Process -Id $BackendJob.Id -Force -ErrorAction SilentlyContinue
    }
    if ($FrontendJob -and -not $FrontendJob.HasExited) {
        Stop-Process -Id $FrontendJob.Id -Force -ErrorAction SilentlyContinue
    }
    
    Cleanup
    exit 1
}
