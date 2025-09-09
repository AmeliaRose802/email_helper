#!/usr/bin/env python3
"""
Simple test to compare old vs improved email classification prompts
"""
import sys
import os

# Add parent directory to path so we can import from src
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))

def test_sample_emails():
    """Test a few sample emails with both old and improved prompts"""
    
    # Sample test cases based on common error patterns
    test_cases = [
        {
            'name': 'Team Action Confusion',
            'subject': '[Reminder] Kr Semester Planning: filing an ask on E+P H+S',
            'sender': 'Ayelet Bar Am',
            'body': 'Hello partners, This is a final reminder for filing dependencies for the upcoming Kr semester. Last date is September 8, 2025. Thanks, Ayelet',
            'expected': 'team_action',  # Not required_personal_action
            'explanation': 'This is team work, not personal work'
        },
        {
            'name': 'Newsletter Spam',
            'subject': 'Re: Titan AZAP & Decom Mainstreamed in Mooncake & Fairfax', 
            'sender': 'Arun Kishan',
            'body': 'Congratulations! Great to see the buildout and decom flows onboarded to Titan/AZAP and converged across national clouds. Arun',
            'expected': 'spam_to_delete',  # Not work_relevant
            'explanation': 'Generic congratulations reply adds no value'
        },
        {
            'name': 'Other Team Action',
            'subject': 'Re: CumulusV2 TiP Halt and Eviction Operations in East US Region',
            'sender': 'Rohith Kugve', 
            'body': 'PR for CVM tests Pull request 13391894: Add more regions for CVM tests - Repos',
            'expected': 'fyi',  # Not team_action
            'explanation': 'Other team is handling this, just informing us'
        }
    ]
    
    try:
        from ai_processor import AIProcessor
        
        ai_processor = AIProcessor()
        learning_data = ai_processor.load_learning_data()
        
        print("🧪 TESTING EMAIL CLASSIFICATION IMPROVEMENTS")
        print("="*70)
        
        for i, case in enumerate(test_cases, 1):
            email_content = {
                'subject': case['subject'],
                'sender': case['sender'], 
                'body': case['body'],
                'received_time': '2025-09-08'
            }
            
            print(f"\n--- Test {i}: {case['name']} ---")
            print(f"Subject: {case['subject']}")
            print(f"Expected: {case['expected']}")
            print(f"Why: {case['explanation']}")
            
            try:
                # Test original prompt
                old_result = ai_processor.classify_email(email_content, learning_data)
                print(f"Original: {old_result}")
                
                # Test improved prompt  
                new_result = ai_processor.classify_email_improved(email_content, learning_data)
                print(f"Improved: {new_result}")
                
                # Compare results
                if new_result == case['expected'] and old_result != case['expected']:
                    print("✅ IMPROVEMENT: Fixed the classification!")
                elif new_result == case['expected'] and old_result == case['expected']:
                    print("✅ MAINTAINED: Both correct")
                elif new_result != case['expected'] and old_result == case['expected']:
                    print("❌ REGRESSION: Broke working classification")
                else:
                    print("⚠️ NO IMPROVEMENT: Both still incorrect")
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
    
        print(f"\n{'='*70}")
        print("✅ Test completed! Check results above.")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure to run from the email_helper directory")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_sample_emails()
