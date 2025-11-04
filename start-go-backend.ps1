#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start the Go backend with proper environment setup.

.DESCRIPTION
    Refreshes PATH to include MinGW/GCC and starts the Go backend.
    Use this if you get GCC not found errors.
#>

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Go Backend" -ForegroundColor Cyan

# Refresh PATH to include MinGW
Write-Host "🔧 Refreshing environment variables..." -ForegroundColor Yellow
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Verify GCC is available
try {
    $gccVersion = gcc --version 2>&1 | Select-Object -First 1
    Write-Host "✓ GCC available: $gccVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ GCC not found. Please restart your terminal or reinstall MinGW." -ForegroundColor Red
    exit 1
}

# Start the backend
Write-Host "▶️  Starting backend..." -ForegroundColor Cyan
cd backend-go
go run cmd/api/main.go
