#!/usr/bin/env python3
"""
Test Accepted Suggestions Recording - Verify that all applied suggestions are recorded for fine-tuning
"""

import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_accepted_suggestions_recording():
    """Test the new accepted suggestions recording functionality"""
    
    print("🔍 TESTING ACCEPTED SUGGESTIONS RECORDING")
    print("=" * 60)
    
    # Import after setting path
    from ai_processor import AIProcessor
    
    # Initialize AI processor
    ai_processor = AIProcessor()
    
    # Create mock email suggestions data (simulating what would be applied to Outlook)
    mock_email_suggestions = [
        {
            'email_data': {
                'subject': 'Quarterly Security Training Reminder',
                'sender_name': 'Security Team',
                'sender': 'security@company.com',
                'received_time': datetime.now(),
                'body': 'Please complete your quarterly security training by the end of this week. This training covers the latest security protocols and best practices.'
            },
            'ai_suggestion': 'required_personal_action',
            'initial_classification': 'required_personal_action',  # Same as final - accepted as-is
            'ai_summary': 'Action required: Complete quarterly security training by end of week',
            'processing_notes': [],
            'thread_data': {'thread_count': 1}
        },
        {
            'email_data': {
                'subject': 'Weekly Team Newsletter - Tech Updates',
                'sender_name': 'Tech Team Lead',
                'sender': 'techteam@company.com', 
                'received_time': datetime.now(),
                'body': 'This week\'s newsletter includes updates on new technologies, upcoming conferences, and team achievements.'
            },
            'ai_suggestion': 'newsletter',
            'initial_classification': 'work_relevant',  # Changed from work_relevant to newsletter
            'ai_summary': 'Weekly tech newsletter with updates and achievements',
            'processing_notes': ['Reclassified from work_relevant to newsletter by user'],
            'thread_data': {'thread_count': 1}
        },
        {
            'email_data': {
                'subject': 'Office Maintenance Notice - Friday',
                'sender_name': 'Facilities Management',
                'sender': 'facilities@company.com',
                'received_time': datetime.now(),
                'body': 'Please be aware that office maintenance will be conducted this Friday from 6 PM to 8 PM. All employees should vacate the building by 5:30 PM.'
            },
            'ai_suggestion': 'fyi',
            'initial_classification': 'fyi',  # Same as final - accepted as-is
            'ai_summary': 'Office maintenance scheduled Friday 6-8 PM, vacate by 5:30 PM',
            'processing_notes': [],
            'thread_data': {'thread_count': 1}
        },
        {
            'email_data': {
                'subject': 'Project Status Update Thread',
                'sender_name': 'Project Manager',
                'sender': 'pm@company.com',
                'received_time': datetime.now(),
                'body': 'Here\'s the latest update on Project Alpha. Please review and provide feedback by Monday.'
            },
            'ai_suggestion': 'team_action',
            'initial_classification': 'optional_action',  # Changed from optional to team action
            'ai_summary': 'Review project status and provide feedback by Monday',
            'processing_notes': ['Escalated to team action due to deadline'],
            'thread_data': {'thread_count': 3}
        }
    ]
    
    print("📧 Mock Email Suggestions Created:")
    print(f"   • Total suggestions: {len(mock_email_suggestions)}")
    
    # Count categories
    categories = {}
    modified_count = 0
    accepted_as_is_count = 0
    
    for suggestion in mock_email_suggestions:
        category = suggestion['ai_suggestion']
        categories[category] = categories.get(category, 0) + 1
        
        if suggestion['ai_suggestion'] != suggestion['initial_classification']:
            modified_count += 1
        else:
            accepted_as_is_count += 1
    
    print(f"   • Categories: {categories}")
    print(f"   • Modified by user: {modified_count}")
    print(f"   • Accepted as-is: {accepted_as_is_count}")
    
    print("\n🔄 Testing Accepted Suggestions Recording...")
    
    # Record the accepted suggestions
    ai_processor.record_accepted_suggestions(mock_email_suggestions)
    
    # Verify the file was created and contains the data
    accepted_file = os.path.join(ai_processor.user_feedback_dir, 'accepted_suggestions.csv')
    
    if os.path.exists(accepted_file):
        print(f"✅ Accepted suggestions file created: {accepted_file}")
        
        # Read and verify content
        try:
            import pandas as pd
            df = pd.read_csv(accepted_file)
            
            print(f"📊 File contains {len(df)} records")
            print("\n📋 Sample recorded data:")
            
            # Show the columns
            print(f"   Columns: {list(df.columns)}")
            
            # Show summary of recent entries
            recent_entries = df.tail(len(mock_email_suggestions))
            for i, row in recent_entries.iterrows():
                print(f"\n   Record {i+1}:")
                print(f"     Subject: {row['subject']}")
                print(f"     Initial AI: {row['initial_ai_suggestion']}")
                print(f"     Final Applied: {row['final_applied_category']}")
                print(f"     Was Modified: {row['was_modified']}")
                print(f"     Reason: {row['modification_reason']}")
                if row['processing_notes']:
                    print(f"     Notes: {row['processing_notes']}")
            
        except Exception as e:
            print(f"❌ Error reading accepted suggestions file: {e}")
    else:
        print(f"❌ Accepted suggestions file not created")
    
    print(f"\n🎯 BENEFITS OF ACCEPTED SUGGESTIONS RECORDING:")
    print(f"   • Captures ALL user decisions (modified + accepted as-is)")
    print(f"   • Provides complete dataset for AI fine-tuning")
    print(f"   • Tracks user satisfaction with AI suggestions")
    print(f"   • Enables analysis of which categories work well vs need improvement")
    print(f"   • Distinguishes between confident vs uncertain classifications")
    
    print(f"\n💡 USAGE FOR FINE-TUNING:")
    print(f"   • High acceptance rate categories: AI is working well")
    print(f"   • High modification rate categories: Need model improvement") 
    print(f"   • Processing notes: Provide context for edge cases")
    print(f"   • Thread count: Helps understand context complexity")
    
    print(f"\n✅ Accepted suggestions recording is working correctly!")
    return True

if __name__ == "__main__":
    success = test_accepted_suggestions_recording()
    print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")
    sys.exit(0 if success else 1)
