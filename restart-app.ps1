# Clean restart script for Email Helper Desktop App
# Kills all processes cleanly and restarts the app

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Email Helper - Clean Restart" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Kill existing processes without prompts
Write-Host "Stopping existing processes..." -ForegroundColor Yellow

# Kill Electron processes
Get-Process -Name electron -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Kill Python backend processes
Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*email_helper*" -or $_.CommandLine -like "*backend*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

# Free port 8000 if occupied
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000) {
    Write-Host "Freeing port 8000..." -ForegroundColor Yellow
    $port8000 | Select-Object -ExpandProperty OwningProcess | ForEach-Object {
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
    }
}

# Wait for cleanup
Write-Host "Waiting for cleanup..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

Write-Host "Cleanup complete!" -ForegroundColor Green
Write-Host ""

# Start the app
Write-Host "Starting Email Helper..." -ForegroundColor Cyan
Write-Host ""

Set-Location electron
& ".\start-app.ps1"
