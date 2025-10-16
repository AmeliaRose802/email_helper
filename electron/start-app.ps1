# Email Helper Startup Script - Simple Working Version
Write-Host "🚀 Starting Email Helper..." -ForegroundColor Green

# Clean up
Get-Process -Name electron -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Free ports
@(8001, 5173) | ForEach-Object {
    Get-NetTCPConnection -LocalPort $_ -ErrorAction SilentlyContinue | ForEach-Object { 
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue 
    }
}

Start-Sleep 1

# Start API server
Write-Host "Starting API..." -ForegroundColor Cyan
Start-Process -FilePath "python" -ArgumentList "simple_api.py" -WorkingDirectory "C:\Users\ameliapayne\email_helper" -WindowStyle Hidden

# Start frontend server  
Write-Host "Starting frontend..." -ForegroundColor Cyan
Start-Process -FilePath "python" -ArgumentList "-m", "http.server", "5173" -WorkingDirectory "C:\Users\ameliapayne\email_helper" -WindowStyle Hidden

# Wait for services
Write-Host "Waiting for services..." -ForegroundColor Yellow
Start-Sleep 6

# Test services with retry
$maxRetries = 3
$apiReady = $false
$frontendReady = $false

for ($i = 1; $i -le $maxRetries; $i++) {
    try {
        $health = Invoke-RestMethod "http://localhost:8001/api/health" -TimeoutSec 3
        Write-Host "✅ API ready at http://localhost:8001" -ForegroundColor Green
        $apiReady = $true
        break
    } catch {
        Write-Host "⚠️ API attempt $i failed, retrying..." -ForegroundColor Yellow
        Start-Sleep 2
    }
}

for ($i = 1; $i -le $maxRetries; $i++) {
    try {
        Invoke-WebRequest "http://localhost:5173/test-simple.html" -TimeoutSec 3 | Out-Null
        Write-Host "✅ Frontend ready at http://localhost:5173" -ForegroundColor Green
        $frontendReady = $true
        break
    } catch {
        Write-Host "⚠️ Frontend attempt $i failed, retrying..." -ForegroundColor Yellow
        Start-Sleep 2
    }
}

if (-not $apiReady) {
    Write-Host "❌ API failed to start" -ForegroundColor Red
}

if (-not $frontendReady) {
    Write-Host "❌ Frontend failed to start" -ForegroundColor Red
}

Write-Host ""
Write-Host "📧 Email Helper Dashboard" -ForegroundColor Cyan
Write-Host "Opening in Electron..." -ForegroundColor Green
Write-Host ""

# Start electron directly
Set-Location $PSScriptRoot
npx electron main.js
