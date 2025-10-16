# Diagnostic Electron Startup Script
# Tests the app and provides detailed diagnostics without blocking

Write-Host '╔══════════════════════════════════════════════════════════╗' -ForegroundColor Cyan
Write-Host '║     EMAIL HELPER - DIAGNOSTIC STARTUP & TEST SUITE      ║' -ForegroundColor Cyan
Write-Host '╚══════════════════════════════════════════════════════════╝' -ForegroundColor Cyan
Write-Host ''

# Step 1: Cleanup
Write-Host '🧹 Step 1: Cleaning up existing processes...' -ForegroundColor Yellow
Get-Process -Name electron -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Step 2: Check port 8000
Write-Host '🔍 Step 2: Checking port 8000...' -ForegroundColor Yellow
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000) {
    Write-Host '   ⚠️  Port 8000 in use, freeing...' -ForegroundColor Red
    $port8000 | Select-Object -ExpandProperty OwningProcess | ForEach-Object {
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
    Write-Host '   ✅ Port 8000 freed' -ForegroundColor Green
} else {
    Write-Host '   ✅ Port 8000 available' -ForegroundColor Green
}

# Step 3: Verify frontend build
Write-Host '🔍 Step 3: Verifying frontend build...' -ForegroundColor Yellow
$distPath = 'c:\Users\ameliapayne\email_helper\frontend\dist\index.html'
if (Test-Path $distPath) {
    $buildAge = (Get-Item $distPath).LastWriteTime
    Write-Host '   ✅ Frontend build exists (last built: '$buildAge')' -ForegroundColor Green
} else {
    Write-Host '   ❌ Frontend build missing!' -ForegroundColor Red
    Write-Host '   🔧 Building frontend...' -ForegroundColor Yellow
    Set-Location c:\Users\ameliapayne\email_helper\frontend
    npm run build
    Set-Location c:\Users\ameliapayne\email_helper\electron
}

# Step 4: Start app with timeout
Write-Host '🚀 Step 4: Starting Electron app (with 30s timeout)...' -ForegroundColor Green
Write-Host ''
Write-Host '   The app will start and you should test:' -ForegroundColor Cyan
Write-Host '   1. Can you see the Dashboard?' -ForegroundColor White
Write-Host '   2. Can you click the \"Process New Emails\" button?' -ForegroundColor White
Write-Host '   3. Can you click the \"View Pending Tasks\" button?' -ForegroundColor White
Write-Host '   4. Can you click the \"Generate Summary\" button?' -ForegroundColor White
Write-Host '   5. Do buttons show alerts/navigate correctly?' -ForegroundColor White
Write-Host ''
Write-Host '   📝 Check the console output below for any errors' -ForegroundColor Yellow
Write-Host '   📝 Press F12 in the app to open DevTools' -ForegroundColor Yellow
Write-Host ''
Write-Host '   ⏱️  App will auto-close in 30 seconds for testing...' -ForegroundColor Gray
Write-Host ''

Set-Location c:\Users\ameliapayne\email_helper\electron

# Start app in background job
$appJob = Start-Job -ScriptBlock {
    Set-Location c:\Users\ameliapayne\email_helper\electron
    npx electron . 2>&1
}

# Monitor for 30 seconds
$elapsed = 0
$maxTime = 30
while ($appJob.State -eq 'Running' -and $elapsed -lt $maxTime) {
    Start-Sleep -Seconds 5
    $elapsed += 5
    
    # Check if processes are running
    $electronRunning = Get-Process -Name electron -ErrorAction SilentlyContinue
    $pythonRunning = Get-Process -Name python -ErrorAction SilentlyContinue
    
    if ($electronRunning) {
        Write-Host '   ✅ Electron running ('$elapsed's elapsed)' -ForegroundColor Green
    }
    if ($pythonRunning) {
        Write-Host '   ✅ Backend running ('$elapsed's elapsed)' -ForegroundColor Green
    }
    
    # Get job output
    $output = Receive-Job -Job $appJob -Keep
    if ($output) {
        Write-Host $output
    }
}

Write-Host ''
Write-Host '⏹️  Stopping app...' -ForegroundColor Yellow
Stop-Job -Job $appJob -ErrorAction SilentlyContinue
Remove-Job -Job $appJob -ErrorAction SilentlyContinue

# Step 5: Cleanup
Write-Host '🧹 Step 5: Final cleanup...' -ForegroundColor Yellow
Get-Process -Name electron -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host ''
Write-Host '╔══════════════════════════════════════════════════════════╗' -ForegroundColor Cyan
Write-Host '║                    DIAGNOSTIC COMPLETE                   ║' -ForegroundColor Cyan
Write-Host '╚══════════════════════════════════════════════════════════╝' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Next steps:' -ForegroundColor Yellow
Write-Host '1. Review the output above for errors' -ForegroundColor White
Write-Host '2. To run the app normally: cd electron; & \".\start-clean.ps1\"' -ForegroundColor White
Write-Host '3. To run tests: cd frontend; & \".\run-electron-tests.ps1\"' -ForegroundColor White
Write-Host ''
