#!/usr/bin/env pwsh
# Email Helper Desktop App Launcher (PowerShell)
# Cross-platform launcher for the Electron desktop app

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Email Helper Desktop App Launcher" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Node.js
Write-Host "Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "Node.js version: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Node.js is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "Python version: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python from https://python.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Check Electron dependencies
if (-not (Test-Path "electron\node_modules")) {
    Write-Host "Installing Electron dependencies..." -ForegroundColor Yellow
    Push-Location electron
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install Electron dependencies" -ForegroundColor Red
        Pop-Location
        Read-Host "Press Enter to exit"
        exit 1
    }
    Pop-Location
    Write-Host ""
}

# Build frontend
Write-Host "Building frontend..." -ForegroundColor Yellow
Push-Location frontend

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install frontend dependencies" -ForegroundColor Red
        Pop-Location
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host ""
}

Write-Host "Building React app..." -ForegroundColor Yellow
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Frontend build failed" -ForegroundColor Red
    Pop-Location
    Read-Host "Press Enter to exit"
    exit 1
}

Pop-Location
Write-Host "Frontend built successfully!" -ForegroundColor Green
Write-Host ""

# Launch Electron
Write-Host "Launching Email Helper Desktop App..." -ForegroundColor Cyan
Push-Location electron
npm start
Pop-Location

Write-Host ""
Write-Host "Email Helper closed." -ForegroundColor Yellow
Read-Host "Press Enter to exit"
