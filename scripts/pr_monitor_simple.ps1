# Simplified Autonomous PR Monitor
param(
    [int]$MaxRuntimeHours = 2,
    [int]$CheckIntervalMinutes = 3
)

$StartTime = Get-Date
$EndTime = $StartTime.AddHours($MaxRuntimeHours)

Write-Host "🤖 Starting Autonomous PR Monitor" -ForegroundColor Green
Write-Host "⏰ Will run until: $($EndTime.ToString('HH:mm:ss'))" -ForegroundColor Cyan

$iterationCount = 0
while ((Get-Date) -lt $EndTime) {
    $iterationCount++
    $currentTime = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[$currentTime] 🔍 Iteration $iterationCount - Checking GitHub status..." -ForegroundColor White
    
    try {
        # Check for open PRs
        $prs = curl -s "https://api.github.com/repos/AmeliaRose802/email_helper/pulls?state=open" | ConvertFrom-Json
        
        if ($prs.Count -eq 0) {
            Write-Host "📝 No open PRs found." -ForegroundColor Blue
            
            # Check for T9 issue #55 status
            try {
                $issue55 = curl -s "https://api.github.com/repos/AmeliaRose802/email_helper/issues/55" | ConvertFrom-Json
                
                if ($issue55.state -eq "open") {
                    if ($issue55.assignee -and $issue55.assignee.login -eq "Copilot") {
                        Write-Host "🤖 T9 Issue #55 is assigned to GitHub Copilot and ready" -ForegroundColor Green
                    } else {
                        Write-Host "📋 T9 Issue #55 is open but not assigned to Copilot" -ForegroundColor Yellow
                        Write-Host "   Please manually assign issue #55 to GitHub Copilot" -ForegroundColor Yellow
                    }
                } else {
                    Write-Host "✅ T9 Issue #55 appears to be closed/completed" -ForegroundColor Green
                }
            }
            catch {
                Write-Host "⚠️ Could not check T9 issue status" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "📋 Found $($prs.Count) open PR(s):" -ForegroundColor Blue
            foreach ($pr in $prs) {
                Write-Host "  - PR #$($pr.number): $($pr.title)" -ForegroundColor Cyan
            }
        }
    }
    catch {
        Write-Host "❌ Error checking GitHub: $_" -ForegroundColor Red
    }
    
    Write-Host "⏳ Waiting $CheckIntervalMinutes minutes..." -ForegroundColor Gray
    Start-Sleep -Seconds ($CheckIntervalMinutes * 60)
}

$actualRuntime = ((Get-Date) - $StartTime).TotalMinutes
Write-Host "`n🏁 Monitoring completed!" -ForegroundColor Green
Write-Host "⏱️ Runtime: $([math]::Round($actualRuntime, 1)) minutes" -ForegroundColor Cyan
Write-Host "🔄 Total iterations: $iterationCount" -ForegroundColor Cyan