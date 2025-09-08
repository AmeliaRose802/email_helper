#!/usr/bin/env python3
"""
Backward Compatibility Wrapper for Original email_manager.py
This maintains the original interface while using the new modular system.
"""

import sys
import os

# Add the scripts directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Import the new main system
from email_manager_main import EmailManagementSystem, main

# For backward compatibility, expose the main function
if __name__ == "__main__":
    print("🔄 Using new modular email management system...")
    print("   (This maintains compatibility with the original email_manager.py)")
    print()
    main()
