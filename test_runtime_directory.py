#!/usr/bin/env python3
"""
Test script to verify runtime directory functionality
"""
import os
import sys
from datetime import datetime

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from summary_generator import SummaryGenerator

def test_directory_creation():
    """Test that the runtime directory structure is created correctly"""
    sg = SummaryGenerator()
    
    # Mock data for testing
    test_sections = {
        'required_actions': [
            {
                'subject': 'Test Email',
                'sender': 'Test Sender',
                'due_date': 'Today',
                'explanation': 'Test explanation',
                'action_required': 'Test action',
                'links': []
            }
        ],
        'team_actions': [],
        'optional_actions': [],
        'job_listings': [],
        'optional_events': []
    }
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # This should create the directory and save the file
        result = sg.save_focused_summary(test_sections, timestamp)
        
        print(f"✅ Success! File saved to: {result}")
        
        # Verify the file exists
        if os.path.exists(result):
            print(f"✅ File verification: File exists at {result}")
            
            # Check the directory structure
            expected_dir = os.path.join(os.path.dirname(__file__), 'runtime_data', 'ai_summaries')
            if os.path.exists(expected_dir):
                print(f"✅ Directory verification: {expected_dir} exists")
            else:
                print(f"❌ Directory verification failed: {expected_dir} does not exist")
                
        else:
            print(f"❌ File verification failed: {result} does not exist")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing runtime directory functionality...")
    test_directory_creation()
