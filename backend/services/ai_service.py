"""AI service wrapper for FastAPI Email Helper API.

This module provides async wrappers around the existing AIProcessor functionality
for use with FastAPI endpoints, following T1's dependency injection patterns.
"""

import asyncio
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.core.business.ai_orchestrator import AIOrchestrator
from backend.core.infrastructure.azure_config import get_azure_config


class AIService:
    """Async AI service wrapper for FastAPI integration.
    
    Wraps AIOrchestrator (pure business logic) with async operations
    for FastAPI endpoint integration.
    """
    
    def __init__(self, ai_orchestrator: Optional[AIOrchestrator] = None, azure_config: Optional[Any] = None):
        """Initialize AI service with AIOrchestrator.
        
        Args:
            ai_orchestrator: Optional pre-configured AIOrchestrator (for dependency injection)
            azure_config: Optional Azure configuration (for dependency injection)
        """
        self.ai_orchestrator = ai_orchestrator
        self.azure_config = azure_config
        self._initialized = ai_orchestrator is not None and azure_config is not None
    
    async def _run_sync(self, func, *args):
        """Run synchronous function in executor to avoid blocking event loop.
        
        Args:
            func: Synchronous function to execute
            *args: Arguments to pass to function
            
        Returns:
            Result from function execution
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)
    
    def _error_response(self, response_type: str, error_msg: str) -> Dict[str, Any]:
        """Generate error response based on type."""
        error_responses = {
            "classification": {"category": "work_relevant", "confidence": 0.5, "reasoning": error_msg, "alternatives": []},
            "action_items": {"action_items": [], "urgency": "unknown", "deadline": None, "confidence": 0.0, "action_required": "Unable to extract action items", "explanation": error_msg},
            "summary": {"summary": f"Unable to generate summary: {error_msg}", "key_points": [], "confidence": 0.0}
        }
        return {**error_responses.get(response_type, {}), "error": error_msg}
    
    @staticmethod
    def _parse_email_headers(email_content: str) -> tuple[str, str, str]:
        """Parse email headers from content.
        
        Returns:
            tuple: (subject, sender, body)
        """
        lines = email_content.split('\n', 5)
        subject = sender = ""
        for i, line in enumerate(lines[:5]):
            if line.startswith('Subject:'): subject = line[8:].strip()
            elif line.startswith('From:'): sender = line[5:].strip()
            elif not line.strip():
                return subject, sender, '\n'.join(lines[i+1:])
        return subject, sender, email_content
    
    def _convert_email_for_orchestrator(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """Convert API email format to AIOrchestrator format."""
        return {
            'entry_id': email.get('id', ''),
            'subject': email.get('subject', ''),
            'sender': email.get('sender', email.get('from', '')),
            'sender_name': email.get('sender_name', email.get('from', '')),
            'received_time': email.get('date', email.get('received_time', '')),
            'body': email.get('body', email.get('content', ''))
        }
        
    def _ensure_initialized(self):
        """Lazy initialization of AI components."""
        if not self._initialized:
            if AIOrchestrator is None or get_azure_config is None:
                raise RuntimeError("AI dependencies not available")
            
            try:
                self.azure_config = get_azure_config()
                self.ai_orchestrator = AIOrchestrator(self.azure_config)
                self._initialized = True
            except Exception as e:
                raise RuntimeError(f"Failed to initialize AI components: {e}")
    
    async def classify_email(
        self, 
        email_content: str, 
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Async wrapper for email classification.
        
        Args:
            email_content: Full email text (may include Subject:, From: headers)
            context: Additional context for classification
            
        Returns:
            Dict containing classification results with category, confidence, and reasoning
        """
        self._ensure_initialized()
        try:
            return await self._run_sync(self._classify_email_sync, email_content, context or "")
        except Exception as e:
            return self._error_response("classification", str(e))
    
    def _classify_email_sync(self, email_content: str, context: str) -> Dict[str, Any]:
        """Synchronous email classification for thread pool execution."""
        result = self.ai_orchestrator.classify_email_with_explanation(email_content, learning_data=[])
        
        if isinstance(result, dict):
            return {
                "category": result.get("category", "work_relevant"),
                "confidence": result.get("confidence", 0.8),
                "reasoning": result.get("explanation", "Classification completed"),
                "alternatives": result.get("alternatives", [])
            }
        
        return {
            "category": str(result) if result else "work_relevant",
            "confidence": 0.8,
            "reasoning": "Email classified successfully",
            "alternatives": []
        }
    
    async def extract_action_items(
        self, 
        email_content: str, 
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract action items from email content.
        
        Args:
            email_content: Full email content for analysis
            context: Additional context for extraction
            
        Returns:
            Dict containing action items, urgency, deadline, and other details
        """
        self._ensure_initialized()
        try:
            return await self._run_sync(self._extract_action_items_sync, email_content, context or "")
        except Exception as e:
            return self._error_response("action_items", str(e))
    
    @staticmethod
    def _parse_ai_result(result: Any, default_action: str = "Review email content") -> Dict[str, Any]:
        """Parse AI result into dict, handling string/dict/other types."""
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"action_required": default_action, "explanation": "Unable to parse structured response"}
        return {"action_required": default_action}
    
    def _extract_action_items_sync(self, email_content: str, context: str) -> Dict[str, Any]:
        """Synchronous action item extraction for thread pool execution."""
        subject, sender, body = self._parse_email_headers(email_content)
        
        inputs = {
            'context': context, 'username': 'User',
            'subject': subject or 'No subject', 'sender': sender or 'Unknown',
            'date': 'Recent', 'body': body
        }
        result = self.ai_orchestrator.execute_prompty('summerize_action_item.prompty', inputs)
        parsed = self._parse_ai_result(result)
        
        # Extract action_items list from parsed result
        action_items = parsed.get("action_items", [])
        if not isinstance(action_items, list):
            # If action_items isn't a list, try to construct from action_required
            action_required = parsed.get("action_required", "Review email")
            action_items = []
            if action_required and action_required != "No action required":
                action_items = [{"action": action_required, "deadline": parsed.get("due_date"), "priority": "medium"}]
        
        action = parsed.get("action_required", "Review email")
        return {
            "action_items": action_items,
            "urgency": "medium",
            "deadline": parsed.get("due_date"),
            "confidence": 0.8,
            "due_date": parsed.get("due_date"),
            "action_required": action,
            "explanation": parsed.get("explanation"),
            "relevance": parsed.get("relevance"),
            "links": parsed.get("links", [])
        }
    
    async def generate_summary(
        self,
        email_content: str,
        summary_type: str = "brief"
    ) -> Dict[str, Any]:
        """Generate email summary.
        
        Args:
            email_content: Email content to summarize
            summary_type: Type of summary (brief or detailed)
            
        Returns:
            Dict containing summary, key points, and confidence
        """
        self._ensure_initialized()
        try:
            return await self._run_sync(self._generate_summary_sync, email_content, summary_type)
        except Exception as e:
            return self._error_response("summary", str(e))
    
    def _generate_summary_sync(self, email_content: str, summary_type: str) -> Dict[str, Any]:
        """Synchronous summary generation for thread pool execution."""
        subject, sender, body = self._parse_email_headers(email_content)
        
        inputs = {
            'context': f'Summary type: {summary_type}', 'username': 'User',
            'subject': subject or 'No subject', 'sender': sender or 'Unknown',
            'date': 'Recent', 'body': body
        }
        result = self.ai_orchestrator.execute_prompty('email_one_line_summary.prompty', inputs)
        
        summary_text = str(result).strip() if result else "Unable to generate summary"
        is_good = result and len(summary_text) > 20
        key_points = [s.strip() for s in summary_text.split('.') if len(s.strip()) > 10][:3] if is_good else []
        
        return {
            "summary": summary_text,
            "key_points": key_points,
            "confidence": 0.8 if is_good else 0.5
        }
    
    async def detect_duplicates(
        self,
        emails: List[Dict[str, Any]]
    ) -> List[str]:
        """Detect duplicate emails using AI.
        
        Args:
            emails: List of email dictionaries to check for duplicates
            
        Returns:
            List of email IDs that are duplicates
        """
        self._ensure_initialized()
        try:
            return await self._run_sync(self._detect_duplicates_sync, emails)
        except Exception as e:
            return []
    
    def _detect_duplicates_sync(self, emails: List[Dict[str, Any]]) -> List[str]:
        """Synchronous duplicate detection for thread pool execution."""
        email_data_list = [self._convert_email_for_orchestrator(email) for email in emails]
        
        inputs = {"emails": email_data_list}
        result = self.ai_orchestrator.execute_prompty('email_duplicate_detection.prompty', inputs)
        
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                return parsed.get("duplicate_ids", [])
            except json.JSONDecodeError:
                return []
        elif isinstance(result, dict):
            return result.get("duplicate_ids", [])
        elif isinstance(result, list):
            return result
        return []
    
    async def analyze_holistically(
        self,
        emails: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform holistic analysis across multiple emails.
        
        Args:
            emails: List of email dictionaries with content
            
        Returns:
            Dict containing holistic analysis results with truly_relevant_actions,
            superseded_actions, duplicate_groups, and expired_items
        """
        self._ensure_initialized()
        try:
            return await self._run_sync(self._analyze_holistically_sync, emails)
        except Exception as e:
            return {
                "truly_relevant_actions": [],
                "superseded_actions": [],
                "duplicate_groups": [],
                "expired_items": [],
                "error": str(e)
            }
    
    def _analyze_holistically_sync(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synchronous holistic analysis for thread pool execution."""
        email_data_list = [self._convert_email_for_orchestrator(email) for email in emails]
        analysis, notes = self.ai_orchestrator.analyze_inbox_holistically(email_data_list)
        
        if not analysis:
            return {
                "truly_relevant_actions": [],
                "superseded_actions": [],
                "duplicate_groups": [],
                "expired_items": [],
                "notes": notes
            }
        
        return analysis
    
    def _extract_template_description(self, template_file: Path) -> str:
        """Extract description from prompty template YAML frontmatter."""
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 2:
                        for line in parts[1].split('\n'):
                            if line.strip().startswith('description:'):
                                return line.split('description:', 1)[1].strip().strip('"\'')
        except Exception:
            pass
        return "No description available"
    
    async def get_available_templates(self) -> Dict[str, Any]:
        """Get list of available prompt templates.
        
        Returns:
            Dict containing template names and descriptions
        """
        templates_dir = Path(__file__).parent.parent.parent / "prompts"
        
        if not templates_dir.exists():
            return {"templates": [], "descriptions": {}}
        
        templates = []
        descriptions = {}
        
        for template_file in templates_dir.glob("*.prompty"):
            template_name = template_file.name
            templates.append(template_name)
            descriptions[template_name] = self._extract_template_description(template_file)
        
        return {
            "templates": sorted(templates),
            "descriptions": descriptions
        }


def get_ai_service() -> AIService:
    """FastAPI dependency for AI service (following T1's pattern)."""
    return AIService()