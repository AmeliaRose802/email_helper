#!/usr/bin/env python3
"""
Debug holistic deduplication similarity calculation
"""

import sys
import os
from datetime import datetime

# Add parent directory to path so we can import from src
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))

def debug_similarity_calculation():
    """Debug why holistic deduplication isn't working"""
    print("🔍 DEBUGGING HOLISTIC DEDUPLICATION SIMILARITY")
    print("=" * 60)
    
    try:
        from email_analyzer import EmailAnalyzer
        
        # Create email analyzer
        analyzer = EmailAnalyzer()
        
        # Create test items that should be detected as similar
        action_item = {
            'subject': 'Certificate Renewal Required',
            'sender': 'IT Security',
            'action_required': 'Renew your security certificate before expiration',
            'due_date': '2025-01-15'
        }
        
        fyi_item = {
            'subject': 'Certificate Expiring Soon',
            'sender': 'Security Team',
            'summary': 'Your certificate will expire soon and needs renewal'  # No action_required field
        }
        
        newsletter_item = {
            'subject': 'Security Update Newsletter',
            'sender': 'IT Newsletter',
            'summary': 'Monthly security newsletter with certificate renewal reminders'  # No action_required field
        }
        
        print("📊 Test Items:")
        print(f"   Action: '{action_item['subject']}' - '{action_item['action_required']}'")
        print(f"   FYI: '{fyi_item['subject']}' - '{fyi_item['summary']}'")
        print(f"   Newsletter: '{newsletter_item['subject']}' - '{newsletter_item['summary']}'")
        print()
        
        # Test similarity between action and FYI
        print("🔍 Action vs FYI Comparison:")
        is_similar_fyi, score_fyi = analyzer.calculate_content_similarity(
            action_item, fyi_item, threshold=0.65
        )
        print(f"   Similarity Score: {score_fyi:.3f}")
        print(f"   Is Similar (≥0.65): {is_similar_fyi}")
        print(f"   Expected: Should be similar (both about certificate renewal)")
        print()
        
        # Test similarity between action and newsletter
        print("🔍 Action vs Newsletter Comparison:")
        is_similar_newsletter, score_newsletter = analyzer.calculate_content_similarity(
            action_item, newsletter_item, threshold=0.6
        )
        print(f"   Similarity Score: {score_newsletter:.3f}")
        print(f"   Is Similar (≥0.6): {is_similar_newsletter}")
        print(f"   Expected: Should be similar (both about certificate)")
        print()
        
        # Debug the feature extraction
        print("🔍 Feature Extraction Debug:")
        action_features = analyzer._extract_similarity_features(action_item)
        fyi_features = analyzer._extract_similarity_features(fyi_item)
        newsletter_features = analyzer._extract_similarity_features(newsletter_item)
        
        print(f"   Action features:")
        print(f"     subject: '{action_features['subject']}'")
        print(f"     sender: '{action_features['sender']}'")
        print(f"     action: '{action_features['action']}'")
        print(f"     due_date: '{action_features['due_date']}'")
        print()
        
        print(f"   FYI features:")
        print(f"     subject: '{fyi_features['subject']}'")
        print(f"     sender: '{fyi_features['sender']}'")
        print(f"     action: '{fyi_features['action']}'")
        print(f"     due_date: '{fyi_features['due_date']}'")
        print()
        
        print(f"   Newsletter features:")
        print(f"     subject: '{newsletter_features['subject']}'")
        print(f"     sender: '{newsletter_features['sender']}'")
        print(f"     action: '{newsletter_features['action']}'")
        print(f"     due_date: '{newsletter_features['due_date']}'")
        print()
        
        # Test individual similarity components
        print("🔍 Component-wise Similarity:")
        
        # Action vs FYI
        subject_sim = analyzer._calculate_text_similarity(action_features['subject'], fyi_features['subject'])
        sender_sim = analyzer._calculate_exact_match_score(action_features['sender'], fyi_features['sender'])
        action_sim = analyzer._calculate_text_similarity(action_features['action'], fyi_features['action'])
        date_sim = analyzer._calculate_date_similarity(action_features['due_date'], fyi_features['due_date'])
        
        print(f"   Action vs FYI components:")
        print(f"     Subject similarity: {subject_sim:.3f}")
        print(f"     Sender match: {sender_sim:.3f}")
        print(f"     Action similarity: {action_sim:.3f}")
        print(f"     Date similarity: {date_sim:.3f}")
        
        weighted_score = (subject_sim * 0.3 + action_sim * 0.4 + sender_sim * 0.2 + date_sim * 0.1)
        print(f"     Weighted total: {weighted_score:.3f}")
        print()
        
        # Recommendations
        print("💡 Recommendations:")
        if score_fyi < 0.65:
            print(f"   - FYI similarity ({score_fyi:.3f}) below threshold (0.65)")
            print(f"   - Consider lowering threshold or improving content similarity")
            
            if action_sim < 0.3:
                print(f"   - Action text similarity very low ({action_sim:.3f})")
                print(f"   - FYI items use 'summary' field instead of 'action_required'")
                print(f"   - Need to compare action_required vs summary fields")
        
        if score_newsletter < 0.6:
            print(f"   - Newsletter similarity ({score_newsletter:.3f}) below threshold (0.6)")
            print(f"   - Newsletters may need different comparison logic")
        
        print()
        print("=" * 60)
        print("✅ Similarity debug completed")
        
    except Exception as e:
        print(f"❌ Debug failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_similarity_calculation()