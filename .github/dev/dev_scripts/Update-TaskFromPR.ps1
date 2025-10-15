#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick helper to update task status after merging a PR.

.DESCRIPTION
    Fetches modified files from a GitHub PR and updates task completion status
    in parallel_execution_plan.json. Automatically detects incidental completions.

.PARAMETER TaskId
    The task ID (e.g., T1.1)

.PARAMETER PRNumber
    The PR number

.EXAMPLE
    .\Update-TaskFromPR.ps1 -TaskId T1.1 -PRNumber 123
    
.EXAMPLE
    .\Update-TaskFromPR.ps1 T1.1 123
#>

param(
    [Parameter(Mandatory, Position=0)]
    [string]$TaskId,
    
    [Parameter(Mandatory, Position=1)]
    [int]$PRNumber
)

$ErrorActionPreference = "Stop"

$Owner = "AmeliaRose802"
$Repo = "email_helper"

Write-Host "🔍 Fetching PR #$PRNumber details..." -ForegroundColor Cyan

# Get PR info
try {
    $prInfo = gh pr view $PRNumber --repo "$Owner/$Repo" --json number,url,files 2>&1 | ConvertFrom-Json
    
    if (-not $prInfo) {
        Write-Host "❌ Could not fetch PR #$PRNumber" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error fetching PR: $_" -ForegroundColor Red
    exit 1
}

$prUrl = $prInfo.url
$files = $prInfo.files | ForEach-Object { $_.path }

Write-Host "✅ PR #$PRNumber found: $prUrl" -ForegroundColor Green
Write-Host "📁 Modified files ($($files.Count)):" -ForegroundColor Gray
foreach ($file in $files) {
    Write-Host "   - $file" -ForegroundColor Gray
}

Write-Host ""
Write-Host "📝 Updating task status for $TaskId..." -ForegroundColor Cyan

# Change to repo root
$repoRoot = git rev-parse --show-toplevel 2>$null
if ($LASTEXITCODE -ne 0) {
    $repoRoot = (Get-Location).Path
}
Set-Location $repoRoot

# Run the Python script
$filesArgs = $files -join " "
$command = "python .github\dev\dev_scripts\update_task_status.py check-incidental $TaskId --pr $PRNumber --url `"$prUrl`" --files $filesArgs"

Write-Host "Running: $command" -ForegroundColor Gray
Write-Host ""

try {
    Invoke-Expression $command
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Task status updated successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 Next steps:" -ForegroundColor Yellow
        Write-Host "   1. Review the changes in parallel_execution_plan.json" -ForegroundColor White
        Write-Host "   2. Commit the update:" -ForegroundColor White
        Write-Host "      git add tasklist/plan/parallel_execution_plan.json" -ForegroundColor Gray
        Write-Host "      git commit -m `"chore: mark task $TaskId as completed (PR #$PRNumber)`"" -ForegroundColor Gray
        Write-Host "      git push" -ForegroundColor Gray
        Write-Host ""
    } else {
        Write-Host "❌ Failed to update task status" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error running update script: $_" -ForegroundColor Red
    exit 1
}
