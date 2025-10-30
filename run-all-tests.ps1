# run-all-tests.ps1
# Comprehensive test runner for Email Helper project
# Runs all tests: Python backend tests, Python src tests, frontend unit tests, and E2E tests

param(
    [switch]$SkipBackend,
    [switch]$SkipFrontend,
    [switch]$SkipE2E,
    [switch]$SkipSrc,
    [switch]$Coverage,
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"
$originalLocation = Get-Location

# Color output functions
function Write-Header {
    param([string]$Message)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Failure {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Yellow
}

# Track results
$results = @{
    BackendTests = $null
    SrcTests = $null
    FrontendUnitTests = $null
    FrontendE2ETests = $null
}

$totalStartTime = Get-Date

# 1. Backend Python Tests (pytest for backend/)
if (-not $SkipBackend) {
    Write-Header "Running Backend Tests (pytest backend/tests/)"
    
    $backendArgs = @("python", "-m", "pytest", "backend/tests/", "-v")
    if ($Coverage) {
        $backendArgs += @("--cov=backend", "--cov-report=term-missing", "--cov-report=html:runtime_data/coverage/backend")
    }
    if ($Verbose) {
        $backendArgs += "-vv"
    }
    
    try {
        & $backendArgs[0] $backendArgs[1..($backendArgs.Length-1)]
        $results.BackendTests = $LASTEXITCODE -eq 0
    } catch {
        Write-Failure "Backend tests failed to run: $_"
        $results.BackendTests = $false
    }
}

# 2. Src Python Tests (pytest for test/)
if (-not $SkipSrc) {
    Write-Header "Running Src Tests (pytest test/)"
    
    $srcArgs = @("python", "-m", "pytest", "test/", "-v")
    if ($Coverage) {
        $srcArgs += @("--cov=src", "--cov-report=term-missing", "--cov-report=html:runtime_data/coverage/src")
    }
    if ($Verbose) {
        $srcArgs += "-vv"
    }
    
    try {
        & $srcArgs[0] $srcArgs[1..($srcArgs.Length-1)]
        $results.SrcTests = $LASTEXITCODE -eq 0
    } catch {
        Write-Failure "Src tests failed to run: $_"
        $results.SrcTests = $false
    }
}

# 3. Frontend Unit Tests (vitest)
if (-not $SkipFrontend) {
    Write-Header "Running Frontend Unit Tests (vitest)"
    
    Set-Location "frontend"
    try {
        if ($Coverage) {
            npm run test:run -- --coverage
        } else {
            npm run test:run
        }
        $results.FrontendUnitTests = $LASTEXITCODE -eq 0
    } catch {
        Write-Failure "Frontend unit tests failed to run: $_"
        $results.FrontendUnitTests = $false
    } finally {
        Set-Location $originalLocation
    }
}

# 4. Frontend E2E Tests (Playwright)
if (-not $SkipE2E) {
    Write-Header "Running Frontend E2E Tests (Playwright)"
    
    Set-Location "frontend"
    try {
        npm run test:e2e
        $results.FrontendE2ETests = $LASTEXITCODE -eq 0
    } catch {
        Write-Failure "Frontend E2E tests failed to run: $_"
        $results.FrontendE2ETests = $false
    } finally {
        Set-Location $originalLocation
    }
}

# Summary
$totalEndTime = Get-Date
$totalDuration = $totalEndTime - $totalStartTime

Write-Header "Test Results Summary"

$allPassed = $true
foreach ($suite in $results.Keys) {
    $result = $results[$suite]
    if ($null -eq $result) {
        Write-Info "$suite : SKIPPED"
    } elseif ($result) {
        Write-Success "$suite : PASSED"
    } else {
        Write-Failure "$suite : FAILED"
        $allPassed = $false
    }
}

Write-Host "`nTotal Duration: $($totalDuration.ToString('mm\:ss'))" -ForegroundColor Cyan

if ($allPassed) {
    Write-Success "`nAll test suites passed! ✨"
    exit 0
} else {
    Write-Failure "`nSome test suites failed. Please review the output above."
    exit 1
}
