# PR Monitor and Merge Script
# Monitors PRs #7 and #8 for completion and merges them when ready

param(
    [string]$Owner = "AmeliaRose802",
    [string]$Repo = "email_helper",
    [int[]]$PRNumbers = @(7, 8),
    [int]$CheckIntervalSeconds = 30,
    [string]$TargetBranch = "ameliapayne/add_accuracy_tracking"
)

# Colors for output
$Colors = @{
    Info    = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error   = "Red"
}

function Write-ColorOutput {
    param([string]$Message, [string]$Type = "Info")
    Write-Host $Message -ForegroundColor $Colors[$Type]
}

function Get-PRInfo {
    param([int]$PRNumber)
    
    try {
        $response = gh api repos/$Owner/$Repo/pulls/$PRNumber --jq '{
            number: .number,
            title: .title,
            state: .state,
            draft: .draft,
            mergeable: .mergeable,
            mergeable_state: .mergeable_state,
            commits: .commits,
            changed_files: .changed_files,
            head_branch: .head.ref,
            base_branch: .base.ref,
            head_sha: .head.sha
        }'
        return $response | ConvertFrom-Json
    }
    catch {
        Write-ColorOutput "Failed to get info for PR #$PRNumber`: $_" "Error"
        return $null
    }
}

function Get-PRStatus {
    param([int]$PRNumber, [string]$HeadSHA)
    
    try {
        $response = gh api repos/$Owner/$Repo/commits/$HeadSHA/status --jq '{
            state: .state,
            total_count: .total_count
        }'
        return $response | ConvertFrom-Json
    }
    catch {
        Write-ColorOutput "Failed to get status for PR #$PRNumber`: $_" "Error"
        return @{ state = "unknown"; total_count = 0 }
    }
}

function Test-PRReadyToMerge {
    param($PRInfo, $PRStatus)
    
    # Check if PR has actual content (commits and changed files)
    if ($PRInfo.commits -eq 0 -or $PRInfo.changed_files -eq 0) {
        return $false, "No commits or file changes yet"
    }
    
    # Check if PR is still draft
    if ($PRInfo.draft) {
        return $false, "Still in draft state"
    }
    
    # Check if PR is mergeable
    if (-not $PRInfo.mergeable) {
        return $false, "Not mergeable (conflicts or issues)"
    }
    
    # Check CI status (if there are status checks)
    if ($PRStatus.total_count -gt 0 -and $PRStatus.state -ne "success") {
        return $false, "CI checks not passing (state: $($PRStatus.state))"
    }
    
    return $true, "Ready to merge"
}

function Update-PRTargetBranch {
    param([int]$PRNumber, [string]$NewBaseBranch)
    
    try {
        Write-ColorOutput "Updating PR #$PRNumber to target branch: $NewBaseBranch" "Info"
        gh api repos/$Owner/$Repo/pulls/$PRNumber -X PATCH -f base=$NewBaseBranch
        Write-ColorOutput "Successfully updated PR #$PRNumber target branch" "Success"
        return $true
    }
    catch {
        Write-ColorOutput "Failed to update PR #$PRNumber target branch: $_" "Error"
        return $false
    }
}

function Merge-PR {
    param([int]$PRNumber, [string]$MergeMethod = "merge")
    
    try {
        Write-ColorOutput "Merging PR #$PRNumber..." "Info"
        
        # Get current branch to ensure we're merging to the right place
        $currentBranch = git branch --show-current
        Write-ColorOutput "Current branch: $currentBranch" "Info"
        
        # Merge using GitHub API
        gh api repos/$Owner/$Repo/pulls/$PRNumber/merge -X PUT -f merge_method=$MergeMethod
        
        Write-ColorOutput "Successfully merged PR #$PRNumber" "Success"
        return $true
    }
    catch {
        Write-ColorOutput "Failed to merge PR #$PRNumber`: $_" "Error"
        return $false
    }
}

function Show-PRSummary {
    param($PRInfo, $PRStatus, $ReadyStatus, $ReadyReason)
    
    $statusIcon = if ($ReadyStatus) { "✅" } else { "⏳" }
    $statusColor = if ($ReadyStatus) { "Success" } else { "Warning" }
    
    Write-ColorOutput "$statusIcon PR #$($PRInfo.number): $($PRInfo.title)" $statusColor
    Write-ColorOutput "   State: $($PRInfo.state) | Draft: $($PRInfo.draft) | Commits: $($PRInfo.commits) | Files: $($PRInfo.changed_files)" "Info"
    Write-ColorOutput "   Target: $($PRInfo.base_branch) | Source: $($PRInfo.head_branch)" "Info"
    Write-ColorOutput "   Mergeable: $($PRInfo.mergeable) | CI State: $($PRStatus.state)" "Info"
    Write-ColorOutput "   Status: $ReadyReason" $statusColor
    Write-ColorOutput "" "Info"
}

