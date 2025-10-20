# Clean startup script for Email Helper Electron app
Write-Host "🧹 Cleaning up processes..." -ForegroundColor Yellow

# Kill processes using Stop-Process (NOT taskkill)
Get-Process -Name electron -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Free ports 8000 and 3000
$ports = @(8000, 3000)
foreach ($port in $ports) {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn) {
        Write-Host "🔓 Freeing port $port..." -ForegroundColor Yellow
        $conn | Select-Object -ExpandProperty OwningProcess | ForEach-Object {
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        }
    }
}

Start-Sleep -Seconds 2
Write-Host "✅ Cleanup complete" -ForegroundColor Green
Write-Host ""
Write-Host "�� Starting Electron app..." -ForegroundColor Cyan
Write-Host ""

# Start Electron
Set-Location $PSScriptRoot
& npx electron .
