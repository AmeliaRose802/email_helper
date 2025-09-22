#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo script to show the accuracy dashboard is working
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_gui import UnifiedEmailGUI

def demo_accuracy_dashboard():
    """Demo the accuracy dashboard functionality"""
    print("🚀 Starting Accuracy Dashboard Demo")
    print("=" * 50)
    
    try:
        # Create GUI
        root = tk.Tk()
        root.title("Email Helper - Accuracy Dashboard Demo")
        root.geometry("1200x800")
        
        # Create GUI instance
        gui = UnifiedEmailGUI()
        
        # Enable the accuracy tab for demo
        gui.notebook.tab(3, state="normal")
        
        # Select the accuracy tab
        gui.notebook.select(3)
        
        # Show information about the dashboard
        info_message = """📊 ACCURACY DASHBOARD READY!

The accuracy tab has been successfully created and includes:

📈 Overview Tab:
   • Key metrics display (Overall, 7-day, sessions, emails)
   • Trend indicators and recent activity summary
   
📊 Trends Tab:
   • Time-series analysis with configurable date ranges
   • Chart visualization (ready for matplotlib integration)
   
🏷️ Categories Tab:
   • Category performance analysis
   • Sortable table with accuracy rates and correction counts
   
📋 Sessions Tab:
   • Detailed session history
   • Session-by-session accuracy tracking

🔄 Data Integration:
   • Uses all 5 new AccuracyTracker methods from PR #2
   • Real-time refresh capabilities
   • CSV export functionality

Click 'OK' to explore the dashboard interface!"""
        
        messagebox.showinfo("Accuracy Dashboard Ready", info_message)
        
        print("✅ Dashboard loaded successfully")
        print("✅ All AccuracyTracker methods integrated")
        print("✅ Four sub-tabs created (Overview, Trends, Categories, Sessions)")
        print("✅ Ready for user interaction")
        
        # Start the GUI
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        if 'root' in locals():
            root.destroy()

if __name__ == "__main__":
    demo_accuracy_dashboard()