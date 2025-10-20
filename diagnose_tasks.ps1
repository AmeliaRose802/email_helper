# Task Visibility Diagnostic Script
Write-Host "🔍 Diagnosing Task Visibility Issue..." -ForegroundColor Cyan
Write-Host ""

# Check database tasks
Write-Host "📊 Checking Database..." -ForegroundColor Yellow
python -c "import sqlite3; conn = sqlite3.connect('runtime_data/email_helper_history.db'); cursor = conn.cursor(); cursor.execute('SELECT id, title, category, status, user_id FROM tasks ORDER BY id DESC LIMIT 10'); tasks = cursor.fetchall(); print(f'Total tasks in database: {len(tasks)}'); print('\nRecent tasks:'); [print(f'  Task {t[0]}: {t[1][:70]} | Category: {t[2]} | Status: {t[3]} | User: {t[4]}') for t in tasks]; conn.close()"

Write-Host ""
Write-Host "🌐 Testing Backend API..." -ForegroundColor Yellow
try {
    $ApiResponse = Invoke-RestMethod "http://localhost:8000/api/tasks" -TimeoutSec 5
    Write-Host "✅ Backend API is responding" -ForegroundColor Green
    Write-Host "   Total tasks from API: $($ApiResponse.tasks.Count)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   Tasks returned by API:" -ForegroundColor Cyan
    foreach ($task in $ApiResponse.tasks) {
        Write-Host "     - ID: $($task.id) | Title: $($task.title.Substring(0, [Math]::Min(60, $task.title.Length)))" -ForegroundColor Gray
        Write-Host "       Category: $($task.category) | Status: $($task.status) | Priority: $($task.priority)" -ForegroundColor DarkGray
    }
} catch {
    Write-Host "❌ Backend API is not responding" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔧 Recommended Actions:" -ForegroundColor Green
Write-Host "   1. If backend shows tasks but frontend doesn't:" -ForegroundColor Cyan
Write-Host "      → Restart the Electron app to clear cache" -ForegroundColor Gray
Write-Host "      → Run: cd electron && .\start-app.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "   2. If tasks are in database but not in API:" -ForegroundColor Cyan
Write-Host "      → Check backend logs for errors" -ForegroundColor Gray
Write-Host ""
Write-Host "   3. If no tasks in database:" -ForegroundColor Cyan
Write-Host "      → Re-run task extraction from Email List page" -ForegroundColor Gray
Write-Host "      → Click 'Approve All' button" -ForegroundColor Gray
Write-Host ""

Write-Host "📝 Quick Restart Command:" -ForegroundColor Cyan
Write-Host "   Get-Process electron,python,node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue; cd electron; .\start-app.ps1" -ForegroundColor Yellow
Write-Host ""
