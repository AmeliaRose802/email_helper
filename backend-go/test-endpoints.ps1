# Email Helper API Endpoint Testing Script
# Tests all endpoints defined in api-spec.yml with real Azure OpenAI credentials
# Usage: .\test-endpoints.ps1 [-BaseUrl http://localhost:8000] [-Verbose]

param(
    [string]$BaseUrl = "http://localhost:8000",
    [switch]$Verbose,
    [switch]$SkipAI  # Skip AI endpoints if Azure OpenAI not configured
)

$ErrorActionPreference = "Continue"
$script:TestResults = @()
$script:PassCount = 0
$script:FailCount = 0
$script:SkipCount = 0

# Color output helpers
function Write-TestHeader($text) {
    Write-Host "`n═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  $text" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
}

function Write-TestResult($name, $status, $message = "") {
    $timestamp = Get-Date -Format "HH:mm:ss"
    $result = @{
        Name = $name
        Status = $status
        Message = $message
        Timestamp = $timestamp
    }
    $script:TestResults += $result
    
    switch ($status) {
        "PASS" { 
            $script:PassCount++
            Write-Host "[$timestamp] ✓ " -ForegroundColor Green -NoNewline
            Write-Host "$name" -ForegroundColor White
        }
        "FAIL" { 
            $script:FailCount++
            Write-Host "[$timestamp] ✗ " -ForegroundColor Red -NoNewline
            Write-Host "$name" -ForegroundColor White
            if ($message) { Write-Host "    Error: $message" -ForegroundColor Red }
        }
        "SKIP" {
            $script:SkipCount++
            Write-Host "[$timestamp] ⊘ " -ForegroundColor Yellow -NoNewline
            Write-Host "$name" -ForegroundColor Gray
            if ($message) { Write-Host "    Reason: $message" -ForegroundColor Yellow }
        }
    }
}

# HTTP request helper
function Invoke-APIRequest {
    param(
        [string]$Method,
        [string]$Endpoint,
        [object]$Body = $null,
        [int]$ExpectedStatus = 200,
        [string]$ContentType = "application/json"
    )
    
    $url = "$BaseUrl$Endpoint"
    $headers = @{
        "Content-Type" = $ContentType
        "Accept" = "application/json"
    }
    
    try {
        $params = @{
            Uri = $url
            Method = $Method
            Headers = $headers
            TimeoutSec = 30
        }
        
        if ($Body) {
            if ($Body -is [string]) {
                $params.Body = $Body
            } else {
                $params.Body = ($Body | ConvertTo-Json -Depth 10 -Compress)
            }
        }
        
        if ($Verbose) {
            Write-Host "  → $Method $url" -ForegroundColor Gray
            if ($Body) {
                Write-Host "    Body: $($params.Body)" -ForegroundColor DarkGray
            }
        }
        
        $response = Invoke-WebRequest @params -UseBasicParsing
        
        $result = @{
            Success = $true
            StatusCode = $response.StatusCode
            Content = $response.Content
            Data = $null
        }
        
        # Try to parse JSON
        if ($response.Content) {
            try {
                $result.Data = $response.Content | ConvertFrom-Json
            } catch {
                # Not JSON, keep as string
            }
        }
        
        # Validate status code
        if ($response.StatusCode -ne $ExpectedStatus) {
            $result.Success = $false
            $result.Error = "Expected status $ExpectedStatus but got $($response.StatusCode)"
        }
        
        if ($Verbose -and $result.Data) {
            Write-Host "  ← Status: $($response.StatusCode)" -ForegroundColor Gray
            Write-Host "    Response: $($result.Content.Substring(0, [Math]::Min(200, $result.Content.Length)))..." -ForegroundColor DarkGray
        }
        
        return $result
        
    } catch {
        return @{
            Success = $false
            StatusCode = $_.Exception.Response.StatusCode.Value__
            Error = $_.Exception.Message
            Content = $null
            Data = $null
        }
    }
}

# Test suites
function Test-HealthEndpoints {
    Write-TestHeader "Health & Status Endpoints"
    
    # Test /health
    $result = Invoke-APIRequest -Method GET -Endpoint "/health"
    if ($result.Success -and $result.Data.status -eq "healthy") {
        Write-TestResult "GET /health" "PASS"
    } else {
        Write-TestResult "GET /health" "FAIL" $result.Error
    }
    
    # Test root /
    $result = Invoke-APIRequest -Method GET -Endpoint "/"
    if ($result.Success -and $result.Data.message) {
        Write-TestResult "GET /" "PASS"
    } else {
        Write-TestResult "GET /" "FAIL" $result.Error
    }
}

