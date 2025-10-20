#!/usr/bin/env python3
"""Entry point for running the FastAPI backend server."""

import sys
import os
import io

# Configure stdout/stderr for UTF-8 to handle Unicode characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from backend.main import app, settings
    import uvicorn
    
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Debug mode: {settings.debug}")
    print(f"Server: {settings.host}:{settings.port}")
    print(f"API docs: http://{settings.host}:{settings.port}/docs")
    
    if settings.debug:
        # Use module string for reload
        uvicorn.run(
            "backend.main:app",
            host=settings.host,
            port=settings.port,
            reload=True,
            log_level="info"
        )
    else:
        # Use app object for production
        uvicorn.run(
            app,
            host=settings.host,
            port=settings.port,
            reload=False,
            log_level="info"
        )