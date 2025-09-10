#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_processor import AIProcessor
import json

def test_json_repair():
    print("🧪 Testing JSON Repair Functionality")
    print("=" * 50)
    
    ai = AIProcessor()
    
    # Test 1: Simple unterminated string
    print("\n📋 Test 1: Unterminated string repair")
    malformed = '{"key": "unterminated value, "other": "complete"}'
    
    try:
        json.loads(malformed)
        print("❌ Should have failed to parse")
    except json.JSONDecodeError as e:
        print(f"✅ Original fails as expected: {e}")
        
        repaired = ai._repair_json_response(malformed)
        if repaired:
            try:
                parsed = json.loads(repaired)
                print("✅ Repair successful - JSON now valid")
                print(f"   Parsed keys: {list(parsed.keys())}")
            except json.JSONDecodeError as repair_error:
                print(f"❌ Repair failed: {repair_error}")
        else:
            print("❌ Repair function returned None")
    
    # Test 2: Missing closing brace
    print("\n📋 Test 2: Missing closing brace")
    incomplete = '{"actions": [], "status": "incomplete"'
    
    repaired = ai._repair_json_response(incomplete)
    if repaired:
        try:
            parsed = json.loads(repaired)
            print("✅ Missing brace repair successful")
            print(f"   Parsed keys: {list(parsed.keys())}")
        except json.JSONDecodeError as e:
            print(f"❌ Missing brace repair failed: {e}")
    else:
        print("❌ Missing brace repair returned None")
    
    # Test 3: Valid JSON should remain unchanged
    print("\n📋 Test 3: Valid JSON preservation")
    valid = '{"truly_relevant_actions": [], "superseded_actions": []}'
    
    repaired = ai._repair_json_response(valid)
    if repaired:
        try:
            original_parsed = json.loads(valid)
            repaired_parsed = json.loads(repaired)
            if original_parsed == repaired_parsed:
                print("✅ Valid JSON preserved correctly")
            else:
                print("⚠️ Valid JSON was modified (but still valid)")
        except json.JSONDecodeError as e:
            print(f"❌ Valid JSON was corrupted: {e}")
    else:
        print("❌ Valid JSON repair returned None")
    
    print("\n🎉 JSON repair testing completed!")

if __name__ == "__main__":
    test_json_repair()
