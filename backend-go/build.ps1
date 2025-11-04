# Build and Run Script for Email Helper Go Backend

param(
    [switch]$Build,
    [switch]$Run,
    [switch]$Dev,
    [switch]$Test,
    [switch]$Clean,
    [switch]$Install,
    [string]$Port = "8000"
)

$ErrorActionPreference = "Stop"

Write-Host "Email Helper Go Backend - Build Script" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check Go installation
function Test-GoInstalled {
    try {
        $goVersion = go version
        Write-Host "✓ Go is installed: $goVersion" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "✗ Go is not installed" -ForegroundColor Red
        Write-Host "  Please install Go from https://golang.org/dl/" -ForegroundColor Yellow
        return $false
    }
}

# Install dependencies
function Install-Dependencies {
    Write-Host "`nInstalling Go dependencies..." -ForegroundColor Yellow
    
    if (-not (Test-Path "go.mod")) {
        Write-Host "Initializing Go module..." -ForegroundColor Yellow
        go mod init email-helper-backend
    }
    
    Write-Host "Downloading dependencies..." -ForegroundColor Yellow
    go mod download
    go mod tidy
    
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
}

# Clean build artifacts
function Clean-Build {
    Write-Host "`nCleaning build artifacts..." -ForegroundColor Yellow
    
    if (Test-Path "bin") {
        Remove-Item -Recurse -Force "bin"
        Write-Host "✓ Removed bin/" -ForegroundColor Green
    }
    
    # Clean Go cache
    go clean -cache
    Write-Host "✓ Cleaned Go cache" -ForegroundColor Green
}

# Build binary
function Build-Binary {
    Write-Host "`nBuilding binary..." -ForegroundColor Yellow
    
    # Create bin directory
    New-Item -ItemType Directory -Force -Path "bin" | Out-Null
    
    # Get version from git or use default
    $version = "1.0.0"
    try {
        $gitTag = git describe --tags --always 2>$null
        if ($gitTag) { $version = $gitTag }
    } catch {}
    
    # Build
    $buildTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $ldflags = "-X 'main.Version=$version' -X 'main.BuildTime=$buildTime'"
    
    Write-Host "Building version: $version" -ForegroundColor Cyan
    
    # Pure Go SQLite (modernc.org/sqlite) - no CGO required
    $env:CGO_ENABLED = "0"
    
    go build -ldflags $ldflags -o bin/email-helper.exe cmd/api/main.go
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Build successful: bin/email-helper.exe" -ForegroundColor Green
        
        # Show binary info
        $binaryInfo = Get-Item "bin/email-helper.exe"
        Write-Host "  Size: $([math]::Round($binaryInfo.Length / 1MB, 2)) MB" -ForegroundColor Gray
    } else {
        Write-Host "✗ Build failed" -ForegroundColor Red
        exit 1
    }
}

# Run tests
function Run-Tests {
    Write-Host "`nRunning tests..." -ForegroundColor Yellow
    
    go test ./... -v -cover
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ All tests passed" -ForegroundColor Green
    } else {
        Write-Host "✗ Tests failed" -ForegroundColor Red
        exit 1
    }
}

# Run in development mode
function Run-Dev {
    Write-Host "`nStarting development server..." -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
    
    $env:PORT = $Port
    $env:DEBUG = "true"
    $env:CGO_ENABLED = "0"
    
    # Use air for hot reload if available, otherwise use go run
    if (Get-Command air -ErrorAction SilentlyContinue) {
        Write-Host "Using air for hot reload" -ForegroundColor Cyan
        air
    } else {
        Write-Host "Tip: Install 'air' for hot reload: go install github.com/cosmtrek/air@latest" -ForegroundColor Yellow
        go run cmd/api/main.go
    }
}

# Run built binary
function Run-Binary {
    if (-not (Test-Path "bin/email-helper.exe")) {
        Write-Host "Binary not found. Building first..." -ForegroundColor Yellow
        Build-Binary
    }
    
    Write-Host "`nStarting server on port $Port..." -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
    
    $env:PORT = $Port
    
    & "bin/email-helper.exe"
}

# Check prerequisites
function Test-Prerequisites {
    Write-Host "`nChecking prerequisites..." -ForegroundColor Yellow
    
    $allGood = $true
    
    # Check Go
    if (-not (Test-GoInstalled)) {
        $allGood = $false
    }
    
    # GCC no longer required - using pure Go SQLite (modernc.org/sqlite)
    Write-Host "✓ Using pure Go SQLite (no GCC/CGO required)" -ForegroundColor Green
    
    # Check for .env file
    if (-not (Test-Path ".env")) {
        Write-Host "⚠ .env file not found" -ForegroundColor Yellow
        Write-Host "  Copy .env.example to .env and configure" -ForegroundColor Gray
    } else {
        Write-Host "✓ .env file exists" -ForegroundColor Green
    }
    
    # Check database directory
    $dbPath = "../runtime_data/database"
    if (-not (Test-Path $dbPath)) {
        Write-Host "⚠ Database directory not found: $dbPath" -ForegroundColor Yellow
        Write-Host "  Creating directory..." -ForegroundColor Gray
        New-Item -ItemType Directory -Force -Path $dbPath | Out-Null
        Write-Host "✓ Created database directory" -ForegroundColor Green
    } else {
        Write-Host "✓ Database directory exists" -ForegroundColor Green
    }
    
    return $allGood
}

# Main execution
try {
    if (-not (Test-Prerequisites)) {
        Write-Host "`n✗ Prerequisites check failed" -ForegroundColor Red
        exit 1
    }
    
    if ($Install) {
        Install-Dependencies
    }
    
    if ($Clean) {
        Clean-Build
    }
    
    if ($Test) {
        Run-Tests
    }
    
    if ($Build) {
        Build-Binary
    }
    
    if ($Dev) {
        Run-Dev
    } elseif ($Run) {
        Run-Binary
    }
    
    # If no action specified, show help
    if (-not ($Build -or $Run -or $Dev -or $Test -or $Clean -or $Install)) {
        Write-Host "`nUsage:" -ForegroundColor Yellow
        Write-Host "  .\build.ps1 -Install      Install dependencies" -ForegroundColor Gray
        Write-Host "  .\build.ps1 -Build        Build binary" -ForegroundColor Gray
        Write-Host "  .\build.ps1 -Run          Run built binary" -ForegroundColor Gray
        Write-Host "  .\build.ps1 -Dev          Run in development mode (hot reload)" -ForegroundColor Gray
        Write-Host "  .\build.ps1 -Test         Run tests" -ForegroundColor Gray
        Write-Host "  .\build.ps1 -Clean        Clean build artifacts" -ForegroundColor Gray
        Write-Host "  .\build.ps1 -Port 9000    Specify port (default: 8000)" -ForegroundColor Gray
        Write-Host "`nExamples:" -ForegroundColor Yellow
        Write-Host "  .\build.ps1 -Install -Build -Run" -ForegroundColor Gray
        Write-Host "  .\build.ps1 -Dev -Port 9000" -ForegroundColor Gray
        Write-Host "  .\build.ps1 -Test" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "`n✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
