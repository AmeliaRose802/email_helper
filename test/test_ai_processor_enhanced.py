#!/usr/bin/env python3
"""
Comprehensive tests for enhanced AI processor functionality
Tests few-shot learning, confidence thresholds, and explanation generation
"""

import sys
import os

# Add parent directory to path so we can import from src
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))


def create_mock_learning_data():
    """Create mock learning data structure"""
    class MockDataFrame:
        def __init__(self, data):
            self.data = data
            self.empty = len(data) == 0
            self.columns = ['subject', 'sender', 'body', 'category', 'user_modified'] if data else []
            
        def iterrows(self):
            for i, item in enumerate(self.data):
                yield i, MockRow(item)
                
        def get(self, col, default):
            return [item.get(col, default) for item in self.data]
            
        def copy(self):
            return MockDataFrame(self.data.copy())
    
    class MockRow:
        def __init__(self, data):
            self.data = data
            
        def get(self, key, default=None):
            return self.data.get(key, default)
    
    sample_data = [
        {
            'subject': 'Review PR #123: Fix auth bug',
            'sender': 'teammate@company.com',
            'body': 'Please review this PR to fix authentication issues',
            'category': 'team_action',
            'user_modified': False
        },
        {
            'subject': 'Weekly newsletter from Engineering',
            'sender': 'newsletter@company.com', 
            'body': 'This week in engineering: updates and announcements',
            'category': 'newsletter',
            'user_modified': False
        }
    ]
    
    return MockDataFrame(sample_data)


def test_ai_processor_enhancements():
    """Test enhanced AI processor functionality"""
    print("\n🧪 TESTING ENHANCED AI PROCESSOR FUNCTIONALITY")
    print("=" * 60)
    
    try:
        from ai_processor import AIProcessor
        
        ai_processor = AIProcessor()
        mock_learning_data = create_mock_learning_data()
        
        test_email = {
            'subject': 'Please review PR #456: Update API',
            'sender': 'developer@company.com',
            'body': 'Could you please review this PR that updates our REST API?',
            'date': '2025-01-01'
        }
        
        print("✅ Testing few-shot example generation...")
        examples = ai_processor.get_few_shot_examples(test_email, mock_learning_data, max_examples=3)
        assert isinstance(examples, list), "Examples should be a list"
        assert len(examples) <= 3, "Should not exceed max examples"
        print(f"   Generated {len(examples)} examples")
        
        if examples:
            example = examples[0]
            assert 'subject' in example, "Example should have subject"
            assert 'category' in example, "Example should have category"
            assert len(example['subject']) <= 100, "Subject should be truncated"
        
        print("✅ Testing confidence thresholds...")
        
        # Test FYI with high confidence
        fyi_result = ai_processor.apply_confidence_thresholds(
            {'category': 'fyi', 'explanation': 'Just informational'}, 0.95
        )
        assert fyi_result['auto_approve'] == True, "High confidence FYI should auto-approve"
        print("   High confidence FYI: auto-approved ✓")
        
        # Test FYI with low confidence
        fyi_low = ai_processor.apply_confidence_thresholds(
            {'category': 'fyi', 'explanation': 'Not sure'}, 0.7
        )
        assert fyi_low['auto_approve'] == False, "Low confidence FYI should need review"
        print("   Low confidence FYI: requires review ✓")
        
        # Test required action always needs review
        required_action = ai_processor.apply_confidence_thresholds(
            {'category': 'required_personal_action', 'explanation': 'Needs action'}, 0.99
        )
        assert required_action['auto_approve'] == False, "Required actions should always need review"
        print("   Required actions: always require review ✓")
        
        # Test team action always needs review
        team_action = ai_processor.apply_confidence_thresholds(
            {'category': 'team_action', 'explanation': 'Team needs to act'}, 0.99
        )
        assert team_action['auto_approve'] == False, "Team actions should always need review"
        print("   Team actions: always require review ✓")
        
        print("✅ Testing explanation generation...")
        
        # Test explanation generation for different categories
        categories = ['team_action', 'fyi', 'required_personal_action', 'newsletter']
        for category in categories:
            explanation = ai_processor.generate_explanation(test_email, category)
            assert isinstance(explanation, str), f"Explanation for {category} should be string"
            assert len(explanation) > 10, f"Explanation for {category} should be meaningful"
            print(f"   {category}: explanation generated ✓")
        
        print("✅ Testing empty learning data handling...")
        empty_data = create_mock_learning_data()
        empty_data.data = []
        empty_data.empty = True
        
        empty_examples = ai_processor.get_few_shot_examples(test_email, empty_data)
        assert empty_examples == [], "Empty data should return empty examples"
        print("   Empty data handled correctly ✓")
        
        print("✅ All enhanced AI processor tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced AI processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_enhanced_tests():
    """Run the enhanced test suite"""
    return test_ai_processor_enhancements()


if __name__ == '__main__':
    run_enhanced_tests()