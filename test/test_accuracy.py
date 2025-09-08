#!/usr/bin/env python3
"""
Test Accuracy Tracking - Simple test to verify accuracy tracking functionality
"""

import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

try:
    from accuracy_tracker import AccuracyTracker
    
    def test_accuracy_calculation():
        """Test the accuracy calculation logic"""
        print("🧪 Testing accuracy calculation...")
        
        # Test case 1: No modifications (100% accuracy)
        total_emails = 10
        modifications = []
        tracker = AccuracyTracker("./runtime_data")
        accuracy = tracker.calculate_accuracy_for_session(total_emails, modifications)
        print(f"Test 1 - No corrections: {accuracy}% (expected: 100%)")
        
        # Test case 2: Some modifications
        modifications = [{"old": "spam", "new": "work"}, {"old": "work", "new": "spam"}]
        accuracy = tracker.calculate_accuracy_for_session(total_emails, modifications)
        print(f"Test 2 - 2/10 corrections: {accuracy}% (expected: 80%)")
        
        # Test case 3: All modifications (0% accuracy)
        modifications = [{"old": "spam", "new": "work"}] * total_emails
        accuracy = tracker.calculate_accuracy_for_session(total_emails, modifications)
        print(f"Test 3 - All corrections: {accuracy}% (expected: 0%)")
        
        print("✅ Accuracy calculation tests completed")
    
    def show_current_accuracy():
        """Show current accuracy if data exists"""
        print("\n📊 Current Accuracy Data:")
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        runtime_data_dir = os.path.join(script_dir, 'runtime_data')
        
        tracker = AccuracyTracker(runtime_data_dir)
        tracker.display_accuracy_report(7)  # Last 7 days
    
    if __name__ == "__main__":
        print("🔬 ACCURACY TRACKING TEST")
        print("=" * 40)
        
        test_accuracy_calculation()
        show_current_accuracy()

except ImportError as e:
    print(f"❌ Cannot import accuracy_tracker: {e}")
    print("This might be due to missing pandas dependency or path issues.")
    print("Try running: pip install pandas")
except Exception as e:
    print(f"❌ Error during testing: {e}")
