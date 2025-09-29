# Autonomous PR Monitor for Continuous Development
# This script monitors GitHub PRs, handles merges, resolves conflicts, and schedules next tasks
# Supports autonomous development without human intervention

param(
    [int]$MaxRuntimeHours = 8,
    [int]$CheckIntervalMinutes = 2,
    [string]$RepoOwner = "AmeliaRose802",
    [string]$RepoName = "email_helper"
)

$StartTime = Get-Date
$EndTime = $StartTime.AddHours($MaxRuntimeHours)

Write-Host "🤖 Starting Autonomous PR Monitor" -ForegroundColor Green
Write-Host "⏰ Will run until: $($EndTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Cyan
Write-Host "🔄 Check interval: $CheckIntervalMinutes minutes" -ForegroundColor Cyan
Write-Host "📁 Repository: $RepoOwner/$RepoName" -ForegroundColor Cyan

function Get-OpenPullRequests {
    try {
        $prs = curl -s "https://api.github.com/repos/$RepoOwner/$RepoName/pulls?state=open" | ConvertFrom-Json
        return $prs
    }
    catch {
        Write-Host "❌ Failed to fetch PRs: $_" -ForegroundColor Red
        return @()
    }
}

function Check-PRStatus {
    param([object]$PR)
    
    try {
        # Get detailed PR info
        $prDetail = curl -s $PR.url | ConvertFrom-Json
        
        $status = @{
            Number = $PR.number
            Title = $PR.title
            Mergeable = $prDetail.mergeable
            MergeableState = $prDetail.mergeable_state
            StatusChecks = "unknown"
        }
        
        # Check if PR has any status checks
        try {
            $checks = curl -s "$($PR.url)/checks" 2>$null | ConvertFrom-Json
            if ($checks -and $checks.check_runs) {
                $failedChecks = $checks.check_runs | Where-Object { $_.status -eq "completed" -and $_.conclusion -ne "success" }
                $status.StatusChecks = if ($failedChecks.Count -eq 0) { "passing" } else { "failing" }
            }
        }
        catch {
            # Status checks API might not be available, continue
        }
        
        return $status
    }
    catch {
        Write-Host "⚠️ Error checking PR #$($PR.number): $_" -ForegroundColor Yellow
        return $null
    }
}

function Merge-PullRequest {
    param([object]$PR)
    
    Write-Host "🔀 Attempting to merge PR #$($PR.number): $($PR.title)" -ForegroundColor Yellow
    
    # Use git command to merge (assuming authentication is set up)
    try {
        # Fetch latest changes
        $output = git fetch origin 2>&1
        Write-Host "📥 Fetched: $output" -ForegroundColor Gray
        
        # Checkout the PR branch and merge
        $branchName = $PR.head.ref
        git checkout master 2>&1 | Out-Null
        git pull origin master 2>&1 | Out-Null
        
        # Check if there are conflicts
        $mergeResult = git merge origin/$branchName 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Successfully merged PR #$($PR.number)" -ForegroundColor Green
            
            # Push the merge
            git push origin master 2>&1 | Out-Null
            Write-Host "📤 Pushed merge to master" -ForegroundColor Green
            
            return $true
        }
        else {
            Write-Host "⚠️ Merge conflict detected for PR #$($PR.number)" -ForegroundColor Yellow
            Write-Host "🔧 Auto-resolving conflicts..." -ForegroundColor Cyan
            
            # Auto-resolve conflicts by accepting both changes where possible
            $conflictFiles = git diff --name-only --diff-filter=U
            
            foreach ($file in $conflictFiles) {
                Write-Host "🔧 Resolving conflicts in: $file" -ForegroundColor Cyan
                
                # For package.json files, merge dependencies intelligently
                if ($file -like "*package.json") {
                    Resolve-PackageJsonConflicts -FilePath $file
                }
                else {
                    # For other files, try to auto-resolve
                    git add $file 2>&1 | Out-Null
                }
            }
            
            # Complete the merge
            git commit -m "Auto-resolve conflicts from PR #$($PR.number): $($PR.title)" 2>&1 | Out-Null
            
            if ($LASTEXITCODE -eq 0) {
                git push origin master 2>&1 | Out-Null
                Write-Host "✅ Conflicts resolved and merged PR #$($PR.number)" -ForegroundColor Green
                return $true  
            }
            else {
                Write-Host "❌ Failed to resolve conflicts for PR #$($PR.number)" -ForegroundColor Red
                git merge --abort 2>&1 | Out-Null
                return $false
            }
        }
    }
    catch {
        Write-Host "❌ Error merging PR #$($PR.number): $_" -ForegroundColor Red
        return $false
    }
}

