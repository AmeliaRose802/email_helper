# Non-blocking test runner for Electron app
Write-Host '🧪 Starting Electron App Tests...' -ForegroundColor Cyan
Write-Host ''

# Kill existing processes
Write-Host '🧹 Cleaning up processes...' -ForegroundColor Yellow
Get-Process -Name electron,python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Free port 8000
$conn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($conn) {
    Write-Host '🔓 Freeing port 8000...' -ForegroundColor Yellow
    $conn | Select-Object -ExpandProperty OwningProcess | ForEach-Object {
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
}

Write-Host ''
Write-Host '🚀 Running Playwright tests...' -ForegroundColor Green
Write-Host ''

# Run tests with timeout
Set-Location c:\Users\ameliapayne\email_helper\frontend
$job = Start-Job -ScriptBlock {
    Set-Location c:\Users\ameliapayne\email_helper\frontend
    npm run test:electron 2>&1
}

# Wait for job with timeout (2 minutes)
$timeout = 120
$elapsed = 0
while ($job.State -eq 'Running' -and $elapsed -lt $timeout) {
    Start-Sleep -Seconds 5
    $elapsed += 5
    Write-Host '⏱️  Test running... ('$elapsed's elapsed)' -ForegroundColor Gray
}

if ($job.State -eq 'Running') {
    Write-Host '⚠️  Tests timed out after '$timeout' seconds' -ForegroundColor Red
    Stop-Job -Job $job
    Remove-Job -Job $job
} else {
    $output = Receive-Job -Job $job
    Remove-Job -Job $job
    Write-Host $output
}

Write-Host ''
Write-Host '🧹 Final cleanup...' -ForegroundColor Yellow
Get-Process -Name electron,python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host ''
Write-Host '✅ Test run complete' -ForegroundColor Green