function Test-AIEndpoints {
    Write-TestHeader "AI Processing Endpoints"
    
    if ($SkipAI) {
        Write-TestResult "AI Endpoints" "SKIP" "Azure OpenAI not configured"
        return
    }
    
    # Test AI health
    $result = Invoke-APIRequest -Method GET -Endpoint "/api/ai/health"
    if ($result.Success) {
        Write-TestResult "GET /api/ai/health" "PASS"
    } else {
        Write-TestResult "GET /api/ai/health" "FAIL" $result.Error
        Write-Host "  WARNING: AI service may not be available. Skipping AI tests..." -ForegroundColor Yellow
        return
    }
    
    # Test email classification
    $classifyBody = @{
        subject = "Team meeting tomorrow at 2 PM"
        sender = "manager@company.com"
        content = "Hi team, please join us for our weekly sync tomorrow at 2 PM in Conference Room A. We'll discuss Q4 planning and project updates."
        context = ""
    }
    
    $result = Invoke-APIRequest -Method POST -Endpoint "/api/ai/classify" -Body $classifyBody
    if ($result.Success -and $result.Data.category) {
        $category = $result.Data.category
        $confidence = $result.Data.confidence
        Write-TestResult "POST /api/ai/classify" "PASS"
        if ($Verbose) {
            Write-Host "    Category: $category (confidence: $confidence)" -ForegroundColor Gray
        }
    } else {
        Write-TestResult "POST /api/ai/classify" "FAIL" $result.Error
    }
    
    # Test action item extraction
    $actionItemBody = @{
        email_content = "Please review the attached proposal by Friday and send me your feedback. Also, don't forget to update the project timeline in Jira."
        context = ""
    }
    
    $result = Invoke-APIRequest -Method POST -Endpoint "/api/ai/action-items" -Body $actionItemBody
    if ($result.Success -and $result.Data.PSObject.Properties.Name -contains "action_items") {
        Write-TestResult "POST /api/ai/action-items" "PASS"
        if ($Verbose -and $result.Data.action_items) {
            Write-Host "    Action Items: $($result.Data.action_items -join ', ')" -ForegroundColor Gray
        }
    } else {
        Write-TestResult "POST /api/ai/action-items" "FAIL" $result.Error
    }
    
    # Test summarization
    $summarizeBody = @{
        email_content = "This is a long email about our Q4 planning. We need to finalize the budget, review team capacity, and set OKRs for the next quarter. The deadline is approaching fast."
        summary_type = "brief"
    }
    
    $result = Invoke-APIRequest -Method POST -Endpoint "/api/ai/summarize" -Body $summarizeBody
    if ($result.Success -and $result.Data.summary) {
        Write-TestResult "POST /api/ai/summarize" "PASS"
        if ($Verbose) {
            Write-Host "    Summary: $($result.Data.summary)" -ForegroundColor Gray
        }
    } else {
        Write-TestResult "POST /api/ai/summarize" "FAIL" $result.Error
    }
    
    # Test templates list
    $result = Invoke-APIRequest -Method GET -Endpoint "/api/ai/templates"
    if ($result.Success -and $result.Data.templates) {
        Write-TestResult "GET /api/ai/templates" "PASS"
        if ($Verbose) {
            Write-Host "    Templates: $($result.Data.templates -join ', ')" -ForegroundColor Gray
        }
    } else {
        Write-TestResult "GET /api/ai/templates" "FAIL" $result.Error
    }
}

