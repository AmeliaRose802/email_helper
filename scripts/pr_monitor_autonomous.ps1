#!/usr/bin/env pwsh
# Autonomous PR Monitoring and Task Scheduling Script
# Monitors PRs, handles merges, and schedules next tasks automatically

param(
    [string]$RepoOwner = "AmeliaRose802",
    [string]$RepoName = "email_helper",
    [int]$CheckIntervalSeconds = 30,
    [int]$MaxRuntimeMinutes = 240  # 4 hours max runtime
)

Write-Host "🤖 Starting Autonomous PR Monitor..." -ForegroundColor Cyan
Write-Host "📊 Monitoring: $RepoOwner/$RepoName" -ForegroundColor Green
Write-Host "⏱️  Check interval: $CheckIntervalSeconds seconds" -ForegroundColor Yellow
Write-Host "🕒 Max runtime: $MaxRuntimeMinutes minutes" -ForegroundColor Yellow

$StartTime = Get-Date
$EndTime = $StartTime.AddMinutes($MaxRuntimeMinutes)

# GitHub API functions
function Get-PullRequests {
    try {
        $response = curl -s "https://api.github.com/repos/$RepoOwner/$RepoName/pulls?state=open" | ConvertFrom-Json
        return $response
    }
    catch {
        Write-Host "❌ Failed to fetch PRs: $_" -ForegroundColor Red
        return @()
    }
}

function Get-PullRequestStatus {
    param([int]$PrNumber)
    try {
        $response = curl -s "https://api.github.com/repos/$RepoOwner/$RepoName/pulls/$PrNumber" | ConvertFrom-Json
        return @{
            Number = $response.number
            Title = $response.title
            State = $response.state
            Mergeable = $response.mergeable
            MergeableState = $response.mergeable_state
            Branch = $response.head.ref
            HasConflicts = ($response.mergeable_state -eq "dirty")
        }
    }
    catch {
        Write-Host "❌ Failed to get PR $PrNumber status: $_" -ForegroundColor Red
        return $null
    }
}

function Merge-PullRequest {
    param([int]$PrNumber, [string]$Branch)
    
    Write-Host "🔄 Attempting to merge PR #$PrNumber from branch $Branch..." -ForegroundColor Yellow
    
    try {
        # Fetch latest changes
        git fetch origin
        
        # Check if already merged
        $alreadyMerged = git log --oneline master --grep="Merge.*#$PrNumber" --max-count=1
        if ($alreadyMerged) {
            Write-Host "✅ PR #$PrNumber already merged" -ForegroundColor Green
            return $true
        }
        
        # Checkout master and merge
        git checkout master
        $mergeResult = git merge "origin/$Branch" 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            if ($mergeResult -match "CONFLICT") {
                Write-Host "⚠️  Merge conflicts detected for PR #$PrNumber" -ForegroundColor Yellow
                Write-Host "🔧 Attempting automatic conflict resolution..." -ForegroundColor Cyan
                
                # Simple conflict resolution for package.json files
                if (Test-Path "frontend/package.json") {
                    $packageJson = Get-Content "frontend/package.json" -Raw
                    if ($packageJson -match "<<<<<<< HEAD") {
                        Write-Host "🔧 Resolving package.json conflicts..." -ForegroundColor Cyan
                        
                        # Remove conflict markers and merge dependencies
                        $resolvedContent = $packageJson -replace "<<<<<<< HEAD.*?>>>>>>> .*?`n", ""
                        $resolvedContent = $resolvedContent -replace "=======`n", ""
                        Set-Content "frontend/package.json" $resolvedContent
                        
                        # Regenerate package-lock.json
                        Remove-Item "frontend/package-lock.json" -ErrorAction SilentlyContinue
                        Push-Location frontend
                        npm install
                        Pop-Location
                        
                        git add frontend/package.json frontend/package-lock.json
                    }
                }
                
                # Commit the merge
                git commit -m "Auto-merge PR #$PrNumber: Resolve conflicts and merge changes"
            }
            else {
                throw "Merge failed: $mergeResult"
            }
        }
        
        # Push to master
        git push origin master
        Write-Host "✅ Successfully merged PR #$PrNumber" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ Failed to merge PR #$PrNumber: $_" -ForegroundColor Red
        git merge --abort 2>$null
        return $false
    }
}

function Get-NextReadyTasks {
    # Read the task plan to determine what's ready next
    $planFile = "tasks/react_native_ui_plan.md"
    if (Test-Path $planFile) {
        $content = Get-Content $planFile -Raw
        
        # Simple task status parsing
        if ($content -match "T8.*Task Management.*ready|T8.*Interface.*ready") {
            return @("T8")
        }
        elseif ($content -match "T9.*Background.*ready|T9.*Processing.*ready") {
            return @("T9")
        }
        elseif ($content -match "T10.*Deployment.*ready") {
            return @("T10")
        }
    }
    
    return @()
}