# Main monitoring loop
Write-ColorOutput "🚀 Starting PR Monitor for email_helper repository" "Info"
Write-ColorOutput "Monitoring PRs: $($PRNumbers -join ', ')" "Info"
Write-ColorOutput "Target branch: $TargetBranch" "Info"
Write-ColorOutput "Check interval: $CheckIntervalSeconds seconds" "Info"
Write-ColorOutput "Press Ctrl+C to stop monitoring`n" "Warning"

$mergedPRs = @()

while ($mergedPRs.Count -lt $PRNumbers.Count) {
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-ColorOutput "[$timestamp] Checking PR status..." "Info"
    
    foreach ($prNumber in $PRNumbers) {
        if ($prNumber -in $mergedPRs) {
            continue  # Skip already merged PRs
        }
        
        # Get PR information
        $prInfo = Get-PRInfo -PRNumber $prNumber
        if (-not $prInfo) { continue }
        
        # Get CI status
        $prStatus = Get-PRStatus -PRNumber $prNumber -HeadSHA $prInfo.head_sha
        
        # Check if ready to merge
        $isReady, $reason = Test-PRReadyToMerge -PRInfo $prInfo -PRStatus $prStatus
        
        # Show current status
        Show-PRSummary -PRInfo $prInfo -PRStatus $prStatus -ReadyStatus $isReady -ReadyReason $reason
        
        # Check if PR needs to be retargeted to our feature branch
        if ($prInfo.base_branch -ne $TargetBranch) {
            Write-ColorOutput "PR #$prNumber is targeting '$($prInfo.base_branch)' but should target '$TargetBranch'" "Warning"
            
            $retarget = Read-Host "Do you want to retarget PR #$prNumber to '$TargetBranch'? (y/N)"
            if ($retarget -eq 'y' -or $retarget -eq 'Y') {
                $success = Update-PRTargetBranch -PRNumber $prNumber -NewBaseBranch $TargetBranch
                if ($success) {
                    # Re-fetch PR info after update
                    Start-Sleep -Seconds 2
                    continue
                }
            }
        }
        
        # If ready to merge, merge it
        if ($isReady) {
            Write-ColorOutput "PR #$prNumber is ready to merge!" "Success"
            
            # For dependency order: PR #7 (GUI foundation) should merge before PR #8 (charts)
            if ($prNumber -eq 8 -and 7 -notin $mergedPRs) {
                Write-ColorOutput "Waiting for PR #7 to merge first (dependency requirement)" "Warning"
                continue
            }
            
            $confirmation = Read-Host "Merge PR #$prNumber now? (Y/n)"
            if ($confirmation -ne 'n' -and $confirmation -ne 'N') {
                $success = Merge-PR -PRNumber $prNumber
                if ($success) {
                    $mergedPRs += $prNumber
                    Write-ColorOutput "✅ PR #$prNumber has been merged successfully!" "Success"
                    
                    # If this was PR #7, notify that PR #8 can now proceed
                    if ($prNumber -eq 7) {
                        Write-ColorOutput "PR #7 merged - PR #8 can now be merged when ready" "Info"
                    }
                }
            }
        }
    }
    
    # Check if all PRs are merged
    if ($mergedPRs.Count -eq $PRNumbers.Count) {
        Write-ColorOutput "🎉 All PRs have been successfully merged!" "Success"
        Write-ColorOutput "Merged PRs: $($mergedPRs -join ', ')" "Success"
        break
    }
    
    Write-ColorOutput "Waiting $CheckIntervalSeconds seconds before next check...`n" "Info"
    Start-Sleep -Seconds $CheckIntervalSeconds
}

Write-ColorOutput "PR monitoring completed. Final summary:" "Info"
Write-ColorOutput "Merged PRs: $($mergedPRs -join ', ')" "Success"

# Check current git status
Write-ColorOutput "`nCurrent git status:" "Info"
git status --porcelain
git log --oneline -5