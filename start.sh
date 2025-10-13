#!/usr/bin/env bash
# Startup script for Email Helper application
# This script handles the startup sequence and dependency checks

echo "🚀 Starting Email Helper Application..."

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed or not in PATH"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed or not in PATH"
    exit 1
fi

# Install Python dependencies if needed
echo "📦 Checking Python dependencies..."
python -c "import fastapi, uvicorn" 2>/dev/null || {
    echo "Installing Python dependencies..."
    pip install fastapi uvicorn
}

# Install Node.js dependencies if needed
echo "📦 Checking Node.js dependencies..."
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "Installing Frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Start the application
echo "🚀 Starting both frontend and backend..."
npm start