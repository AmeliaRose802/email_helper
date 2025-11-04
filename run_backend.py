"""Backend server startup script for Email Helper.

This script starts the FastAPI backend server for the Email Helper application.
It's designed to be called by the Electron main process or run standalone for development.
"""

import sys
import os
from pathlib import Path

# Add project paths to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "backend"))

# Configure environment
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')


def main():
    """Start the FastAPI backend server."""
    import uvicorn
    from backend.main import app
    
    # Get configuration from environment or use defaults
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    
    print(f"[Backend] Starting FastAPI server...")
    print(f"[Backend] Host: {host}")
    print(f"[Backend] Port: {port}")
    print(f"[Backend] Debug: {debug}")
    
    try:
        # Start uvicorn server
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info" if debug else "warning",
            access_log=debug,
            reload=False,  # Don't reload in production
        )
    except KeyboardInterrupt:
        print("\n[Backend] Received keyboard interrupt, shutting down...")
    except Exception as e:
        print(f"[Backend] Error: {e}")
        sys.exit(1)
    finally:
        print("[Backend] Shutdown complete")

if __name__ == "__main__":
    main()
