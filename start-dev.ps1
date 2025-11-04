#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Clean development server startup with proper shutdown handling.

.DESCRIPTION
    Starts the Email Helper development environment with proper signal handling
    for clean shutdown. Kills any existing processes on ports 8000 and 3001,
    then starts the backend and frontend servers with coordinated shutdown.

.EXAMPLE
    .\start-dev.ps1
    Starts the development servers. Press Ctrl+C to shut down cleanly.
#>

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Email Helper Development Environment" -ForegroundColor Cyan
Write-Host ""

# Function to kill processes on a specific port
function Stop-ProcessOnPort {
    param([int]$Port)
    
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($connections) {
        Write-Host "🔧 Freeing port $Port..." -ForegroundColor Yellow
        $connections | ForEach-Object {
            $processId = $_.OwningProcess
            try {
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                Write-Host "   ✓ Stopped process $processId on port $Port" -ForegroundColor Green
            } catch {
                Write-Host "   ⚠ Could not stop process $processId" -ForegroundColor Yellow
            }
        }
        Start-Sleep -Seconds 1
    }
}

# Function to cleanup on exit
function Cleanup {
    Write-Host ""
    Write-Host "🛑 Shutting down development servers..." -ForegroundColor Yellow
    
    # Kill any Python processes (backend)
    Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    
    # Kill any Node processes (frontend) - be careful not to kill VS Code
    Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object {
        $_.MainWindowTitle -notlike "*Visual Studio Code*"
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Host "✓ Cleanup complete" -ForegroundColor Green
}

# Register cleanup on exit
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Cleanup }

# Cleanup any existing processes
Write-Host "🔧 Cleaning up existing processes..." -ForegroundColor Yellow
Stop-ProcessOnPort -Port 8000  # Backend
Stop-ProcessOnPort -Port 3001  # Frontend
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "✓ Cleanup complete" -ForegroundColor Green
Write-Host ""

# Start the development servers
Write-Host "▶️  Starting servers..." -ForegroundColor Cyan
Write-Host "   Press Ctrl+C to shut down cleanly" -ForegroundColor Gray
Write-Host ""

try {
    # Use npm run dev which uses concurrently with proper shutdown flags
    npm run dev
} catch {
    Write-Host "⚠ Server interrupted" -ForegroundColor Yellow
} finally {
    Cleanup
}
