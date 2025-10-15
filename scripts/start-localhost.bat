@echo off
REM start-localhost.bat
REM One-click startup script for Email Helper on Windows
REM This script checks prerequisites and starts both backend and frontend

SETLOCAL EnableDelayedExpansion

REM Set colors using ANSI escape codes (Windows 10+)
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "CYAN=[96m"
set "RESET=[0m"

REM Get timestamp for log files
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set LOG_TIMESTAMP=%mydate%_%mytime%
set LOG_DIR=runtime_data\logs
set LOG_FILE=%LOG_DIR%\startup_%LOG_TIMESTAMP%.log

REM Ensure log directory exists
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo %CYAN%========================================%RESET%
echo %CYAN%  Email Helper - Localhost Startup%RESET%
echo %CYAN%========================================%RESET%
echo.

REM Log startup attempt
echo [%date% %time%] Starting Email Helper >> "%LOG_FILE%"

REM Run prerequisite checks using PowerShell
echo %CYAN%Running prerequisite checks...%RESET%
echo [%date% %time%] Running prerequisite checks >> "%LOG_FILE%"

powershell -ExecutionPolicy Bypass -File "%~dp0check-prerequisites.ps1" -Quiet
if errorlevel 1 (
    echo.
    echo %RED%========================================%RESET%
    echo %RED%  Prerequisites check failed!%RESET%
    echo %RED%========================================%RESET%
    echo.
    echo %YELLOW%Run the following command to see details:%RESET%
    echo   powershell -ExecutionPolicy Bypass -File scripts\check-prerequisites.ps1
    echo.
    echo [%date% %time%] ERROR: Prerequisite check failed >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo %GREEN%✓ All prerequisites met%RESET%
echo [%date% %time%] Prerequisites check passed >> "%LOG_FILE%"
echo.

REM Check if ports are available
echo %CYAN%Checking port availability...%RESET%

REM Check port 8000
netstat -ano | findstr ":8000" >nul 2>&1
if not errorlevel 1 (
    echo %RED%✗ Port 8000 is already in use!%RESET%
    echo.
    echo %YELLOW%To find and kill the process:%RESET%
    echo   netstat -ano ^| findstr :8000
    echo   taskkill /PID ^<process_id^> /F
    echo.
    echo [%date% %time%] ERROR: Port 8000 in use >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo %GREEN%✓ Port 8000 is available (Backend)%RESET%

REM Check port 5173
netstat -ano | findstr ":5173" >nul 2>&1
if not errorlevel 1 (
    echo %RED%✗ Port 5173 is already in use!%RESET%
    echo.
    echo %YELLOW%To find and kill the process:%RESET%
    echo   netstat -ano ^| findstr :5173
    echo   taskkill /PID ^<process_id^> /F
    echo.
    echo [%date% %time%] ERROR: Port 5173 in use >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo %GREEN%✓ Port 5173 is available (Frontend)%RESET%
echo.

REM Check if Python dependencies are installed
echo %CYAN%Checking Python dependencies...%RESET%
python -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%Installing Python dependencies...%RESET%
    pip install -r requirements.txt >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo %RED%✗ Failed to install Python dependencies%RESET%
        echo Check the log file for details: %LOG_FILE%
        pause
        exit /b 1
    )
    echo %GREEN%✓ Python dependencies installed%RESET%
) else (
    echo %GREEN%✓ Python dependencies ready%RESET%
)

REM Check if Node.js dependencies are installed
echo %CYAN%Checking Node.js dependencies...%RESET%
if not exist "frontend\node_modules" (
    echo %YELLOW%Installing frontend dependencies...%RESET%
    cd frontend
    call npm install >> "..\%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo %RED%✗ Failed to install frontend dependencies%RESET%
        echo Check the log file for details: %LOG_FILE%
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo %GREEN%✓ Frontend dependencies installed%RESET%
) else (
    echo %GREEN%✓ Frontend dependencies ready%RESET%
)

echo.
echo %GREEN%========================================%RESET%
echo %GREEN%  Starting services...%RESET%
echo %GREEN%========================================%RESET%
echo.

REM Start backend in a new window
echo %CYAN%Starting backend on http://localhost:8000...%RESET%
echo [%date% %time%] Starting backend >> "%LOG_FILE%"
start "Email Helper - Backend" cmd /k "python run_backend.py 2>&1 | tee -a %LOG_FILE%"

REM Wait for backend to initialize
echo %YELLOW%Waiting for backend to start (5 seconds)...%RESET%
timeout /t 5 /nobreak >nul

REM Verify backend is running
echo %CYAN%Verifying backend health...%RESET%
powershell -Command "try { Invoke-RestMethod -Uri 'http://localhost:8000/health' -TimeoutSec 5 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%⚠ Backend may still be starting... Check the Backend window%RESET%
    echo [%date% %time%] WARNING: Backend health check failed >> "%LOG_FILE%"
) else (
    echo %GREEN%✓ Backend is healthy%RESET%
    echo [%date% %time%] Backend started successfully >> "%LOG_FILE%"
)

REM Start frontend in a new window
echo %CYAN%Starting frontend on http://localhost:5173...%RESET%
echo [%date% %time%] Starting frontend >> "%LOG_FILE%"
start "Email Helper - Frontend" cmd /k "cd frontend && npm run dev 2>&1 | tee -a ..\%LOG_FILE%"

echo.
echo %GREEN%========================================%RESET%
echo %GREEN%  ✓ Email Helper Started!%RESET%
echo %GREEN%========================================%RESET%
echo.
echo %CYAN%Services:%RESET%
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo.
echo %CYAN%Logs:%RESET%
echo   %LOG_FILE%
echo.
echo %YELLOW%To stop the application:%RESET%
echo   1. Press Ctrl+C in each window, OR
echo   2. Run: scripts\stop-all.bat
echo.
echo [%date% %time%] Startup complete >> "%LOG_FILE%"

REM Open frontend in default browser after a short delay
timeout /t 3 /nobreak >nul
start http://localhost:5173

pause
