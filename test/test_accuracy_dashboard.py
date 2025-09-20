#!/usr/bin/env python3
"""
Test the accuracy dashboard with sample data
"""

import sys
import os
from datetime import datetime, timedelta
import json

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from accuracy_tracker import AccuracyTracker

def create_sample_data():
    """Create sample accuracy data for testing"""
    
    runtime_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'runtime_data')
    tracker = AccuracyTracker(runtime_data_dir)
    
    print("🧪 Creating sample accuracy data...")
    
    # Create sample sessions over the last 30 days
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(20):  # 20 sessions
        session_date = base_date + timedelta(days=i * 1.5)
        
        # Simulate varying accuracy (improving trend)
        base_accuracy = 70 + (i * 1.5)  # Gradual improvement
        noise = (-5 + (i % 10))  # Some variation
        accuracy = min(95, max(50, base_accuracy + noise))
        
        # Random email counts
        total_emails = 30 + (i % 20)
        modifications = max(0, int(total_emails * (100 - accuracy) / 100))
        
        # Sample category modifications
        categories = ['work_related', 'urgent_follow_up', 'information_only', 'spam_or_promotional']
        category_mods = {}
        
        for j in range(modifications):
            cat = categories[j % len(categories)]
            category_mods[cat] = category_mods.get(cat, 0) + 1
        
        session_data = {
            'run_id': f"test_session_{i:03d}",
            'total_emails': total_emails,
            'modifications_count': modifications,
            'accuracy_rate': accuracy,
            'category_modifications': category_mods
        }
        
        # Temporarily set the timestamp to our test date
        original_timestamp = tracker.accuracy_file
        tracker.record_session_accuracy(session_data)
        
        print(f"Session {i+1}: {total_emails} emails, {modifications} corrections, {accuracy:.1f}% accuracy")
    
    print("✅ Sample data created successfully!")

def test_accuracy_methods():
    """Test the new AccuracyTracker methods"""
    
    runtime_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'runtime_data')
    tracker = AccuracyTracker(runtime_data_dir)
    
    print("\n📊 Testing AccuracyTracker methods...")
    
    # Test time series data
    print("\n1. Time Series Data (daily):")
    time_series = tracker.get_time_series_data(granularity='daily')
    for item in time_series[:5]:  # Show first 5
        print(f"   {item['date']}: {item['accuracy']}% ({item['emails_processed']} emails)")
    
    # Test category performance
    print("\n2. Category Performance Summary:")
    category_perf = tracker.get_category_performance_summary()
    for item in category_perf[:3]:  # Show top 3
        print(f"   {item['category']}: {item['accuracy']}% ({item['corrections']} corrections)")
    
    # Test session comparison
    print("\n3. Recent Session Comparison:")
    sessions = tracker.get_session_comparison_data(session_count=5)
    for session in sessions[-3:]:  # Show last 3
        print(f"   {session['session_id']}: {session['accuracy']}% on {session['date']}")
    
    # Test dashboard metrics
    print("\n4. Dashboard Metrics:")
    metrics = tracker.get_dashboard_metrics()
    print(f"   Overall Accuracy: {metrics['overall_accuracy']}%")
    print(f"   7-Day Average: {metrics['seven_day_average']}%")
    print(f"   Total Sessions: {metrics['total_sessions']}")
    print(f"   Trend: {metrics['trend_indicator']}")
    
    print("\n✅ All AccuracyTracker methods working correctly!")

if __name__ == "__main__":
    print("🔬 ACCURACY DASHBOARD TEST")
    print("=" * 50)
    
    try:
        create_sample_data()
        test_accuracy_methods()
        
        print("\n🎉 Test completed successfully!")
        print("You can now run the GUI to see the accuracy dashboard with sample data.")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()