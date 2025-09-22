import sys
import os
sys.path.append('src')

from datetime import datetime
from accuracy_tracker import AccuracyTracker

# Test if accuracy tracker can create entries
tracker = AccuracyTracker('runtime_data')

# Create a test session
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
test_data = {
    'run_id': f'test_{timestamp}',
    'total_emails': 5,
    'modifications_count': 1,
    'accuracy_rate': 80.0,
    'category_modifications': {'test_category': 1}
}

print('Recording test session...')
tracker.record_session_accuracy(test_data)
print('Test session recorded successfully!')

# Check if it was recorded
trends = tracker.get_accuracy_trends(1)
if trends:
    print(f'Latest accuracy: {trends["latest_accuracy"]}%')
    print(f'Total runs: {trends["total_runs"]}')
else:
    print('No trends data found')
