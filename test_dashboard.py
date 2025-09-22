import sys
import os
sys.path.append('src')

# Test if the dashboard can load existing data
script_dir = os.path.join(os.getcwd(), 'src')
project_root = os.path.dirname(script_dir)
runtime_base_dir = os.path.join(project_root, 'runtime_data')

from accuracy_tracker import AccuracyTracker
tracker = AccuracyTracker(runtime_base_dir)

print('Testing dashboard data loading...')
trends = tracker.get_accuracy_trends(30)
if trends:
    print(f'Data found: {trends["total_runs"]} sessions, {trends["average_accuracy"]}% avg accuracy')
    print(f'Latest: {trends["latest_accuracy"]}%')
else:
    print('No data found')

# Test dashboard metrics
metrics = tracker.get_dashboard_metrics()
print(f'Dashboard metrics total sessions: {metrics["overall_stats"]["total_sessions"]}')
