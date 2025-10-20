# Pre-flight check for Email Helper Desktop App
# Verifies all requirements are met before starting

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Email Helper - Pre-Flight Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# Check 1: Outlook running
Write-Host "[1/4] Checking if Outlook is running..." -ForegroundColor Yellow
$outlookProcess = Get-Process -Name OUTLOOK -ErrorAction SilentlyContinue
if ($outlookProcess) {
    Write-Host "  [OK] Outlook is running" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Outlook is NOT running" -ForegroundColor Red
    Write-Host "  Please start Microsoft Outlook before launching the app" -ForegroundColor Yellow
    $allGood = $false
}
Write-Host ""

# Check 2: Python available
Write-Host "[2/4] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  [OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Python not found" -ForegroundColor Red
    $allGood = $false
}
Write-Host ""

# Check 3: Node.js available
Write-Host "[3/4] Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  [OK] Node.js $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Node.js not found" -ForegroundColor Red
    $allGood = $false
}
Write-Host ""

# Check 4: Port 8000 available
Write-Host "[4/4] Checking if port 8000 is free..." -ForegroundColor Yellow
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000) {
    Write-Host "  [WARNING] Port 8000 is in use" -ForegroundColor Yellow
    Write-Host "  Will attempt to free it on startup" -ForegroundColor Yellow
} else {
    Write-Host "  [OK] Port 8000 is available" -ForegroundColor Green
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "[SUCCESS] All checks passed!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "You can now start the app with:" -ForegroundColor White
    Write-Host "  .\restart-app.ps1" -ForegroundColor Cyan
} else {
    Write-Host "[FAILED] Some checks failed" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Please fix the issues above before starting the app" -ForegroundColor Yellow
}
Write-Host ""
