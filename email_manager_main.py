#!/usr/bin/env python3
import sys
import os

# Add the src directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')
sys.path.append(src_dir)

from unified_gui import UnifiedEmailGUI

def main():
    app = UnifiedEmailGUI()
    app.run()

if __name__ == "__main__":
    main()