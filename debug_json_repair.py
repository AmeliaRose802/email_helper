#!/usr/bin/env python3

import sys
sys.path.append('src')
from ai_processor import AIProcessor
import json

ai_processor = AIProcessor()

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

print('Original malformed JSON:')
print(repr(malformed_json))
print()

repaired = ai_processor._repair_json_response(malformed_json)
print('Repaired JSON:')
print(repr(repaired))
print()

if repaired:
    try:
        parsed = json.loads(repaired)
        print('Parsed successfully:')
        print(json.dumps(parsed, indent=2))
        print(f'Number of truly_relevant_actions: {len(parsed.get("truly_relevant_actions", []))}')
    except Exception as e:
        print(f'Failed to parse: {e}')
else:
    print('Repair returned None')