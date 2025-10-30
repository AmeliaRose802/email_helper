"""Response Parser - AI Response Processing and Repair.

This module handles parsing, cleaning, and repairing AI responses,
including JSON parsing with fallbacks and response validation.
"""

import json
import logging
import re
from utils import clean_json_response, parse_json_with_fallback, clean_ai_response

logger = logging.getLogger(__name__)


class ResponseParser:
    """Handles parsing and repairing AI responses.
    
    This class provides robust AI response processing with automatic
    repair of common JSON formatting issues and fallback handling
    for malformed responses.
    """
    
    def repair_json_response(self, response_text):
        """Repair malformed JSON responses from AI services.
        
        Args:
            response_text (str): The potentially malformed JSON response text.
            
        Returns:
            str: The repaired JSON string, or None if no repair is possible.
        """
        if not response_text or not response_text.strip():
            return None
        
        response_text = response_text.strip()
        
        # If it's already valid JSON, return as-is
        try:
            json.loads(response_text)
            return response_text
        except json.JSONDecodeError:
            pass
        
        # For completely invalid JSON, return None
        if not ('{' in response_text or '[' in response_text):
            return None
        
        # Try common repairs
        repaired = response_text
        
        # Clean up whitespace and control characters
        repaired = ''.join(char for char in repaired if ord(char) >= 32 or char in '\n\t\r')
        repaired = repaired.replace('\r\n', '\n').replace('\r', '\n')
        
        # Fix unterminated string values
        repaired = re.sub(
            r'"([^"]+)":\s*"([^"]*),\s*\n\s*"',
            lambda m: f'"{m.group(1)}": "{m.group(2)}",\n    "',
            repaired
        )
        
        # Fix missing closing braces/brackets
        open_braces = repaired.count('{')
        close_braces = repaired.count('}')
        open_brackets = repaired.count('[')
        close_brackets = repaired.count(']')
        
        if open_brackets > close_brackets:
            repaired += ']' * (open_brackets - close_brackets)
        if open_braces > close_braces:
            repaired += '}' * (open_braces - close_braces)
        
        # Try to parse the repaired JSON
        try:
            json.loads(repaired)
            return repaired
        except json.JSONDecodeError:
            # If still invalid, try to extract minimal valid structure
            if 'truly_relevant_actions' in repaired:
                minimal = {
                    "truly_relevant_actions": [],
                    "superseded_actions": [],
                    "duplicate_groups": [],
                    "expired_items": []
                }
                return json.dumps(minimal)
            return None
    
    def parse_classification_response(self, result, email_content, fallback_category='fyi'):
        """Parse classification response with fallback handling.
        
        Args:
            result: Raw AI response
            email_content: Email data for fallback generation
            fallback_category: Category to use if parsing fails
            
        Returns:
            dict: Classification result with category and explanation
        """
        fallback_data = {
            'category': fallback_category,
            'explanation': self._generate_explanation(email_content, fallback_category)
        }
        
        if not result or result in ["AI processing unavailable", "AI processing failed"]:
            logger.warning(f"[ResponseParser] AI unavailable - using fallback classification")
            return fallback_data
        
        try:
            cleaned_result = clean_ai_response(result)
            parsed = parse_json_with_fallback(cleaned_result, fallback_data)
            
            if not isinstance(parsed, dict) or 'category' not in parsed:
                logger.warning(f"[ResponseParser] Invalid classification format")
                return fallback_data
            
            category = clean_ai_response(parsed.get('category', 'fyi')).lower()
            explanation = parsed.get('explanation', '')
            
            if not explanation or len(explanation.strip()) < 10:
                explanation = self._generate_explanation(email_content, category)
            
            return {
                'category': category,
                'explanation': explanation
            }
            
        except Exception as e:
            logger.error(f"[ResponseParser] Error parsing classification: {type(e).__name__}: {str(e)}")
            return fallback_data
    
    def parse_action_item_response(self, result, email_content):
        """Parse action item extraction response with fallback.
        
        Args:
            result: Raw AI response
            email_content: Email data for fallback generation
            
        Returns:
            dict: Action item details
        """
        fallback_data = {
            "action_required": f"Review email: {email_content.get('subject', 'Unknown')[:100]}",
            "due_date": "No specific deadline",
            "explanation": "AI processing unavailable - please review manually",
            "links": [],
            "relevance": "Manual review needed"
        }
        
        if not result or not result.strip():
            return fallback_data
        
        return parse_json_with_fallback(result, fallback_data)
    
    def _generate_explanation(self, email_content, category):
        """Generate fallback explanation when AI explanations fail."""
        sender = email_content.get('sender', 'Unknown')
        subject = email_content.get('subject', 'Unknown')
        
        explanations = {
            'required_personal_action': f"Email from {sender} appears to require personal action based on direct addressing or responsibility.",
            'team_action': f"Email indicates action required from your team based on content analysis.",
            'optional_action': f"Email contains optional activities or requests that may be worth considering.",
            'work_relevant': f"Email contains work-related information relevant to your role but requires no immediate action.",
            'fyi': f"Email is informational only with no action required.",
            'newsletter': f"Email appears to be a newsletter or bulk information distribution.",
            'spam_to_delete': f"Email does not appear relevant to work or contains no actionable content.",
            'job_listing': f"Email contains job opportunities or recruitment-related content."
        }
        
        base_explanation = explanations.get(category, f"Classified as {category} based on email content analysis.")
        return f"{base_explanation} Subject: '{subject[:50]}...'"
