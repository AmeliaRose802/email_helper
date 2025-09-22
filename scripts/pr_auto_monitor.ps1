# Simple PR Monitor - Auto-merge when ready
# Monitors PRs #7 and #8 and auto-merges them when conditions are met

param(
    [string]$Owner = "AmeliaRose802",
    [string]$Repo = "email_helper", 
    [int[]]$PRNumbers = @(7, 8),
    [int]$CheckIntervalSeconds = 60,
    [string]$TargetBranch = "ameliapayne/add_accuracy_tracking",
    [switch]$AutoRetarget = $false,
    [switch]$AutoMerge = $false
)

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
}

function Get-PRReadiness {
    param([int]$PRNumber)
    
    try {
        # Get PR details
        $pr = gh api repos/$Owner/$Repo/pulls/$PRNumber --jq '{
            number: .number,
            title: .title,
            state: .state,
            draft: .draft,
            mergeable: .mergeable,
            commits: .commits,
            changed_files: .changed_files,
            base_branch: .base.ref,
            head_sha: .head.sha
        }' | ConvertFrom-Json
        
        # Get CI status
        $status = gh api repos/$Owner/$Repo/commits/$($pr.head_sha)/status --jq '{
            state: .state,
            total_count: .total_count
        }' | ConvertFrom-Json
        
        # Determine readiness
        $isReady = $true
        $reasons = @()
        
        if ($pr.commits -eq 0) {
            $isReady = $false
            $reasons += "No commits"
        }
        
        if ($pr.changed_files -eq 0) {
            $isReady = $false
            $reasons += "No file changes"
        }
        
        if ($pr.draft) {
            $isReady = $false
            $reasons += "Still draft"
        }
        
        if (-not $pr.mergeable) {
            $isReady = $false
            $reasons += "Not mergeable"
        }
        
        if ($status.total_count -gt 0 -and $status.state -ne "success") {
            $isReady = $false
            $reasons += "CI not passing ($($status.state))"
        }
        
        return @{
            PR      = $pr
            Status  = $status
            IsReady = $isReady
            Reasons = $reasons
        }
    }
    catch {
        Write-Log "Error checking PR #$PRNumber`: $_" "ERROR"
        return $null
    }
}

# Main execution
Write-Log "Starting automated PR monitor" "INFO"
Write-Log "Monitoring PRs: $($PRNumbers -join ', ')" "INFO"
Write-Log "Auto-retarget: $AutoRetarget | Auto-merge: $AutoMerge" "INFO"

$mergedPRs = @()

while ($mergedPRs.Count -lt $PRNumbers.Count) {
    Write-Log "Checking PR status..." "INFO"
    
    foreach ($prNumber in ($PRNumbers | Sort-Object)) {
        # Check in order (7 then 8)
        if ($prNumber -in $mergedPRs) { continue }
        
        $result = Get-PRReadiness -PRNumber $prNumber
        if (-not $result) { continue }
        
        $pr = $result.PR
        $isReady = $result.IsReady
        $reasons = $result.Reasons
        
        Write-Log "PR #$prNumber ($($pr.title)): Ready=$isReady" "INFO"
        if ($reasons.Count -gt 0) {
            Write-Log "  Blocking reasons: $($reasons -join ', ')" "INFO"
        }
        
        # Handle retargeting if needed
        if ($pr.base_branch -ne $TargetBranch) {
            Write-Log "PR #$prNumber targets '$($pr.base_branch)', should target '$TargetBranch'" "WARN"
            if ($AutoRetarget) {
                try {
                    gh api repos/$Owner/$Repo/pulls/$prNumber -X PATCH -f base=$TargetBranch
                    Write-Log "Retargeted PR #$prNumber to '$TargetBranch'" "INFO"
                    continue  # Re-check after retargeting
                }
                catch {
                    Write-Log "Failed to retarget PR #$prNumber`: $_" "ERROR"
                }
            }
        }
        
        # Handle merging if ready
        if ($isReady) {
            # Enforce dependency order
            if ($prNumber -eq 8 -and 7 -notin $mergedPRs) {
                Write-Log "PR #8 ready but waiting for PR #7 (dependency)" "INFO"
                continue
            }
            
            Write-Log "PR #$prNumber is ready to merge!" "INFO"
            
            if ($AutoMerge) {
                try {
                    gh api repos/$Owner/$Repo/pulls/$prNumber/merge -X PUT -f merge_method=merge
                    Write-Log "Successfully merged PR #$prNumber" "INFO"
                    $mergedPRs += $prNumber
                }
                catch {
                    Write-Log "Failed to merge PR #$prNumber`: $_" "ERROR"
                }
            }
            else {
                Write-Log "Auto-merge disabled. PR #$prNumber ready but not merging." "INFO"
            }
        }
    }
    
    if ($mergedPRs.Count -eq $PRNumbers.Count) {
        Write-Log "All PRs merged successfully: $($mergedPRs -join ', ')" "INFO"
        break
    }
    
    Write-Log "Waiting $CheckIntervalSeconds seconds..." "INFO"
    Start-Sleep -Seconds $CheckIntervalSeconds
}

Write-Log "Monitoring completed. Merged: $($mergedPRs -join ', ')" "INFO"