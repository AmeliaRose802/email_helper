#!/usr/bin/env python3
"""
Test Dashboard Data Methods - Comprehensive test suite for new AccuracyTracker dashboard methods
"""

import sys
import os
import json
import tempfile
import shutil
from datetime import datetime, timedelta
import pandas as pd

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

try:
    from accuracy_tracker import AccuracyTracker
    
    class TestAccuracyDashboardData:
        def __init__(self):
            self.test_data_dir = None
            self.tracker = None
            
        def setup_test_environment(self):
            """Create temporary directory and test data"""
            self.test_data_dir = tempfile.mkdtemp(prefix="accuracy_test_")
            self.tracker = AccuracyTracker(self.test_data_dir)
            
            # Create sample accuracy data
            sample_data = []
            base_date = datetime.now() - timedelta(days=45)
            
            for i in range(20):  # 20 test sessions over 45 days
                session_date = base_date + timedelta(days=i*2, hours=i%12)
                
                # Vary accuracy and email counts realistically
                accuracy = 75 + (i * 1.2) + (i % 3) * 2  # Gradual improvement with some variation
                accuracy = min(98, max(60, accuracy))  # Keep within realistic bounds
                
                total_emails = 50 + (i % 10) * 5  # Vary between 50-95 emails
                modifications = int(total_emails * (100 - accuracy) / 100)
                
                # Create category modifications with realistic patterns
                category_mods = {}
                if modifications > 0:
                    # Distribute modifications across categories
                    categories = ['spam', 'work_relevant', 'team_action', 'required_personal_action', 'fyi']
                    for j in range(min(modifications, len(categories))):
                        cat = categories[j % len(categories)]
                        category_mods[cat] = category_mods.get(cat, 0) + max(1, modifications // len(categories))
                
                sample_data.append({
                    'timestamp': session_date.isoformat(),
                    'run_id': f"test_run_{i:03d}",
                    'total_emails_processed': total_emails,
                    'emails_modified': modifications,
                    'accuracy_rate': round(accuracy, 2),
                    'modifications_by_category': json.dumps(category_mods)
                })
            
            # Save test data to CSV
            df = pd.DataFrame(sample_data)
            df.to_csv(self.tracker.accuracy_file, index=False)
            
            return True
            
        def cleanup_test_environment(self):
            """Clean up temporary test directory"""
            if self.test_data_dir and os.path.exists(self.test_data_dir):
                shutil.rmtree(self.test_data_dir)
                
        def test_get_time_series_data(self):
            """Test time series data method"""
            print("🧪 Testing get_time_series_data()...")
            
            # Test 1: Basic functionality
            ts_data = self.tracker.get_time_series_data()
            assert not ts_data.empty, "Time series data should not be empty"
            assert 'accuracy_rate' in ts_data.columns, "Should have accuracy_rate column"
            assert 'session_count' in ts_data.columns, "Should have session_count column"
            print("✅ Basic time series data retrieval works")
            
            # Test 2: Daily granularity (default)
            daily_data = self.tracker.get_time_series_data(granularity='daily')
            assert not daily_data.empty, "Daily aggregation should work"
            print("✅ Daily granularity works")
            
            # Test 3: Weekly granularity
            weekly_data = self.tracker.get_time_series_data(granularity='weekly')
            assert not weekly_data.empty, "Weekly aggregation should work"
            assert len(weekly_data) <= len(daily_data), "Weekly data should have fewer or equal rows than daily"
            print("✅ Weekly granularity works")
            
            # Test 4: Date filtering
            end_date = datetime.now()
            start_date = end_date - timedelta(days=20)
            filtered_data = self.tracker.get_time_series_data(start_date=start_date, end_date=end_date)
            assert not filtered_data.empty, "Date filtering should work"
            print("✅ Date filtering works")
            
            # Test 5: Empty data handling
            empty_tracker = AccuracyTracker(tempfile.mkdtemp())
            empty_data = empty_tracker.get_time_series_data()
            assert empty_data.empty, "Should return empty DataFrame for no data"
            print("✅ Empty data handling works")
            
        def test_get_category_performance_summary(self):
            """Test category performance summary method"""
            print("\n🧪 Testing get_category_performance_summary()...")
            
            # Test 1: Basic functionality
            category_summary = self.tracker.get_category_performance_summary()
            assert isinstance(category_summary, dict), "Should return a dictionary"
            assert len(category_summary) > 0, "Should have category data"
            print("✅ Basic category summary works")
            
            # Test 2: Check data structure
            for category, stats in category_summary.items():
                assert 'accuracy_rate' in stats, "Should have accuracy_rate"
                assert 'total_corrections' in stats, "Should have total_corrections"
                assert 'sessions_involved' in stats, "Should have sessions_involved"
                assert 'category_name' in stats, "Should have category_name"
                assert 0 <= stats['accuracy_rate'] <= 100, "Accuracy should be 0-100%"
            print("✅ Category data structure is correct")
            
            # Test 3: Different time ranges
            recent_summary = self.tracker.get_category_performance_summary(days_back=7)
            month_summary = self.tracker.get_category_performance_summary(days_back=30)
            assert isinstance(recent_summary, dict), "Recent summary should work"
            assert isinstance(month_summary, dict), "Month summary should work"
            print("✅ Different time ranges work")
            
        def test_get_dashboard_metrics(self):
            """Test dashboard metrics method"""
            print("\n🧪 Testing get_dashboard_metrics()...")
            
            # Test 1: Basic functionality
            metrics = self.tracker.get_dashboard_metrics()
            assert isinstance(metrics, dict), "Should return a dictionary"
            
            required_keys = ['overall_stats', 'trend_analysis', 'category_summary', 
                           'recent_performance', 'session_statistics', 'data_quality']
            for key in required_keys:
                assert key in metrics, f"Should have {key} section"
            print("✅ Basic dashboard metrics structure is correct")
            
            # Test 2: Overall stats validation
            overall = metrics['overall_stats']
            assert overall['total_sessions'] > 0, "Should have sessions"
            assert overall['total_emails'] > 0, "Should have emails"
            assert 0 <= overall['average_accuracy'] <= 100, "Accuracy should be valid percentage"
            print("✅ Overall stats are valid")
            
            # Test 3: Date range filtering
            end_date = datetime.now()
            start_date = end_date - timedelta(days=15)
            filtered_metrics = self.tracker.get_dashboard_metrics(date_range=(start_date, end_date))
            assert isinstance(filtered_metrics, dict), "Date range filtering should work"
            print("✅ Date range filtering works")
            
        def test_export_dashboard_data(self):
            """Test export functionality"""
            print("\n🧪 Testing export_dashboard_data()...")
            
            # Test 1: CSV export
            csv_path = self.tracker.export_dashboard_data(format='csv')
            assert csv_path is not None, "CSV export should return a path"
            assert os.path.exists(csv_path), "CSV file should be created"
            assert csv_path.endswith('.csv'), "Should have .csv extension"
            
            # Verify CSV content
            exported_df = pd.read_csv(csv_path)
            assert not exported_df.empty, "Exported CSV should have data"
            assert 'timestamp' in exported_df.columns, "Should have timestamp column"
            print("✅ CSV export works")
            
            # Test 2: JSON export
            json_data = self.tracker.export_dashboard_data(format='json')
            assert json_data is not None, "JSON export should return data"
            parsed_json = json.loads(json_data)
            assert 'metadata' in parsed_json, "Should have metadata section"
            assert 'data' in parsed_json, "Should have data section"
            assert len(parsed_json['data']) > 0, "Should have actual data"
            print("✅ JSON export works")
            
            # Test 3: Date range export
            end_date = datetime.now()
            start_date = end_date - timedelta(days=10)
            filtered_csv = self.tracker.export_dashboard_data(format='csv', date_range=(start_date, end_date))
            assert filtered_csv is not None, "Filtered export should work"
            print("✅ Date range export works")
            
            # Test 4: Invalid format handling
            try:
                self.tracker.export_dashboard_data(format='xml')
                assert False, "Should raise error for invalid format"
            except ValueError:
                print("✅ Invalid format handling works")
                
        def test_get_session_comparison_data(self):
            """Test session comparison data method"""
            print("\n🧪 Testing get_session_comparison_data()...")
            
            # Test 1: Basic functionality
            comparison_data = self.tracker.get_session_comparison_data()
            assert isinstance(comparison_data, pd.DataFrame), "Should return DataFrame"
            assert not comparison_data.empty, "Should have comparison data"
            print("✅ Basic session comparison works")
            
            # Test 2: Check required columns
            required_columns = ['session_date', 'previous_session_date', 'accuracy_change', 
                              'trend_direction', 'current_accuracy', 'previous_accuracy']
            for col in required_columns:
                assert col in comparison_data.columns, f"Should have {col} column"
            print("✅ Required columns are present")
            
            # Test 3: Trend direction validation
            trend_directions = comparison_data['trend_direction'].unique()
            valid_trends = {'improving', 'declining', 'stable'}
            assert all(trend in valid_trends for trend in trend_directions), "All trends should be valid"
            print("✅ Trend directions are valid")
            
            # Test 4: Data consistency
            for _, row in comparison_data.head(3).iterrows():  # Check first few rows
                calc_change = row['current_accuracy'] - row['previous_accuracy']
                assert abs(calc_change - row['accuracy_change']) < 0.01, "Accuracy change should be consistent"
            print("✅ Data consistency checks pass")
            
        def test_edge_cases_and_error_handling(self):
            """Test edge cases and error handling"""
            print("\n🧪 Testing edge cases and error handling...")
            
            # Test 1: Empty data files
            empty_tracker = AccuracyTracker(tempfile.mkdtemp())
            
            empty_ts = empty_tracker.get_time_series_data()
            assert empty_ts.empty, "Should handle empty data gracefully"
            
            empty_categories = empty_tracker.get_category_performance_summary()
            assert empty_categories == {}, "Should return empty dict for no data"
            
            empty_metrics = empty_tracker.get_dashboard_metrics()
            assert empty_metrics['overall_stats']['total_sessions'] == 0, "Should handle empty data"
            
            print("✅ Empty data handling works")
            
            # Test 2: Malformed JSON in modifications_by_category
            malformed_data = [{
                'timestamp': datetime.now().isoformat(),
                'run_id': 'malformed_test',
                'total_emails_processed': 10,
                'emails_modified': 2,
                'accuracy_rate': 80.0,
                'modifications_by_category': 'invalid_json{'  # Malformed JSON
            }]
            
            malformed_df = pd.DataFrame(malformed_data)
            malformed_tracker = AccuracyTracker(tempfile.mkdtemp())
            malformed_df.to_csv(malformed_tracker.accuracy_file, index=False)
            
            # Should not crash with malformed JSON
            categories = malformed_tracker.get_category_performance_summary()
            assert isinstance(categories, dict), "Should handle malformed JSON gracefully"
            print("✅ Malformed JSON handling works")
            
        def run_all_tests(self):
            """Run all dashboard data tests"""
            print("🔬 DASHBOARD DATA METHODS TEST SUITE")
            print("=" * 60)
            
            try:
                self.setup_test_environment()
                
                self.test_get_time_series_data()
                self.test_get_category_performance_summary()
                self.test_get_dashboard_metrics()
                self.test_export_dashboard_data()
                self.test_get_session_comparison_data()
                self.test_edge_cases_and_error_handling()
                
                print("\n🎉 ALL DASHBOARD DATA TESTS PASSED!")
                print("✅ Time series data generation works correctly")
                print("✅ Category performance analysis is functional")
                print("✅ Dashboard metrics provide comprehensive data")
                print("✅ Export functionality supports CSV and JSON")
                print("✅ Session comparison analysis works")
                print("✅ Edge cases and error handling are robust")
                
                return True
                
            except Exception as e:
                print(f"\n❌ TEST FAILED: {e}")
                import traceback
                traceback.print_exc()
                return False
                
            finally:
                self.cleanup_test_environment()

    def test_performance_with_large_dataset():
        """Test performance with larger dataset (1000+ sessions)"""
        print("\n🧪 Testing performance with large dataset...")
        
        import time
        test_dir = tempfile.mkdtemp(prefix="perf_test_")
        tracker = AccuracyTracker(test_dir)
        
        # Create large dataset
        large_data = []
        base_date = datetime.now() - timedelta(days=365)
        
        for i in range(1000):  # 1000 sessions
            session_date = base_date + timedelta(hours=i*8.76)  # Roughly every 8.76 hours over a year
            
            large_data.append({
                'timestamp': session_date.isoformat(),
                'run_id': f"perf_test_{i:04d}",
                'total_emails_processed': 50 + (i % 50),
                'emails_modified': (i % 10) + 1,
                'accuracy_rate': 75 + (i % 20),
                'modifications_by_category': json.dumps({'spam': i % 5, 'work_relevant': i % 3})
            })
        
        df = pd.DataFrame(large_data)
        df.to_csv(tracker.accuracy_file, index=False)
        
        # Test performance
        start_time = time.time()
        
        ts_data = tracker.get_time_series_data()
        metrics = tracker.get_dashboard_metrics()
        comparison = tracker.get_session_comparison_data()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ Processed 1000 sessions in {processing_time:.2f} seconds")
        print(f"✅ Time series data: {len(ts_data)} rows")
        print(f"✅ Session comparisons: {len(comparison)} rows")
        assert processing_time < 10, "Should process 1000 sessions in under 10 seconds"
        
        # Cleanup
        shutil.rmtree(test_dir)
        
        return True

    if __name__ == "__main__":
        # Run the comprehensive test suite
        test_suite = TestAccuracyDashboardData()
        suite_passed = test_suite.run_all_tests()
        
        # Run performance test
        perf_passed = test_performance_with_large_dataset()
        
        if suite_passed and perf_passed:
            print("\n🎉 ALL TESTS PASSED - Dashboard data methods are ready for integration!")
        else:
            print("\n❌ Some tests failed - review implementation")
            
except ImportError as e:
    print(f"❌ Cannot import accuracy_tracker: {e}")
    print("Make sure pandas and numpy are installed and paths are correct.")
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()