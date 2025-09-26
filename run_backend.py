#!/usr/bin/env python3
"""Entry point for running the FastAPI backend server."""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from backend.main import app, settings
    import uvicorn
    
    print(f"🌟 Starting {settings.app_name} v{settings.app_version}")
    print(f"🔧 Debug mode: {settings.debug}")
    print(f"🌐 Server: {settings.host}:{settings.port}")
    print(f"📋 API docs: http://{settings.host}:{settings.port}/docs")
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )