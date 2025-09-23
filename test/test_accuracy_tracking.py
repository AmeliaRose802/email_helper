#!/usr/bin/env python3
"""
Test Suite for Accuracy Tracking - Block 4 Implementation

Tests for the new AccuracyTracker methods:
- calculate_running_accuracy()
- persist_accuracy_metrics()
"""

import sys
import os
import tempfile
import shutil
import json
from datetime import datetime, timedelta

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

try:
    from accuracy_tracker import AccuracyTracker
    
    def test_calculate_running_accuracy():
        """Test calculate_running_accuracy method"""
        print("🧪 Testing calculate_running_accuracy()...")
        
        test_dir = tempfile.mkdtemp(prefix="accuracy_test_")
        
        try:
            tracker = AccuracyTracker(test_dir)
            
            # Test with no data
            result = tracker.calculate_running_accuracy()
            
            # Verify structure
            expected_fields = ['last_7_days', 'last_30_days', 'current_trend', 
                             'total_sessions_7d', 'total_sessions_30d', 
                             'total_emails_7d', 'total_emails_30d']
            
            for field in expected_fields:
                assert field in result, f"Missing field: {field}"
            
            # Verify default values
            assert result['last_7_days'] == 0.0
            assert result['last_30_days'] == 0.0
            assert result['current_trend'] == 'no_data'
            
            print("  ✅ calculate_running_accuracy() works correctly")
            return True
            
        finally:
            shutil.rmtree(test_dir)
    
    def test_persist_accuracy_metrics():
        """Test persist_accuracy_metrics method"""
        print("🧪 Testing persist_accuracy_metrics()...")
        
        test_dir = tempfile.mkdtemp(prefix="persistence_test_")
        
        try:
            tracker = AccuracyTracker(test_dir)
            
            # Test with default metrics
            result = tracker.persist_accuracy_metrics()
            assert result == True
            
            # Test with custom metrics
            custom_metrics = {
                'last_7_days': 85.5,
                'last_30_days': 82.1,
                'current_trend': 'improving'
            }
            
            result = tracker.persist_accuracy_metrics(custom_metrics)
            assert result == True
            
            # Verify file was created
            long_term_dir = os.path.join(test_dir, 'user_feedback', 'long_term_metrics')
            assert os.path.exists(long_term_dir)
            
            current_month = datetime.now().strftime('%Y_%m')
            metrics_file = os.path.join(long_term_dir, f'accuracy_metrics_{current_month}.jsonl')
            assert os.path.exists(metrics_file)
            
            # Verify file content
            with open(metrics_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) >= 2  # Should have at least 2 entries
                
                # Check last line (custom metrics)
                last_entry = json.loads(lines[-1].strip())
                assert 'timestamp' in last_entry
                assert 'metrics' in last_entry
                assert last_entry['metrics']['last_7_days'] == 85.5
            
            print("  ✅ persist_accuracy_metrics() works correctly")
            return True
            
        finally:
            shutil.rmtree(test_dir)
    
    def test_integration():
        """Test integration between running accuracy and persistence"""
        print("🧪 Testing accuracy tracking integration...")
        
        test_dir = tempfile.mkdtemp(prefix="integration_test_")
        
        try:
            tracker = AccuracyTracker(test_dir)
            
            # Calculate running accuracy
            metrics = tracker.calculate_running_accuracy()
            
            # Persist the metrics
            result = tracker.persist_accuracy_metrics(metrics)
            assert result == True
            
            # Verify persistence
            long_term_dir = os.path.join(test_dir, 'user_feedback', 'long_term_metrics')
            current_month = datetime.now().strftime('%Y_%m')
            metrics_file = os.path.join(long_term_dir, f'accuracy_metrics_{current_month}.jsonl')
            
            with open(metrics_file, 'r') as f:
                entry = json.loads(f.readline().strip())
                assert entry['metrics']['current_trend'] == 'no_data'
            
            print("  ✅ Integration between methods works correctly")
            return True
            
        finally:
            shutil.rmtree(test_dir)
    
    def main():
        print("🚀 ACCURACY TRACKING TESTS")
        print("=" * 40)
        
        tests = [
            test_calculate_running_accuracy,
            test_persist_accuracy_metrics,
            test_integration
        ]
        
        passed = 0
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"  ❌ {test.__name__} failed: {e}")
        
        print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
        
        if passed == len(tests):
            print("🎉 ALL ACCURACY TRACKING TESTS PASSED!")
        else:
            print("⚠️ Some tests failed")
    
    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()