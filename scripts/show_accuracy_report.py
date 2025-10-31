#!/usr/bin/env python3
"""
Accuracy Report - Display detailed accuracy tracking report
"""

import sys
import os

# Add parent directory to Python path to import from backend
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from backend.core.infrastructure.analytics.accuracy_tracker import AccuracyTracker


def main():
    """Display accuracy report with optional parameters"""
    print("📊 AI EMAIL CLASSIFICATION ACCURACY REPORT")
    print("=" * 60)
    
    # Set up paths - runtime_data is in project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    runtime_data_dir = os.path.join(project_root, 'runtime_data')
    
    # Initialize accuracy tracker
    accuracy_tracker = AccuracyTracker(runtime_data_dir)
    
    # Check for command line arguments
    days_back = 30  # default
    if len(sys.argv) > 1:
        try:
            days_back = int(sys.argv[1])
            print(f"Showing data for the last {days_back} days")
        except ValueError:
            print(f"Invalid days parameter '{sys.argv[1]}', using default of 30 days")
    
    # Display the report
    accuracy_tracker.display_accuracy_report(days_back)
    
    # Show category analysis
    print(f"\n{'='*60}")
    print("🔍 CATEGORY ANALYSIS")
    print(f"{'='*60}")
    
    category_analysis = accuracy_tracker.analyze_category_accuracy()
    
    if category_analysis.get('frequently_incorrect'):
        print("\n❌ Most frequently corrected AI predictions:")
        for category, count in list(category_analysis['frequently_incorrect'].items())[:5]:
            category_name = category.replace('_', ' ').title()
            print(f"   • {category_name}: {count} corrections")
    
    if category_analysis.get('user_preferences'):
        print("\n✅ Categories users prefer:")
        for category, count in list(category_analysis['user_preferences'].items())[:5]:
            category_name = category.replace('_', ' ').title()
            print(f"   • {category_name}: {count} times selected")
    
    total_corrections = category_analysis.get('total_corrections', 0)
    if total_corrections > 0:
        print(f"\n📊 Total user corrections recorded: {total_corrections}")
    else:
        print("\n📊 No user corrections recorded yet.")
        print("   Start using the email management system and make corrections")
        print("   to see accuracy tracking data here.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Report cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error generating accuracy report: {e}")
        print("Make sure you have run the email management system at least once.")
