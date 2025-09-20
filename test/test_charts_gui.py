#!/usr/bin/env python3
"""
Simple test for the accuracy dashboard GUI components
"""

import sys
import os
import tkinter as tk
from tkinter import ttk

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from accuracy_tracker import AccuracyTracker
from components.accuracy_charts import AccuracyChartsComponent

def test_charts_component():
    """Test the AccuracyChartsComponent with sample data"""
    
    print("🧪 Testing AccuracyChartsComponent...")
    
    runtime_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'runtime_data')
    tracker = AccuracyTracker(runtime_data_dir)
    
    # Create a simple test window
    root = tk.Tk()
    root.title("Accuracy Charts Test")
    root.geometry("1000x700")
    
    # Create notebook for charts
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Initialize charts component
    charts = AccuracyChartsComponent(root, tracker)
    
    # Test each chart type
    try:
        # Trend Chart Tab
        trend_frame = ttk.Frame(notebook)
        notebook.add(trend_frame, text="📈 Trend Chart")
        charts.create_trend_chart(trend_frame, 'daily')
        
        # Category Performance Tab
        category_frame = ttk.Frame(notebook)
        notebook.add(category_frame, text="📊 Category Performance")
        charts.create_category_performance_chart(category_frame)
        
        # Session Comparison Tab
        session_frame = ttk.Frame(notebook)
        notebook.add(session_frame, text="🔄 Session Comparison")
        charts.create_session_comparison_chart(session_frame)
        
        # Summary Gauges Tab
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="📊 Summary Metrics")
        
        # Configure grid for gauges
        for i in range(2):
            summary_frame.columnconfigure(i, weight=1)
        
        charts.create_summary_gauges(summary_frame)
        
        print("✅ All charts created successfully!")
        print("📋 Charts window opened - close it to continue")
        
        # Start the GUI
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Error creating charts: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔬 CHARTS COMPONENT TEST")
    print("=" * 40)
    
    try:
        test_charts_component()
        print("🎉 Charts test completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()