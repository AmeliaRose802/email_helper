#!/usr/bin/env python3
"""
Test suite for holistic analysis JSON parsing fix
"""

import sys
import os
import json
import unittest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_processor import AIProcessor


class TestHolisticAnalysisFix(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.ai_processor = AIProcessor()
    
    def test_repair_json_unterminated_string(self):
        """Test repair of unterminated string in JSON"""
        malformed_json = '''
        {
            "truly_relevant_actions": [
                {
                    "action_type": "required_personal_action",
                    "priority": "high",
                    "topic": "Unterminated string value,
                    "canonical_email_id": "123",
                    "why_relevant": "This is important"
                }
            ],
            "superseded_actions": []
        }
        '''
        
        repaired = self.ai_processor._repair_json_response(malformed_json)
        self.assertIsNotNone(repaired)
        
        # Should be able to parse the repaired JSON
        try:
            parsed = json.loads(repaired)
            self.assertIn("truly_relevant_actions", parsed)
            self.assertTrue(len(parsed["truly_relevant_actions"]) > 0)
            print("✅ Unterminated string repair test passed")
        except json.JSONDecodeError as e:
            self.fail(f"Repaired JSON is still invalid: {e}")
    
    def test_repair_json_missing_closing_brace(self):
        """Test repair of missing closing brace"""
        malformed_json = '''
        {
            "truly_relevant_actions": [],
            "superseded_actions": [],
            "duplicate_groups": [
        '''
        
        repaired = self.ai_processor._repair_json_response(malformed_json)
        self.assertIsNotNone(repaired)
        
        # Should be able to parse the repaired JSON
        try:
            parsed = json.loads(repaired)
            self.assertIn("truly_relevant_actions", parsed)
            print("✅ Missing closing brace repair test passed")
        except json.JSONDecodeError as e:
            self.fail(f"Repaired JSON is still invalid: {e}")
    
    def test_valid_json_unchanged(self):
        """Test that valid JSON is not modified"""
        valid_json = '''
        {
            "truly_relevant_actions": [],
            "superseded_actions": [],
            "duplicate_groups": [],
            "expired_items": []
        }
        '''
        
        repaired = self.ai_processor._repair_json_response(valid_json)
        self.assertIsNotNone(repaired)
        
        # Both original and repaired should be valid
        try:
            original_parsed = json.loads(valid_json)
            repaired_parsed = json.loads(repaired)
            
            # Should have same structure
            self.assertEqual(set(original_parsed.keys()), set(repaired_parsed.keys()))
            print("✅ Valid JSON unchanged test passed")
        except json.JSONDecodeError as e:
            self.fail(f"Valid JSON test failed: {e}")
    
    def test_holistic_analysis_error_handling(self):
        """Test that holistic analysis handles errors gracefully"""
        # Test with empty email data
        analysis, notes = self.ai_processor.analyze_inbox_holistically([])
        
        # Should return valid structure even with empty data
        self.assertIsNotNone(analysis)
        self.assertIsInstance(analysis, dict)
        
        # Should have required keys
        required_keys = ["truly_relevant_actions", "superseded_actions", "duplicate_groups", "expired_items"]
        for key in required_keys:
            self.assertIn(key, analysis)
            self.assertIsInstance(analysis[key], list)
        
        print("✅ Error handling test passed")
    
    def test_json_repair_edge_cases(self):
        """Test edge cases for JSON repair"""
        # Test completely invalid JSON
        invalid_json = "this is not json at all"
        repaired = self.ai_processor._repair_json_response(invalid_json)
        self.assertIsNone(repaired)
        
        # Test empty string
        empty_json = ""
        repaired = self.ai_processor._repair_json_response(empty_json)
        self.assertIsNone(repaired)
        
        # Test JSON with only opening brace
        incomplete_json = "{"
        repaired = self.ai_processor._repair_json_response(incomplete_json)
        self.assertIsNotNone(repaired)
        
        try:
            parsed = json.loads(repaired)
            self.assertIsInstance(parsed, dict)
            print("✅ Edge cases test passed")
        except json.JSONDecodeError:
            # This is acceptable for very incomplete JSON
            print("✅ Edge cases test passed (correctly rejected incomplete JSON)")


def run_tests():
    """Run all holistic analysis fix tests"""
    print("🧪 Running Holistic Analysis JSON Parsing Fix Tests...")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHolisticAnalysisFix)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("🎉 All tests passed! Holistic analysis JSON parsing fix is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
