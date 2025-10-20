@echo off
REM Email Helper Desktop App Launcher
REM This script builds the frontend and launches the Electron desktop app

echo ========================================
echo Email Helper Desktop App Launcher
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check Node.js version
echo Checking Node.js version...
node --version
echo.

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org/
    pause
    exit /b 1
)

echo Checking Python version...
python --version
echo.

REM Check if Electron is installed
if not exist "electron\node_modules" (
    echo Installing Electron dependencies...
    cd electron
    call npm install
    cd ..
    echo.
)

REM Build frontend
echo Building frontend...
cd frontend
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
    echo.
)

echo Building React app...
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Frontend build failed
    cd ..
    pause
    exit /b 1
)
cd ..
echo Frontend built successfully!
echo.

REM Launch Electron
echo Launching Email Helper Desktop App...
cd electron
call npm start

REM Cleanup on exit
cd ..
echo.
echo Email Helper closed.
pause
