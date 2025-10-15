# check-prerequisites.ps1
# Validates environment prerequisites for Email Helper

param(
    [switch]$Quiet = $false
)

$ErrorActionPreference = "Stop"
$script:AllChecksPassed = $true

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    if (-not $Quiet) {
        Write-Host $Message -ForegroundColor $Color
    }
}

function Test-Prerequisite {
    param(
        [string]$Name,
        [scriptblock]$Test,
        [string]$ErrorMessage
    )
    
    Write-ColorOutput "Checking $Name..." "Cyan"
    
    try {
        $result = & $Test
        if ($result) {
            Write-ColorOutput "  ✓ $Name is available" "Green"
            return $true
        } else {
            Write-ColorOutput "  ✗ $ErrorMessage" "Red"
            $script:AllChecksPassed = $false
            return $false
        }
    } catch {
        Write-ColorOutput "  ✗ $ErrorMessage" "Red"
        Write-ColorOutput "    Error: $_" "Red"
        $script:AllChecksPassed = $false
        return $false
    }
}

Write-ColorOutput "`n========================================" "Yellow"
Write-ColorOutput "  Email Helper - Prerequisite Check" "Yellow"
Write-ColorOutput "========================================`n" "Yellow"

# Check Python 3.10+
Test-Prerequisite -Name "Python 3.10+" -Test {
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            
            if ($major -ge 3 -and $minor -ge 10) {
                Write-ColorOutput "    Version: $pythonVersion" "Gray"
                return $true
            }
        }
        return $false
    } catch {
        return $false
    }
} -ErrorMessage "Python 3.10 or higher is required. Download from https://www.python.org/"

# Check Node.js 18+
Test-Prerequisite -Name "Node.js 18+" -Test {
    try {
        $nodeVersion = node --version 2>&1
        if ($nodeVersion -match "v?(\d+)\.") {
            $major = [int]$Matches[1]
            
            if ($major -ge 18) {
                Write-ColorOutput "    Version: $nodeVersion" "Gray"
                return $true
            }
        }
        return $false
    } catch {
        return $false
    }
} -ErrorMessage "Node.js 18 or higher is required. Download from https://nodejs.org/"

# Check Outlook COM availability (Windows only)
Test-Prerequisite -Name "Microsoft Outlook COM" -Test {
    try {
        $outlook = New-Object -ComObject Outlook.Application
        $version = $outlook.Version
        Write-ColorOutput "    Version: $version" "Gray"
        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($outlook) | Out-Null
        return $true
    } catch {
        return $false
    }
} -ErrorMessage "Microsoft Outlook is not installed or not properly registered. Install Outlook and run: outlook.exe /regserver"

# Check if ports are available
Write-ColorOutput "`nChecking port availability..." "Cyan"

# Check port 8000 (Backend)
$port8000InUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000InUse) {
    Write-ColorOutput "  ⚠ Port 8000 is already in use (Backend port)" "Yellow"
    Write-ColorOutput "    Process using port: PID $($port8000InUse.OwningProcess)" "Gray"
} else {
    Write-ColorOutput "  ✓ Port 8000 is available (Backend)" "Green"
}

# Check port 5173 (Frontend - Vite default)
$port5173InUse = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
if ($port5173InUse) {
    Write-ColorOutput "  ⚠ Port 5173 is already in use (Frontend port)" "Yellow"
    Write-ColorOutput "    Process using port: PID $($port5173InUse.OwningProcess)" "Gray"
} else {
    Write-ColorOutput "  ✓ Port 5173 is available (Frontend)" "Green"
}

# Check Python dependencies
Write-ColorOutput "`nChecking Python dependencies..." "Cyan"
$hasFastAPI = python -c "import fastapi" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-ColorOutput "  ✓ FastAPI is installed" "Green"
} else {
    Write-ColorOutput "  ⚠ FastAPI not found - will be installed on first run" "Yellow"
}

$hasUvicorn = python -c "import uvicorn" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-ColorOutput "  ✓ Uvicorn is installed" "Green"
} else {
    Write-ColorOutput "  ⚠ Uvicorn not found - will be installed on first run" "Yellow"
}

# Check Node dependencies
Write-ColorOutput "`nChecking Node.js dependencies..." "Cyan"
if (Test-Path "frontend\node_modules") {
    Write-ColorOutput "  ✓ Frontend dependencies installed" "Green"
} else {
    Write-ColorOutput "  ⚠ Frontend dependencies not installed - run 'npm install' in frontend directory" "Yellow"
}

# Check for required directories
Write-ColorOutput "`nChecking required directories..." "Cyan"
$requiredDirs = @("runtime_data", "runtime_data\logs", "backend", "frontend")
foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-ColorOutput "  ✓ $dir exists" "Green"
    } else {
        Write-ColorOutput "  ✗ $dir is missing" "Red"
        $script:AllChecksPassed = $false
    }
}

# Final summary
Write-ColorOutput "`n========================================" "Yellow"
if ($script:AllChecksPassed) {
    Write-ColorOutput "  ✓ All critical checks passed!" "Green"
    Write-ColorOutput "========================================`n" "Yellow"
    exit 0
} else {
    Write-ColorOutput "  ✗ Some checks failed" "Red"
    Write-ColorOutput "========================================`n" "Yellow"
    Write-ColorOutput "Please fix the issues above before starting the application." "Red"
    exit 1
}
