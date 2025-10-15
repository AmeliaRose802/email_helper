#!/usr/bin/env pwsh
param([int[]]$PRNumbers)

foreach ($prNum in $PRNumbers) {
    Write-Host "Approving workflows for PR #$prNum..." -ForegroundColor Cyan
    $sha = gh pr view $prNum --json commits --jq '.commits[0].sha'
    if ($sha) {
        $runs = gh api "/repos/AmeliaRose802/email_helper/actions/runs?head_sha=$sha" | ConvertFrom-Json
        foreach ($run in $runs.workflow_runs) {
            if ($run.status -eq 'action_required' -or $run.status -eq 'waiting') {
                Write-Host "  Approving run #$($run.id)..." -ForegroundColor Yellow
                gh api --method POST "/repos/AmeliaRose802/email_helper/actions/runs/$($run.id)/approve" 2>&1 | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  ✅ Approved" -ForegroundColor Green
                }
            }
        }
    }
}
Write-Host "Done!" -ForegroundColor Green