function Test-EmailEndpoints {
    Write-TestHeader "Email Management Endpoints"
    
    # Test get emails list
    $result = Invoke-APIRequest -Method GET -Endpoint "/api/emails?limit=10&offset=0"
    if ($result.Success) {
        Write-TestResult "GET /api/emails" "PASS"
        $script:testEmailId = $null
        if ($result.Data.emails -and $result.Data.emails.Count -gt 0) {
            $script:testEmailId = $result.Data.emails[0].id
            if ($Verbose) {
                Write-Host "    Found $($result.Data.total) emails, first ID: $script:testEmailId" -ForegroundColor Gray
            }
        }
    } else {
        Write-TestResult "GET /api/emails" "FAIL" $result.Error
    }
    
    # Test email stats
    $result = Invoke-APIRequest -Method GET -Endpoint "/api/emails/stats?limit=100"
    if ($result.Success -and $result.Data.PSObject.Properties.Name -contains "total_emails") {
        Write-TestResult "GET /api/emails/stats" "PASS"
        if ($Verbose) {
            Write-Host "    Total emails: $($result.Data.total_emails)" -ForegroundColor Gray
        }
    } else {
        Write-TestResult "GET /api/emails/stats" "FAIL" $result.Error
    }
    
    # Test email search
    $result = Invoke-APIRequest -Method GET -Endpoint "/api/emails/search?q=test&page=1&per_page=10"
    if ($result.Success) {
        Write-TestResult "GET /api/emails/search" "PASS"
    } else {
        Write-TestResult "GET /api/emails/search" "FAIL" $result.Error
    }
    
    # Test get specific email (if we have an ID)
    if ($script:testEmailId) {
        $result = Invoke-APIRequest -Method GET -Endpoint "/api/emails/$script:testEmailId"
        if ($result.Success -and $result.Data.id) {
            Write-TestResult "GET /api/emails/:id" "PASS"
        } else {
            Write-TestResult "GET /api/emails/:id" "FAIL" $result.Error
        }
    } else {
        Write-TestResult "GET /api/emails/:id" "SKIP" "No email ID available"
    }
    
    # Test folders list
    $result = Invoke-APIRequest -Method GET -Endpoint "/api/folders"
    if ($result.Success -and $result.Data.folders) {
        Write-TestResult "GET /api/folders" "PASS"
        if ($Verbose) {
            Write-Host "    Found $($result.Data.total) folders" -ForegroundColor Gray
        }
    } else {
        Write-TestResult "GET /api/folders" "FAIL" $result.Error
    }
}

function Test-TaskEndpoints {
    Write-TestHeader "Task Management Endpoints"
    
    # Test get tasks
    $result = Invoke-APIRequest -Method GET -Endpoint "/api/tasks?page=1&limit=20"
    if ($result.Success) {
        Write-TestResult "GET /api/tasks" "PASS"
        $script:testTaskId = $null
        if ($result.Data.tasks -and $result.Data.tasks.Count -gt 0) {
            $script:testTaskId = $result.Data.tasks[0].id
            if ($Verbose) {
                Write-Host "    Found $($result.Data.total_count) tasks, first ID: $script:testTaskId" -ForegroundColor Gray
            }
        }
    } else {
        Write-TestResult "GET /api/tasks" "FAIL" $result.Error
    }
    
    # Test task stats
    $result = Invoke-APIRequest -Method GET -Endpoint "/api/tasks/stats"
    if ($result.Success -and $result.Data.PSObject.Properties.Name -contains "total_tasks") {
        Write-TestResult "GET /api/tasks/stats" "PASS"
        if ($Verbose) {
            Write-Host "    Total tasks: $($result.Data.total_tasks)" -ForegroundColor Gray
        }
    } else {
        Write-TestResult "GET /api/tasks/stats" "FAIL" $result.Error
    }
    
    # Test create task
    $createTaskBody = @{
        title = "Test Task - API Validation"
        description = "Created by endpoint testing script"
        status = "pending"
        priority = "medium"
        category = "testing"
    }
    
    $result = Invoke-APIRequest -Method POST -Endpoint "/api/tasks" -Body $createTaskBody -ExpectedStatus 201
    if ($result.Success -and $result.Data.id) {
        $createdTaskId = $result.Data.id
        Write-TestResult "POST /api/tasks" "PASS"
        
        # Test get specific task
        $result = Invoke-APIRequest -Method GET -Endpoint "/api/tasks/$createdTaskId"
        if ($result.Success -and $result.Data.id -eq $createdTaskId) {
            Write-TestResult "GET /api/tasks/:id" "PASS"
        } else {
            Write-TestResult "GET /api/tasks/:id" "FAIL" $result.Error
        }
        
        # Test update task
        $updateTaskBody = @{
            title = "Test Task - Updated"
            status = "in_progress"
        }
        
        $result = Invoke-APIRequest -Method PUT -Endpoint "/api/tasks/$createdTaskId" -Body $updateTaskBody
        if ($result.Success -and $result.Data.status -eq "in_progress") {
            Write-TestResult "PUT /api/tasks/:id" "PASS"
        } else {
            Write-TestResult "PUT /api/tasks/:id" "FAIL" $result.Error
        }
        
        # Test delete task
        $result = Invoke-APIRequest -Method DELETE -Endpoint "/api/tasks/$createdTaskId"
        if ($result.Success) {
            Write-TestResult "DELETE /api/tasks/:id" "PASS"
        } else {
            Write-TestResult "DELETE /api/tasks/:id" "FAIL" $result.Error
        }
        
    } else {
        Write-TestResult "POST /api/tasks" "FAIL" $result.Error
        Write-TestResult "GET /api/tasks/:id" "SKIP" "Task creation failed"
        Write-TestResult "PUT /api/tasks/:id" "SKIP" "Task creation failed"
        Write-TestResult "DELETE /api/tasks/:id" "SKIP" "Task creation failed"
    }
}