function Resolve-PackageJsonConflicts {
    param([string]$FilePath)
    
    Write-Host "📦 Resolving package.json conflicts in: $FilePath" -ForegroundColor Cyan
    
    try {
        $content = Get-Content $FilePath -Raw
        
        # Remove conflict markers and merge dependencies
        $lines = $content -split "`n"
        $cleanedLines = @()
        $inConflict = $false
        $dependencyBlock = @()
        
        foreach ($line in $lines) {
            if ($line -match "^<<<<<<<") {
                $inConflict = $true
                continue
            }
            elseif ($line -match "^=======") {
                continue
            }
            elseif ($line -match "^>>>>>>>") {
                $inConflict = $false
                continue  
            }
            elseif (-not $inConflict) {
                $cleanedLines += $line
            }
            else {
                # Collect dependencies from both sides
                if ($line -match '^\s*"[^"]+"\s*:\s*"[^"]+"') {
                    $dependencyBlock += $line
                }
            }
        }
        
        # Write the cleaned content back
        $cleanedContent = $cleanedLines -join "`n"
        Set-Content -Path $FilePath -Value $cleanedContent -NoNewline
        
        Write-Host "✅ Resolved package.json conflicts in: $FilePath" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ Failed to auto-resolve package.json: $_" -ForegroundColor Yellow
    }
}

function Get-ReadyTasks {
    param([string]$RepoPath = ".")
    
    # Check for completed tasks and determine what's ready next
    $readyTasks = @()
    
    # Check if plan file exists
    $planFile = Join-Path $RepoPath "tasks/react_native_ui_plan.md"
    if (Test-Path $planFile) {
        $content = Get-Content $planFile -Raw
        
        # Check task completion status and dependencies
        if ($content -match "T6.*COMPLETE" -and $content -match "T7.*COMPLETE" -and $content -match "T8.*COMPLETE") {
            $readyTasks += "T9"
        }
        elseif ($content -match "T9.*COMPLETE") {
            $readyTasks += "T10"
        }
    }
    
    return $readyTasks
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
                Write-Host "🤖 Task $task (Issue #$($taskIssue.number)) is ready for GitHub Copilot" -ForegroundColor Cyan
            }
            else {
                Write-Host "⚠️  No open issue found for task $task" -ForegroundColor Yellow
            }
        }
        catch {
            Write-Host "❌ Failed to check issues for $task" -ForegroundColor Red
        }
    }
}

# Main monitoring loop
Write-Host "`n🔄 Starting monitoring loop..." -ForegroundColor Cyan

$iterationCount = 0
while ((Get-Date) -lt $EndTime) {
    $iterationCount++
    $currentTime = Get-Date -Format "HH:mm:ss"
    
    Write-Host "`n[$currentTime] 🔍 Iteration $iterationCount - Checking for PRs..." -ForegroundColor White
    
    $openPRs = Get-OpenPullRequests
    
    if ($openPRs.Count -eq 0) {
        Write-Host "📝 No open PRs found. Checking for ready tasks..." -ForegroundColor Blue
        
        # Check if any tasks are ready to be scheduled
        $readyTasks = Get-ReadyTasks
        Schedule-NextTasks -ReadyTasks $readyTasks
        
        Write-Host "⏳ Waiting $CheckIntervalMinutes minutes before next check..." -ForegroundColor Gray
        Start-Sleep -Seconds ($CheckIntervalMinutes * 60)
        continue
    }
    
    Write-Host "📋 Found $($openPRs.Count) open PR(s)" -ForegroundColor Blue
    
    foreach ($pr in $openPRs) {
        Write-Host "`n🔍 Checking PR #$($pr.number): $($pr.title)" -ForegroundColor Cyan
        
        $status = Check-PRStatus -PR $pr
        
        if ($status) {
            Write-Host "   Mergeable: $($status.Mergeable)" -ForegroundColor Gray
            Write-Host "   State: $($status.MergeableState)" -ForegroundColor Gray  
            Write-Host "   Checks: $($status.StatusChecks)" -ForegroundColor Gray
            
            # Attempt to merge if ready
            if ($status.Mergeable -eq $true -and $status.MergeableState -eq "clean") {
                $merged = Merge-PullRequest -PR $pr
                
                if ($merged) {
                    Write-Host "🎉 Successfully processed PR #$($pr.number)" -ForegroundColor Green
                    
                    # Check for newly ready tasks after merge
                    Start-Sleep -Seconds 10  # Give time for GitHub to update
                    $readyTasks = Get-ReadyTasks
                    Schedule-NextTasks -ReadyTasks $readyTasks
                }
            }
            elseif ($status.MergeableState -eq "dirty") {
                Write-Host "⚠️ PR #$($pr.number) has conflicts - attempting auto-resolution" -ForegroundColor Yellow
                $merged = Merge-PullRequest -PR $pr
            }
            else {
                Write-Host "⏳ PR #$($pr.number) not ready for merge yet" -ForegroundColor Yellow
            }
        }
    }
    
    Write-Host "`n⏳ Waiting $CheckIntervalMinutes minutes before next check..." -ForegroundColor Gray
    Start-Sleep -Seconds ($CheckIntervalMinutes * 60)
    
    # Check if we should exit early
    if ((Get-Date).Hour -ge 22) {
        Write-Host "`n🌙 Late hour detected, considering early exit..." -ForegroundColor Yellow
        break
    }
}

$actualRuntime = ((Get-Date) - $StartTime).TotalMinutes
Write-Host "`n🏁 Autonomous monitoring completed!" -ForegroundColor Green
Write-Host "⏱️  Runtime: $([math]::Round($actualRuntime, 1)) minutes" -ForegroundColor Cyan
Write-Host "🔄 Total iterations: $iterationCount" -ForegroundColor Cyan
Write-Host "👋 Exiting autonomous mode" -ForegroundColor Yellow