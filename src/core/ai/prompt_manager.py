"""Prompt Manager - Prompty Template Management and Execution.

This module handles loading, parsing, and executing prompty template files,
providing a clean interface for AI prompt execution.
"""

import os
import logging
from core.ai_client import AIClient

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages prompty template loading and execution.
    
    This class handles all prompty file operations including parsing
    YAML frontmatter, loading templates, and executing prompts through
    the AI client abstraction layer.
    """
    
    def __init__(self, prompts_dir: str, ai_client: AIClient):
        """Initialize the prompt manager.
        
        Args:
            prompts_dir: Directory containing prompty template files
            ai_client: AI client for executing prompts
        """
        self.prompts_dir = prompts_dir
        self.ai_client = ai_client
    
    def parse_prompty_file(self, file_path):
        """Parse a prompty template file and extract the content.
        
        Args:
            file_path (str): Path to the .prompty file to parse.
            
        Returns:
            str: The parsed prompt content without YAML frontmatter.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                return parts[2].strip()
            raise ValueError(f"Malformed YAML frontmatter in {file_path}")
        return content
    
    def execute_prompty(self, prompty_file, inputs=None):
        """Execute a prompty template with given inputs.
        
        Args:
            prompty_file: Name of the .prompty file to execute
            inputs: Dictionary of input variables for the template
            
        Returns:
            AI response - type depends on prompty template
        """
        if inputs is None:
            inputs = {}
        
        prompty_path = os.path.join(self.prompts_dir, prompty_file)
        
        logger.debug(f"[PromptManager] Executing {prompty_file} with inputs: {list(inputs.keys())}")
        
        # Determine if JSON format should be enforced
        json_required_prompts = [
            'summarize_action_item', 'email_classifier', 'holistic_inbox_analyzer',
            'action_item_deduplication', 'content_deduplication', 'email_duplicate_detection',
            'event_relevance_assessment'
        ]
        require_json = any(prompt_name in prompty_file for prompt_name in json_required_prompts)
        
        try:
            result = self.ai_client.execute_prompt(prompty_path, inputs, require_json=require_json)
            logger.info(f"[PromptManager] [OK] {prompty_file} completed successfully")
            return result
            
        except RuntimeError as e:
            error_str = str(e).lower()
            
            # Check if this is a content filter error
            is_content_filter = any(phrase in error_str for phrase in [
                'content_filter', 'content management policy', 'responsibleaipolicyviolation',
                'jailbreak', 'filtered', 'badrequeesterror', 'content filter violation'
            ])
            
            if is_content_filter:
                logger.warning(f"[PromptManager] [FILTER] Content filter blocked {prompty_file}")
                return self._get_content_filter_fallback(prompty_file, inputs)
            else:
                logger.error(f"[PromptManager] [ERROR] Prompty execution failed for {prompty_file}", exc_info=True)
                return self._get_execution_error_fallback(prompty_file, inputs)
    
    def _get_content_filter_fallback(self, prompty_file, inputs):
        """Return appropriate fallback response when content filter blocks the request."""
        if 'email_one_line_summary' in prompty_file:
            subject = inputs.get('subject', 'Email')
            return f"Summary blocked by content filter - {subject[:80]}"
        elif 'event_relevance_assessment' in prompty_file:
            return "Unable to assess relevance - content filter triggered"
        elif 'email_classifier' in prompty_file:
            return '{"category": "fyi", "explanation": "Classification blocked by content filter"}'
        elif 'fyi_summary' in prompty_file:
            subject = inputs.get('subject', 'Email')
            return f"• Summary blocked by content filter - {subject[:80]}"
        elif 'newsletter_summary' in prompty_file:
            return "Newsletter summary blocked by content filter"
        elif 'summerize_action_item' in prompty_file:
            return '{"action_required": "Review email manually", "due_date": "No deadline", "explanation": "Content filter blocked analysis", "relevance": "Manual review needed", "links": []}'
        elif 'holistic_inbox_analyzer' in prompty_file:
            return '{"truly_relevant_actions": [], "superseded_actions": [], "duplicate_groups": [], "expired_items": []}'
        else:
            return "Content filter blocked - manual review required"
    
    def _get_execution_error_fallback(self, prompty_file, inputs):
        """Return appropriate fallback response when AI execution fails."""
        if 'email_one_line_summary' in prompty_file:
            subject = inputs.get('subject', 'Email')
            return f"AI unavailable - {subject[:80]}"
        elif 'event_relevance_assessment' in prompty_file:
            return "Unable to assess relevance - AI service unavailable"
        elif 'email_classifier' in prompty_file:
            return '{"category": "fyi", "explanation": "AI service unavailable for classification"}'
        elif 'fyi_summary' in prompty_file:
            subject = inputs.get('subject', 'Email')
            return f"• AI unavailable - {subject[:80]}"
        elif 'newsletter_summary' in prompty_file:
            return "Newsletter summary unavailable - AI service error"
        elif 'summerize_action_item' in prompty_file:
            return '{"action_required": "Review email manually", "due_date": "No deadline", "explanation": "AI service unavailable", "relevance": "Manual review needed", "links": []}'
        elif 'holistic_inbox_analyzer' in prompty_file:
            return '{"truly_relevant_actions": [], "superseded_actions": [], "duplicate_groups": [], "expired_items": []}'
        else:
            return "AI processing unavailable"
