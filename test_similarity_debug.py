#!/usr/bin/env python3
"""
Debug script to test content similarity calculation directly
"""

import sys
import os

# Add parent directory to path so we can import from src
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))

def test_similarity_calculation():
    """Test the content similarity calculation directly"""
    print("🔍 TESTING CONTENT SIMILARITY CALCULATION")
    print("=" * 60)
    
    try:
        from email_analyzer import EmailAnalyzer
        
        # Create email analyzer
        analyzer = EmailAnalyzer()
        
        # Create test items (same as content deduplication test)
        item1 = {
            'email_subject': 'Credential Expiring',
            'email_sender': 'One Yubi',
            'action_details': {
                'due_date': '2025-10-09',
                'action_required': 'Request a new certificate for your YubiKey credential',
                'explanation': 'Your current YubiKey certificate is set to expire on 2025-10-09'
            }
        }
        
        item2 = {
            'email_subject': 'Credential Expiring', 
            'email_sender': 'One Yubi',
            'action_details': {
                'due_date': '2025-10-09',
                'action_required': 'Request and set up a new certificate for your YubiKey',
                'explanation': 'The current certificate associated with your YubiKey is expiring in 45 days'
            }
        }
        
        item3 = {
            'email_subject': 'Different Task',
            'email_sender': 'Another Sender',
            'action_details': {
                'due_date': '2025-09-15',
                'action_required': 'Complete project review',
                'explanation': 'Need to review the project documentation'
            }
        }
        
        print("📊 Test Data:")
        print(f"   Item 1: {item1['email_subject']} from {item1['email_sender']}")
        print(f"   Item 2: {item2['email_subject']} from {item2['email_sender']}")
        print(f"   Item 3: {item3['email_subject']} from {item3['email_sender']}")
        print()
        
        # Test similarity between item1 and item2 (should be similar)
        is_similar_12, score_12 = analyzer.calculate_content_similarity(item1, item2, threshold=0.75)
        print(f"📋 Item 1 vs Item 2:")
        print(f"   Similarity Score: {score_12:.3f}")
        print(f"   Is Similar (≥0.75): {is_similar_12}")
        print()
        
        # Test similarity between item1 and item3 (should be different)
        is_similar_13, score_13 = analyzer.calculate_content_similarity(item1, item3, threshold=0.75)
        print(f"📋 Item 1 vs Item 3:")
        print(f"   Similarity Score: {score_13:.3f}")
        print(f"   Is Similar (≥0.75): {is_similar_13}")
        print()
        
        # Test similarity between item2 and item3 (should be different)
        is_similar_23, score_23 = analyzer.calculate_content_similarity(item2, item3, threshold=0.75)
        print(f"📋 Item 2 vs Item 3:")
        print(f"   Similarity Score: {score_23:.3f}")
        print(f"   Is Similar (≥0.75): {is_similar_23}")
        print()
        
        # Expected results
        print("✅ Expected Results:")
        print(f"   Item 1 vs Item 2: Should be SIMILAR (both about YubiKey credential expiring)")
        print(f"   Item 1 vs Item 3: Should be DIFFERENT (different tasks)")
        print(f"   Item 2 vs Item 3: Should be DIFFERENT (different tasks)")
        print()
        
        # Validation
        if is_similar_12 and not is_similar_13 and not is_similar_23:
            print("🎉 SUCCESS: Content similarity calculation working correctly!")
        else:
            print("❌ ISSUE: Content similarity calculation not working as expected")
            print(f"   Item1-Item2 similar: {is_similar_12} (expected: True)")
            print(f"   Item1-Item3 similar: {is_similar_13} (expected: False)")
            print(f"   Item2-Item3 similar: {is_similar_23} (expected: False)")
        
        print()
        print("=" * 60)
        print("✅ Similarity test completed")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_similarity_calculation()