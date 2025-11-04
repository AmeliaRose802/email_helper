#!/usr/bin/env pwsh
# Script to run Go tests
# NOTE: CGO is no longer required - using pure Go SQLite (modernc.org/sqlite)

$ErrorActionPreference = "Stop"

Write-Host "Using pure Go SQLite (modernc.org/sqlite) - no CGO/GCC required" -ForegroundColor Green
Write-Host "CGO_ENABLED=0 for faster, simpler builds" -ForegroundColor Cyan

# Explicitly disable CGO (not required, but makes it clear)
$env:CGO_ENABLED = "0"

# Run tests
Write-Host "`nRunning Go tests..." -ForegroundColor Cyan
$testPath = if ($args.Count -gt 0) { $args[0] } else { "./..." }

go test $testPath -v $args[1..($args.Count-1)]

exit $LASTEXITCODE
