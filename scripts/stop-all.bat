@echo off
REM stop-all.bat
REM Graceful shutdown script for Email Helper
REM Stops all running Email Helper processes and cleans up ports

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
set LOG_FILE=%LOG_DIR%\shutdown_%LOG_TIMESTAMP%.log

REM Ensure log directory exists
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo %CYAN%========================================%RESET%
echo %CYAN%  Email Helper - Shutdown%RESET%
echo %CYAN%========================================%RESET%
echo.

echo [%date% %time%] Starting shutdown process >> "%LOG_FILE%"

REM Function to kill process on port
set "PORTS=8000 5173"
set "PORT_NAMES=Backend Frontend"

echo %CYAN%Checking for running processes...%RESET%
echo.

set INDEX=0
for %%P in (%PORTS%) do (
    set /A INDEX+=1
    set "PORT=%%P"
    
    REM Get port name
    for /f "tokens=!INDEX!" %%N in ("%PORT_NAMES%") do set "PORT_NAME=%%N"
    
    echo %CYAN%Checking port !PORT! ^(!PORT_NAME!^)...%RESET%
    echo [%date% %time%] Checking port !PORT! >> "%LOG_FILE%"
    
    REM Find process using the port
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":!PORT! "') do (
        set "PID=%%a"
        
        REM Check if PID is valid (numeric)
        echo !PID! | findstr /r "^[0-9][0-9]*$" >nul
        if not errorlevel 1 (
            REM Get process name
            for /f "tokens=1" %%b in ('tasklist /FI "PID eq !PID!" /NH 2^>nul') do (
                set "PROCESS_NAME=%%b"
            )
            
            if defined PROCESS_NAME (
                echo   %YELLOW%Found process: !PROCESS_NAME! ^(PID: !PID!^)%RESET%
                echo [%date% %time%] Found process !PROCESS_NAME! (PID: !PID!) on port !PORT! >> "%LOG_FILE%"
                
                REM Attempt graceful termination first
                echo   %CYAN%Attempting graceful shutdown...%RESET%
                taskkill /PID !PID! >nul 2>&1
                
                REM Wait a moment
                timeout /t 2 /nobreak >nul
                
                REM Check if still running
                tasklist /FI "PID eq !PID!" 2>nul | find "!PID!" >nul
                if not errorlevel 1 (
                    echo   %YELLOW%Process still running, forcing termination...%RESET%
                    taskkill /F /PID !PID! >nul 2>&1
                    echo [%date% %time%] Forced termination of PID !PID! >> "%LOG_FILE%"
                )
                
                echo   %GREEN%✓ Process terminated%RESET%
                echo [%date% %time%] Successfully terminated PID !PID! >> "%LOG_FILE%"
            )
        )
    )
    
    REM Verify port is now free
    netstat -ano | findstr ":!PORT!" >nul 2>&1
    if errorlevel 1 (
        echo   %GREEN%✓ Port !PORT! is now free%RESET%
    ) else (
        echo   %YELLOW%⚠ Port !PORT! may still be in use%RESET%
    )
    echo.
)

REM Close any Email Helper windows by title
echo %CYAN%Closing Email Helper windows...%RESET%
echo [%date% %time%] Closing Email Helper windows >> "%LOG_FILE%"

REM Kill any remaining processes by window title
taskkill /FI "WINDOWTITLE eq Email Helper - Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Email Helper - Frontend*" /F >nul 2>&1

REM Kill any Python/Node processes that might be Email Helper related
echo %CYAN%Checking for orphaned processes...%RESET%

REM Check for uvicorn processes
tasklist | findstr /I "uvicorn" >nul 2>&1
if not errorlevel 1 (
    echo %YELLOW%Found uvicorn processes, terminating...%RESET%
    taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" >nul 2>&1
    echo [%date% %time%] Terminated uvicorn processes >> "%LOG_FILE%"
)

REM Check for Vite dev server processes
tasklist | findstr /I "vite" >nul 2>&1
if not errorlevel 1 (
    echo %YELLOW%Found Vite processes, terminating...%RESET%
    taskkill /F /IM node.exe /FI "WINDOWTITLE eq *vite*" >nul 2>&1
    echo [%date% %time%] Terminated Vite processes >> "%LOG_FILE%"
)

echo.
echo %GREEN%========================================%RESET%
echo %GREEN%  ✓ Shutdown Complete%RESET%
echo %GREEN%========================================%RESET%
echo.
echo %CYAN%All Email Helper processes have been stopped.%RESET%
echo %CYAN%Ports 8000 and 5173 should now be available.%RESET%
echo.
echo %CYAN%Log file:%RESET% %LOG_FILE%
echo.
echo [%date% %time%] Shutdown process complete >> "%LOG_FILE%"

REM Optional: Clean up old log files (keep last 10)
echo %CYAN%Cleaning up old log files...%RESET%
for /f "skip=10 delims=" %%F in ('dir /b /o-d "%LOG_DIR%\*.log" 2^>nul') do (
    del /q "%LOG_DIR%\%%F" >nul 2>&1
)

echo %GREEN%✓ Cleanup complete%RESET%
echo.
pause
