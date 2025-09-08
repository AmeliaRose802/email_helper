#!/usr/bin/env python3
"""
Email Manager Main Entry Point - Launches the Unified GUI
This is the main entry point for the complete email management workflow
"""

import sys
import os

# Add the src directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')
sys.path.append(src_dir)

try:
    from unified_gui import UnifiedEmailGUI
    
    def main():
        """Main entry point for the unified GUI"""
        print("🤖 AI-POWERED EMAIL MANAGEMENT SYSTEM")
        print("Complete Workflow: Process → Edit → Generate Summary → View")
        print("=" * 60)
        
        try:
            app = UnifiedEmailGUI()
            app.run()
        except Exception as e:
            print(f"❌ Failed to start application: {e}")
            print("\nTroubleshooting tips:")
            print("• Ensure Microsoft Outlook is installed and running")
            print("• Check that all required Python packages are installed")
            print("• Verify Azure OpenAI credentials are configured")
            return False
        
        return True

    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nPlease ensure you're running this from the correct directory and all dependencies are installed.")
    sys.exit(1)