function Schedule-NextTasks {
    param([array]$ReadyTasks)
    
    if ($ReadyTasks.Count -eq 0) {
        Write-Host "ℹ️  No tasks ready to schedule" -ForegroundColor Blue
        return
    }
    
    Write-Host "🚀 Scheduling next batch of tasks: $($ReadyTasks -join ', ')" -ForegroundColor Green
    
    foreach ($task in $ReadyTasks) {
        Write-Host "📋 Scheduling $task..." -ForegroundColor Cyan
        
        # Find the GitHub issue for this task
        try {
            $issues = curl -s "https://api.github.com/repos/$RepoOwner/$RepoName/issues?state=open" | ConvertFrom-Json
            $taskIssue = $issues | Where-Object { $_.title -match $task }
            
            if ($taskIssue) {
                Write-Host "✅ Found issue #$($taskIssue.number) for $task" -ForegroundColor Green
                
                # The task should already be assigned to @github-copilot
                # Just log that it's ready
                Write-Host "🤖 Task $task (Issue #$($taskIssue.number)) is ready for GitHub Copilot" -ForegroundColor Cyan
            }
            else {
                Write-Host "⚠️  No open issue found for task $task" -ForegroundColor Yellow
            }
        }
        catch {
            Write-Host "❌ Failed to check issues for $task: $_" -ForegroundColor Red
        }
    }
}

# Main monitoring loop
Write-Host "`n🔄 Starting monitoring loop..." -ForegroundColor Cyan

$iterationCount = 0
while ((Get-Date) -lt $EndTime) {
    $iterationCount++
    $currentTime = Get-Date -Format "HH:mm:ss"
    
    Write-Host "`n--- Iteration $iterationCount at $currentTime ---" -ForegroundColor Magenta
    
    # Get all open PRs
    $prs = Get-PullRequests
    Write-Host "📋 Found $($prs.Count) open PRs" -ForegroundColor Blue
    
    $merged = 0
    $pending = 0
    
    foreach ($pr in $prs) {
        $status = Get-PullRequestStatus -PrNumber $pr.number
        
        if ($status) {
            Write-Host "🔍 PR #$($status.Number): $($status.Title)" -ForegroundColor Cyan
            Write-Host "   State: $($status.State), Mergeable: $($status.Mergeable), Status: $($status.MergeableState)" -ForegroundColor Gray
            
            if ($status.State -eq "open" -and $status.Mergeable -eq $true -and $status.MergeableState -eq "clean") {
                Write-Host "✅ PR #$($status.Number) is ready to merge!" -ForegroundColor Green
                
                if (Merge-PullRequest -PrNumber $status.Number -Branch $status.Branch) {
                    $merged++
                    Write-Host "🎉 Successfully merged PR #$($status.Number)" -ForegroundColor Green
                }
            }
            elseif ($status.HasConflicts) {
                Write-Host "⚠️  PR #$($status.Number) has conflicts - attempting resolution..." -ForegroundColor Yellow
                
                if (Merge-PullRequest -PrNumber $status.Number -Branch $status.Branch) {
                    $merged++
                    Write-Host "🎉 Successfully resolved conflicts and merged PR #$($status.Number)" -ForegroundColor Green
                }
                else {
                    $pending++
                }
            }
            else {
                $pending++
                Write-Host "⏳ PR #$($status.Number) not ready yet (State: $($status.MergeableState))" -ForegroundColor Yellow
            }
        }
    }
    
    # After processing PRs, check for next tasks to schedule
    if ($merged -gt 0) {
        Write-Host "`n🚀 Merged $merged PRs - checking for next tasks..." -ForegroundColor Green
        $readyTasks = Get-NextReadyTasks
        Schedule-NextTasks -ReadyTasks $readyTasks
    }
    
    Write-Host "`n📊 Summary: $merged merged, $pending pending" -ForegroundColor Blue
    
    # Wait before next iteration
    if ((Get-Date) -lt $EndTime.AddSeconds(-$CheckIntervalSeconds)) {
        Write-Host "💤 Waiting $CheckIntervalSeconds seconds..." -ForegroundColor Gray
        Start-Sleep -Seconds $CheckIntervalSeconds
    }
    else {
        Write-Host "⏰ Approaching max runtime, stopping..." -ForegroundColor Yellow
        break
    }
}

$actualRuntime = ((Get-Date) - $StartTime).TotalMinutes
Write-Host "`n🏁 Autonomous monitoring completed!" -ForegroundColor Green
Write-Host "⏱️  Runtime: $([math]::Round($actualRuntime, 1)) minutes" -ForegroundColor Cyan
Write-Host "🔄 Total iterations: $iterationCount" -ForegroundColor Cyan
Write-Host "👋 Exiting autonomous mode" -ForegroundColor Yellow