@echo off
REM Startup script for Email Helper application (Windows)
REM This script handles the startup sequence and dependency checks

echo 🚀 Starting Email Helper Application...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH
    pause
    exit /b 1
)

REM Check Python dependencies
echo 📦 Checking Python dependencies...
python -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo Installing Python dependencies...
    pip install fastapi uvicorn
)

REM Install Node.js dependencies if needed
echo 📦 Checking Node.js dependencies...
if not exist "node_modules" (
    echo Installing Node.js dependencies...
    npm install
)

if not exist "frontend\node_modules" (
    echo Installing Frontend dependencies...
    cd frontend
    npm install
    cd ..
)

REM Start the application
echo 🚀 Starting both frontend and backend...
npm start