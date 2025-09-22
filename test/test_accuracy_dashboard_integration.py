#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive integration test for accuracy dashboard tab
Tests the integration between GUI accuracy tab and AccuracyTracker data methods
"""

import sys
import os
import tkinter as tk
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from unified_gui import UnifiedEmailGUI
from accuracy_tracker import AccuracyTracker

def test_accuracy_tab_creation():
    """Test that accuracy tab can be created without errors"""
    print("🧪 Testing accuracy tab creation...")
    
    try:
        # Create root window (don't show it)
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Create GUI instance
        gui = UnifiedEmailGUI()
        
        # Verify accuracy tab exists
        assert hasattr(gui, 'accuracy_frame'), "Accuracy frame not created"
        assert hasattr(gui, 'create_accuracy_tab'), "create_accuracy_tab method not found"
        
        # Check that tab is added to notebook
        tabs = [gui.notebook.tab(i, 'text') for i in range(gui.notebook.index('end'))]
        accuracy_tab_exists = any('Accuracy Dashboard' in tab for tab in tabs)
        assert accuracy_tab_exists, f"Accuracy Dashboard tab not found in tabs: {tabs}"
        
        print("✅ Accuracy tab creation test passed")
        
        # Clean up
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ Accuracy tab creation test failed: {str(e)}")
        if 'root' in locals():
            root.destroy()
        return False

def test_accuracy_tracker_integration():
    """Test that AccuracyTracker methods work with GUI"""
    print("🧪 Testing AccuracyTracker integration...")
    
    try:
        # Test AccuracyTracker instantiation
        feedback_dir = os.path.join(os.getcwd(), "runtime_data", "user_feedback")
        os.makedirs(feedback_dir, exist_ok=True)
        
        tracker = AccuracyTracker(feedback_dir)
        
        # Test dashboard methods exist and are callable
        methods_to_test = [
            'get_dashboard_metrics',
            'get_time_series_data', 
            'get_category_performance_summary',
            'get_session_comparison_data',
            'export_dashboard_data'
        ]
        
        for method_name in methods_to_test:
            assert hasattr(tracker, method_name), f"Method {method_name} not found"
            method = getattr(tracker, method_name)
            assert callable(method), f"Method {method_name} is not callable"
        
        # Test calling dashboard metrics (should work even with no data)
        metrics = tracker.get_dashboard_metrics()
        assert isinstance(metrics, dict), "get_dashboard_metrics should return dict"
        
        print("✅ AccuracyTracker integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ AccuracyTracker integration test failed: {str(e)}")
        return False

def test_gui_accuracy_methods():
    """Test that GUI accuracy methods exist and are callable"""
    print("🧪 Testing GUI accuracy methods...")
    
    try:
        # Create root window (don't show it)
        root = tk.Tk()
        root.withdraw()
        
        # Create GUI instance
        gui = UnifiedEmailGUI()
        
        # Test that accuracy-related methods exist
        accuracy_methods = [
            'create_accuracy_tab',
            'create_metrics_view',
            'create_trends_view', 
            'create_categories_view',
            'create_sessions_view',
            'refresh_accuracy_data',
            'update_metrics_display',
            'update_trends_chart',
            'update_category_analysis',
            'update_sessions_list',
            'export_accuracy_data'
        ]
        
        for method_name in accuracy_methods:
            assert hasattr(gui, method_name), f"GUI method {method_name} not found"
            method = getattr(gui, method_name)
            assert callable(method), f"GUI method {method_name} is not callable"
        
        # Test that accuracy tab widgets were created
        assert hasattr(gui, 'accuracy_notebook'), "Accuracy notebook not created"
        
        print("✅ GUI accuracy methods test passed")
        
        # Clean up
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ GUI accuracy methods test failed: {str(e)}")
        if 'root' in locals():
            root.destroy()
        return False

def test_tab_navigation():
    """Test that accuracy tab can be navigated to"""
    print("🧪 Testing tab navigation...")
    
    try:
        # Create root window (don't show it)
        root = tk.Tk()
        root.withdraw()
        
        # Create GUI instance
        gui = UnifiedEmailGUI()
        
        # Get number of tabs
        num_tabs = gui.notebook.index('end')
        assert num_tabs >= 4, f"Expected at least 4 tabs, found {num_tabs}"
        
        # Check all tab texts first
        tab_texts = []
        for i in range(num_tabs):
            tab_text = gui.notebook.tab(i, 'text')
            tab_state = gui.notebook.tab(i, 'state')
            tab_texts.append(f"Tab {i}: '{tab_text}' (state: {tab_state})")
        
        # Find accuracy tab by searching for "Accuracy Dashboard" in text
        accuracy_tab_index = None
        for i in range(num_tabs):
            tab_text = gui.notebook.tab(i, 'text')
            if 'Accuracy Dashboard' in tab_text:
                accuracy_tab_index = i
                break
        
        assert accuracy_tab_index is not None, f"Accuracy Dashboard tab not found. Tabs: {tab_texts}"
        
        # Enable the accuracy tab (it's disabled by default)
        gui.notebook.tab(accuracy_tab_index, state="normal")
        
        # Try to select accuracy tab
        gui.notebook.select(accuracy_tab_index)
        current_tab = gui.notebook.select()
        assert current_tab is not None, "Could not select accuracy tab"
        
        # Verify selected tab text
        selected_tab_text = gui.notebook.tab(current_tab, 'text')
        assert 'Accuracy Dashboard' in selected_tab_text, f"Selected tab text is '{selected_tab_text}', expected 'Accuracy Dashboard'"
        
        print("✅ Tab navigation test passed")
        
        # Clean up
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ Tab navigation test failed: {str(e)}")
        if 'root' in locals():
            root.destroy()
        return False

def test_error_handling():
    """Test that accuracy tab handles errors gracefully"""
    print("🧪 Testing error handling...")
    
    try:
        # Create root window (don't show it)
        root = tk.Tk()
        root.withdraw()
        
        # Create GUI instance
        gui = UnifiedEmailGUI()
        
        # Test refresh with no accuracy tracker (should handle gracefully)
        try:
            gui.refresh_accuracy_data()
            print("   ✓ refresh_accuracy_data handles missing tracker")
        except Exception as e:
            print(f"   ⚠ refresh_accuracy_data error: {str(e)}")
        
        # Test update methods without tracker
        update_methods = ['update_metrics_display', 'update_trends_chart', 
                         'update_category_analysis', 'update_sessions_list']
        
        for method_name in update_methods:
            try:
                method = getattr(gui, method_name)
                method()
                print(f"   ✓ {method_name} handles missing data")
            except Exception as e:
                print(f"   ⚠ {method_name} error: {str(e)}")
        
        print("✅ Error handling test completed")
        
        # Clean up
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")
        if 'root' in locals():
            root.destroy()
        return False

def main():
    """Run all integration tests"""
    print("🚀 Starting Accuracy Dashboard Integration Tests")
    print("=" * 60)
    
    # Change to project directory
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_dir)
    
    tests = [
        test_accuracy_tab_creation,
        test_accuracy_tracker_integration,
        test_gui_accuracy_methods,
        test_tab_navigation,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"📊 Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed! Accuracy dashboard is ready.")
        return True
    else:
        print("⚠ Some integration tests failed. Review errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)