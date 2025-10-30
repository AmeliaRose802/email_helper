"""Prompt Execution Module for AI Processing.

This module handles prompty template execution with fallback handling,
JSON repair, and error recovery. It provides the core infrastructure
for executing AI prompts across all AI operations.
"""

import os
import json
import logging
import re
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PromptExecutor:
    """Executes prompty templates with robust error handling.
    
    This class provides:
    - Prompty file parsing and execution
    - JSON response repair for malformed outputs
    - Content filter fallback responses
    - Execution error handling
    
    Attributes:
        prompts_dir: Path to prompty template directory
        azure_config: Azure OpenAI configuration
    """
    
    def __init__(self, prompts_dir: str, azure_config):
        """Initialize prompt executor.
        
        Args:
            prompts_dir: Path to directory containing .prompty files
            azure_config: Azure configuration object with endpoint/key/deployment
        """
        self.prompts_dir = prompts_dir
        self.azure_config = azure_config
    
    def parse_prompty_file(self, file_path: str) -> str:
        """Parse prompty file content.
        
        Args:
            file_path: Path to .prompty file
            
        Returns:
            str: Parsed file content
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def execute_prompty(self, prompty_file: str, inputs: Optional[Dict[str, Any]] = None) -> Any:
        """Execute prompty template with fallback handling.
        
        Args:
            prompty_file: Name of prompty file (e.g., 'email_classifier.prompty')
            inputs: Dictionary of input variables for the template
            
        Returns:
            Prompty execution result (string or dict depending on template)
        """
        if inputs is None:
            inputs = {}
        
        prompty_path = os.path.join(self.prompts_dir, prompty_file)
        
        logger.debug(f"[AI] Executing {prompty_file}")
        
        try:
            from promptflow.core import Prompty
            model_config = self.azure_config.get_promptflow_config()
            prompty_instance = Prompty.load(prompty_path, model={'configuration': model_config})
            result = prompty_instance(**inputs)
            logger.info(f"[AI] OK {prompty_file}")
            return result
            
        except ImportError:
            try:
                import prompty
                import prompty.azure
                
                p = prompty.load(prompty_path)
                p.model.configuration["azure_endpoint"] = self.azure_config.endpoint
                p.model.configuration["azure_deployment"] = self.azure_config.deployment  
                p.model.configuration["api_version"] = self.azure_config.api_version
                
                # Configure JSON mode for specific prompts
                json_required_prompts = [
                    'summerize_action_item', 'email_classifier', 'holistic_inbox_analyzer',
                    'action_item_deduplication', 'content_deduplication', 'email_duplicate_detection',
                    'event_relevance_assessment'
                ]
                if any(prompt_name in prompty_file for prompt_name in json_required_prompts):
                    if not hasattr(p.model, 'parameters'):
                        p.model.parameters = {}
                    p.model.parameters["response_format"] = {"type": "json_object"}
                
                # Configure authentication
                if self.azure_config.use_azure_credential():
                    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
                    token_provider = get_bearer_token_provider(
                        DefaultAzureCredential(), 
                        "https://cognitiveservices.azure.com/.default"
                    )
                    p.model.configuration["azure_ad_token_provider"] = token_provider
                    if "api_key" in p.model.configuration:
                        del p.model.configuration["api_key"]
                else:
                    p.model.configuration["api_key"] = self.azure_config.get_api_key()
                
                result = prompty.run(p, inputs=inputs)
                return result
                
            except ImportError as e:
                logger.error(f"[AI] Prompty library unavailable: {e}")
                raise RuntimeError(f"Prompty library unavailable: {e}")
                
        except Exception as e:
            error_str = str(e).lower()
            is_content_filter = any(phrase in error_str for phrase in [
                'content_filter', 'content management policy', 'responsibleaipolicyviolation',
                'jailbreak', 'filtered', 'badrequeesterror'
            ])
            
            if is_content_filter or 'wrappedopenaierror' in type(e).__name__.lower():
                logger.warning(f"[AI] Content filter blocked {prompty_file}")
                return self._get_content_filter_fallback(prompty_file, inputs)
            else:
                logger.error(f"[AI] Execution failed {prompty_file}: {str(e)[:200]}")
                return self._get_execution_error_fallback(prompty_file, inputs)
    
    def repair_json_response(self, response_text: str) -> Optional[str]:
        """Repair malformed JSON responses.
        
        Args:
            response_text: Raw JSON string that may be malformed
            
        Returns:
            Repaired JSON string or None if unrepairable
        """
        if not response_text or not response_text.strip():
            return None
        
        response_text = response_text.strip()
        
        # Try parsing as-is first
        try:
            json.loads(response_text)
            return response_text
        except json.JSONDecodeError:
            pass
        
        # Check if it even looks like JSON
        if not ('{' in response_text or '[' in response_text):
            return None
        
        repaired = response_text
        
        # Remove non-printable characters
        repaired = ''.join(char for char in repaired if ord(char) >= 32 or char in '\n\t\r')
        repaired = repaired.replace('\r\n', '\n').replace('\r', '\n')
        
        # Fix common JSON formatting issues
        repaired = re.sub(
            r'"([^"]+)":\s*"([^"]*),\s*\n\s*"',
            lambda m: f'"{m.group(1)}": "{m.group(2)}",\n    "',
            repaired
        )
        
        # Balance brackets
        open_braces = repaired.count('{')
        close_braces = repaired.count('}')
        open_brackets = repaired.count('[')
        close_brackets = repaired.count(']')
        
        if open_brackets > close_brackets:
            repaired += ']' * (open_brackets - close_brackets)
        if open_braces > close_braces:
            repaired += '}' * (open_braces - close_braces)
        
        # Try parsing repaired version
        try:
            json.loads(repaired)
            return repaired
        except json.JSONDecodeError:
            # Last resort: return minimal valid structure for specific types
            if 'truly_relevant_actions' in repaired:
                minimal = {
                    "truly_relevant_actions": [],
                    "superseded_actions": [],
                    "duplicate_groups": [],
                    "expired_items": []
                }
                return json.dumps(minimal)
            return None
    
    def _get_content_filter_fallback(self, prompty_file: str, inputs: Dict[str, Any]) -> Any:
        """Fallback response when content filter triggers.
        
        Args:
            prompty_file: Name of prompty file that was blocked
            inputs: Input parameters that triggered the filter
            
        Returns:
            Safe fallback response appropriate for the prompty type
        """
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
    
    def _get_execution_error_fallback(self, prompty_file: str, inputs: Dict[str, Any]) -> Any:
        """Fallback response when AI execution fails.
        
        Args:
            prompty_file: Name of prompty file that failed
            inputs: Input parameters for the failed execution
            
        Returns:
            Safe fallback response appropriate for the prompty type
        """
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
