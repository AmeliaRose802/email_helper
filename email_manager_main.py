#!/usr/bin/env python3
"""Email Helper Main Application Entry Point.

This is the main entry point for the Email Helper application. It initializes
the service factory, validates configuration, and launches the GUI interface.

The application uses dependency injection through the ServiceFactory to create
all necessary components with proper dependencies and configuration.
"""

import sys
import os
import logging

# Add the src directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')
sys.path.append(src_dir)

import tkinter as tk
from core.service_factory import ServiceFactory
from core.config import config
from email_helper_app import EmailHelperApp


def setup_logging():
    """Configure logging for the application."""
    log_level = getattr(logging, config.get('logging.level', 'INFO').upper())
    log_format = config.get('logging.format')
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(config.get_storage_path('email_helper.log'), encoding='utf-8')
        ] if config.get('logging.file_enabled') else [logging.StreamHandler(sys.stdout)]
    )


def validate_configuration():
    """Validate that essential configuration is present."""
    issues = config.validate()
    if issues:
        print("⚠️  Configuration Issues:")
        for issue in issues:
            print(f"   - {issue}")
        print("\nPlease check your configuration and environment variables.")
        return False
    return True


def main():
    """Main application entry point - now using clean MVC architecture."""
    print("🚀 Starting Email Helper (MVC Architecture)...")
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Validate configuration
    if not validate_configuration():
        logger.error("Configuration validation failed")
        sys.exit(1)
    
    try:
        # Create Tkinter root window
        root = tk.Tk()
        
        # Create and run the main application with MVC architecture
        app = EmailHelperApp(root)
        logger.info("Email Helper started successfully with MVC architecture")
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()