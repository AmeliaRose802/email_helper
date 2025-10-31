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
    
    def __init__(self):
        """Initialize AI service with AIOrchestrator."""
        self.ai_orchestrator = None
        self.azure_config = None
        self._initialized = False
    
    def _parse_email_content(self, email_content: str) -> Dict[str, str]:
        """Parse email content to extract subject, sender, and body.
        
        Args:
            email_content: Full email text (may include Subject:, From: headers)
            
        Returns:
            Dict with keys: subject, sender, body
        """
        lines = email_content.split('\n')
        subject = "No subject"
        sender = "Unknown sender"
        body = email_content
        
        # Simple parsing to extract subject and sender
        for line in lines[:5]:  # Check first few lines
            if line.startswith('Subject:'):
                subject = line.replace('Subject:', '').strip()
            elif line.startswith('From:'):
                sender = line.replace('From:', '').strip()
            elif line.strip() == '':
                body = '\n'.join(lines[lines.index(line)+1:])
                break
        
        return {"subject": subject, "sender": sender, "body": body}
    
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
    
    def _classification_fallback(self, error_msg: str) -> Dict[str, Any]:
        """Generate fallback classification response."""
        return {
            "category": "work_relevant",
            "confidence": 0.5,
            "reasoning": f"Classification failed: {error_msg}",
            "alternatives": [],
            "error": error_msg
        }
    
    def _action_items_fallback(self, error_msg: str) -> Dict[str, Any]:
        """Generate fallback action items response."""
        return {
            "action_items": [],
            "urgency": "unknown",
            "deadline": None,
            "confidence": 0.0,
            "due_date": None,
            "action_required": "Unable to extract action items",
            "explanation": f"Action item extraction failed: {error_msg}",
            "relevance": "Unknown relevance due to processing error",
            "links": [],
            "error": error_msg
        }
    
    def _summary_fallback(self, error_msg: str) -> Dict[str, Any]:
        """Generate fallback summary response."""
        return {
            "summary": f"Unable to generate summary: {error_msg}",
            "key_points": [],
            "confidence": 0.0,
            "error": error_msg
        }
    
    def _parse_json_result(self, result: Any, fallback: Dict[str, Any]) -> Dict[str, Any]:
        """Parse JSON result from AI with fallback.
        
        Args:
            result: Result from AI (may be string or dict)
            fallback: Fallback dict to return if parsing fails
            
        Returns:
            Parsed dict or fallback
        """
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return fallback
        return fallback
    
    def _execute_prompty_with_email(self, template: str, email_content: str, context: str = "") -> Any:
        """Execute prompty template with parsed email content.
        
        Args:
            template: Prompty template filename
            email_content: Full email content to parse
            context: Additional context
            
        Returns:
            Result from prompty execution
        """
        parsed = self._parse_email_content(email_content)
        inputs = {
            'context': context,
            'username': 'User',
            'subject': parsed["subject"],
            'sender': parsed["sender"],
            'date': 'Recent',
            'body': parsed["body"]
        }
        return self.ai_orchestrator.execute_prompty(template, inputs)
    
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
        """Async wrapper for email classification using full email content.
        
        Args:
            email_content: Full email text (may include Subject:, From: headers)
            context: Additional context for classification
            
        Returns:
            Dict containing classification results with category, confidence, and reasoning
        """
        self._ensure_initialized()
        
        try:
            return await self._run_sync(
                self._classify_email_sync,
                email_content,
                context or ""
            )
        except Exception as e:
            return self._classification_fallback(str(e))
    
    async def classify_email_async(
        self, 
        subject: str, 
        content: str, 
        sender: str, 
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Async wrapper for email classification.
        
        Args:
            subject: Email subject line
            content: Email body content
            sender: Email sender address
            context: Additional context for classification
            
        Returns:
            Dict containing classification results with category, confidence, and reasoning
        """
        self._ensure_initialized()
        email_text = f"Subject: {subject}\nFrom: {sender}\n\n{content}"
        
        try:
            return await self._run_sync(
                self._classify_email_sync,
                email_text,
                context or ""
            )
        except Exception as e:
            return self._classification_fallback(str(e))
    
    def _classify_email_sync(self, email_content: str, context: str) -> Dict[str, Any]:
        """Synchronous email classification for thread pool execution."""
        try:
            # Use the enhanced classification method with explanation
            result = self.ai_orchestrator.classify_email_with_explanation(
                email_content, 
                learning_data=[]  # Empty learning data for now
            )
            
            # Ensure result is in expected format
            if isinstance(result, dict):
                return {
                    "category": result.get("category", "work_relevant"),
                    "confidence": result.get("confidence", 0.8),
                    "reasoning": result.get("explanation", "Classification completed"),
                    "alternatives": result.get("alternatives", [])
                }
            else:
                # Fallback for string results
                return {
                    "category": str(result) if result else "work_relevant",
                    "confidence": 0.8,
                    "reasoning": "Email classified successfully",
                    "alternatives": []
                }
        except Exception as e:
            raise RuntimeError(f"Email classification failed: {e}")
    
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
            return await self._run_sync(
                self._extract_action_items_sync,
                email_content,
                context or ""
            )
        except Exception as e:
            return self._action_items_fallback(str(e))
    
    def _extract_action_items_sync(self, email_content: str, context: str) -> Dict[str, Any]:
        """Synchronous action item extraction for thread pool execution."""
        try:
            result = self._execute_prompty_with_email(
                'summerize_action_item.prompty',
                email_content,
                context
            )
            
            # Parse JSON result with fallback
            fallback = {
                "due_date": "No specific deadline",
                "action_required": "Review email content",
                "explanation": "Unable to parse structured response",
                "relevance": "Email requires attention",
                "links": []
            }
            parsed_result = self._parse_json_result(result, fallback)
            
            # Convert to expected API format
            return {
                "action_items": [parsed_result.get("action_required", "Review email")] if parsed_result.get("action_required") else [],
                "urgency": "medium",
                "deadline": parsed_result.get("due_date"),
                "confidence": 0.8,
                "due_date": parsed_result.get("due_date"),
                "action_required": parsed_result.get("action_required"),
                "explanation": parsed_result.get("explanation"),
                "relevance": parsed_result.get("relevance"),
                "links": parsed_result.get("links", [])
            }
            
        except Exception as e:
            raise RuntimeError(f"Action item extraction failed: {e}")
    
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
            return await self._run_sync(
                self._generate_summary_sync,
                email_content,
                summary_type
            )
        except Exception as e:
            return self._summary_fallback(str(e))
    
    def _generate_summary_sync(self, email_content: str, summary_type: str) -> Dict[str, Any]:
        """Synchronous summary generation for thread pool execution."""
        try:
            result = self._execute_prompty_with_email(
                'email_one_line_summary.prompty',
                email_content,
                f'Summary type: {summary_type}'
            )
            
            # Process result
            summary_text = str(result).strip() if result else "Unable to generate summary"
            
            # Generate key points (simple extraction)
            key_points = []
            if len(summary_text) > 20:
                sentences = summary_text.split('.')
                key_points = [s.strip() for s in sentences if len(s.strip()) > 10][:3]
            
            return {
                "summary": summary_text,
                "key_points": key_points,
                "confidence": 0.8 if len(summary_text) > 20 else 0.5
            }
            
        except Exception as e:
            raise RuntimeError(f"Summary generation failed: {e}")
    
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
            return await self._run_sync(
                self._analyze_holistically_sync,
                emails
            )
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
        try:
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
            
        except Exception as e:
            raise RuntimeError(f"Holistic analysis failed: {e}")
    
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