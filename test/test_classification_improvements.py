#!/usr/bin/env python3
"""
Test script to compare old vs improved email classification prompts
"""
import sys
import os
sys.path.append('src')

from ai_processor import AIProcessor
import pandas as pd

def test_classification_improvements():
    """Test the improved classification prompt against known error cases"""
    
    # Load recent error cases from suggestion modifications
    df = pd.read_csv('runtime_data/user_feedback/suggestion_modifications.csv')
    
    # Select representative error cases for testing
    test_cases = []
    
    # Case 1: Required Personal Action -> Team Action errors
    rpa_to_team = df[(df['old_suggestion'] == 'required_personal_action') & 
                     (df['new_suggestion'] == 'team_action')].head(3)
    for _, row in rpa_to_team.iterrows():
        test_cases.append({
            'subject': row['subject'],
            'sender': row['sender'],
            'body': row['body_preview'],
            'expected_new': row['new_suggestion'],
            'old_ai_result': row['old_suggestion'],
            'user_explanation': row['user_explanation'],
            'type': 'rpa_to_team'
        })
    
    # Case 2: Work Relevant -> Spam errors
    work_to_spam = df[(df['old_suggestion'] == 'work_relevant') & 
                      (df['new_suggestion'] == 'spam_to_delete')].head(3)
    for _, row in work_to_spam.iterrows():
        test_cases.append({
            'subject': row['subject'],
            'sender': row['sender'], 
            'body': row['body_preview'],
            'expected_new': row['new_suggestion'],
            'old_ai_result': row['old_suggestion'],
            'user_explanation': row['user_explanation'],
            'type': 'work_to_spam'
        })
    
    # Case 3: Team Action -> FYI errors
    team_to_fyi = df[(df['old_suggestion'] == 'team_action') & 
                     (df['new_suggestion'] == 'fyi')].head(3)
    for _, row in team_to_fyi.iterrows():
        test_cases.append({
            'subject': row['subject'],
            'sender': row['sender'],
            'body': row['body_preview'], 
            'expected_new': row['new_suggestion'],
            'old_ai_result': row['old_suggestion'],
            'user_explanation': row['user_explanation'],
            'type': 'team_to_fyi'
        })
    
    print(f"🧪 Testing {len(test_cases)} representative error cases...")
    print("="*80)
    
    # Test with both prompts
    ai_processor = AIProcessor()
    learning_data = ai_processor.load_learning_data()
    
    improvements = 0
    no_change = 0
    regressions = 0
    
    for i, case in enumerate(test_cases, 1):
        email_content = {
            'subject': case['subject'],
            'sender': case['sender'],
            'body': case['body'],
            'received_time': '2025-09-08'
        }
        
        print(f"\n--- Test Case {i} ({case['type']}) ---")
        print(f"Subject: {case['subject'][:60]}...")
        print(f"Sender: {case['sender']}")
        print(f"User Explanation: {case['user_explanation']}")
        print(f"Expected Correct: {case['expected_new']}")
        print(f"Old AI Result: {case['old_ai_result']}")
        
        try:
            # Test with original prompt
            old_result = ai_processor.classify_email(email_content, learning_data)
            print(f"Original Prompt: {old_result}")
            
            # Test with improved prompt (modify the method temporarily)
            # We'll backup and restore the prompty file reference
            original_prompty = 'email_classifier_system.prompty'
            improved_prompty = 'email_classifier_system_improved.prompty'
            
            # Temporarily use improved prompt
            inputs = ai_processor._create_email_inputs(email_content, f"{ai_processor.get_standard_context()}\\nLearning History: {len(learning_data)} previous decisions")
            improved_result = ai_processor.execute_prompty(improved_prompty, inputs)
            
            if improved_result:
                improved_result = improved_result.strip().lower()
                print(f"Improved Prompt: {improved_result}")
                
                # Evaluate improvement
                if improved_result == case['expected_new']:
                    if old_result != case['expected_new']:
                        improvements += 1
                        print("✅ IMPROVEMENT: Fixed classification error!")
                    else:
                        no_change += 1  
                        print("✅ MAINTAINED: Already correct")
                elif old_result == case['expected_new']:
                    regressions += 1
                    print("❌ REGRESSION: Broke previously correct classification")
                else:
                    no_change += 1
                    print("⚠️ NO CHANGE: Still incorrect")
            else:
                print("❌ FAILED: Improved prompt failed to return result")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print(f"\n{'='*80}")
    print(f"📊 IMPROVEMENT TESTING RESULTS:")
    print(f"✅ Improvements: {improvements}")
    print(f"➖ No Change: {no_change}")  
    print(f"❌ Regressions: {regressions}")
    
    if improvements > regressions:
        print(f"🎉 NET IMPROVEMENT: {improvements - regressions} cases improved")
        print("👍 RECOMMENDATION: Deploy improved prompt")
    else:
        print(f"⚠️ MIXED RESULTS: May need further refinement")
    
    print(f"{'='*80}")

if __name__ == "__main__":
    test_classification_improvements()