function Test-SettingsEndpoints {
    Write-TestHeader "Settings Management Endpoints"
    
    # Test get settings
    $result = Invoke-APIRequest -Method GET -Endpoint "/api/settings"
    if ($result.Success) {
        Write-TestResult "GET /api/settings" "PASS"
        $originalSettings = $result.Data
        
        # Test update settings
        $updateBody = @{
            username = $originalSettings.username
            job_context = "Software Engineer working on email automation"
        }
        
        $result = Invoke-APIRequest -Method PUT -Endpoint "/api/settings" -Body $updateBody
        if ($result.Success) {
            Write-TestResult "PUT /api/settings" "PASS"
        } else {
            Write-TestResult "PUT /api/settings" "FAIL" $result.Error
        }
        
    } else {
        Write-TestResult "GET /api/settings" "FAIL" $result.Error
        Write-TestResult "PUT /api/settings" "SKIP" "Settings retrieval failed"
    }
}

function Test-ProcessingEndpoints {
    Write-TestHeader "Processing Pipeline Endpoints"
    
    # Test processing stats
    $result = Invoke-APIRequest -Method GET -Endpoint "/api/processing/stats"
    if ($result.Success) {
        Write-TestResult "GET /api/processing/stats" "PASS"
    } else {
        Write-TestResult "GET /api/processing/stats" "FAIL" $result.Error
    }
    
    # Note: We skip actual pipeline start to avoid processing real emails during tests
    Write-TestResult "POST /api/processing/start" "SKIP" "Skipping to avoid processing real data"
}

# Main execution
function Main {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║     Email Helper API Endpoint Testing Suite                  ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Base URL: $BaseUrl" -ForegroundColor White
    Write-Host "  Verbose:  $Verbose" -ForegroundColor White
    Write-Host "  Skip AI:  $SkipAI" -ForegroundColor White
    Write-Host ""
    
    $startTime = Get-Date
    
    # Run test suites
    Test-HealthEndpoints
    Test-AIEndpoints
    Test-EmailEndpoints
    Test-TaskEndpoints
    Test-SettingsEndpoints
    Test-ProcessingEndpoints
    
    # Summary
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    Write-TestHeader "Test Summary"
    Write-Host ""
    Write-Host "  Total Tests:   " -NoNewline -ForegroundColor White
    Write-Host "$($script:PassCount + $script:FailCount + $script:SkipCount)" -ForegroundColor Cyan
    
    Write-Host "  ✓ Passed:      " -NoNewline -ForegroundColor Green
    Write-Host "$script:PassCount" -ForegroundColor White
    
    Write-Host "  ✗ Failed:      " -NoNewline -ForegroundColor Red
    Write-Host "$script:FailCount" -ForegroundColor White
    
    Write-Host "  ⊘ Skipped:     " -NoNewline -ForegroundColor Yellow
    Write-Host "$script:SkipCount" -ForegroundColor White
    
    Write-Host ""
    Write-Host "  Duration:      $($duration.ToString('F2')) seconds" -ForegroundColor White
    Write-Host ""
    
    # Save results to JSON
    $resultsFile = "test-results-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
    $reportData = @{
        summary = @{
            total = $script:PassCount + $script:FailCount + $script:SkipCount
            passed = $script:PassCount
            failed = $script:FailCount
            skipped = $script:SkipCount
            duration_seconds = $duration
        }
        base_url = $BaseUrl
        timestamp = (Get-Date).ToString('o')
        tests = $script:TestResults
    }
    
    $reportData | ConvertTo-Json -Depth 10 | Out-File $resultsFile -Encoding UTF8
    Write-Host "  Results saved to: $resultsFile" -ForegroundColor Gray
    Write-Host ""
    
    # Exit code
    if ($script:FailCount -gt 0) {
        Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
        Write-Host "  TESTS FAILED" -ForegroundColor Red
        Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
        exit 1
    } else {
        Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
        Write-Host "  ALL TESTS PASSED" -ForegroundColor Green
        Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
        exit 0
    }
}

# Run the tests
Main
