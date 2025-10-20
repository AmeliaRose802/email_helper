"""AI service wrapper for FastAPI Email Helper API.

This module provides async wrappers around the existing AIProcessor functionality
for use with FastAPI endpoints, following T1's dependency injection patterns.
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add src to Python path for existing service imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from ai_processor import AIProcessor
    from azure_config import get_azure_config
except ImportError as e:
    print(f"Warning: Could not import AI dependencies: {e}")
    AIProcessor = None
    get_azure_config = None


class AIService:
    """Async AI service wrapper for FastAPI integration."""
    
    def __init__(self):
        """Initialize AI service with existing processors."""
        self.ai_processor = None
        self.azure_config = None
        self._initialized = False
        
    def _ensure_initialized(self):
        """Lazy initialization of AI components."""
        if not self._initialized:
            if AIProcessor is None or get_azure_config is None:
                raise RuntimeError("AI dependencies not available")
            
            try:
                self.ai_processor = AIProcessor()
                self.azure_config = get_azure_config()
                self._initialized = True
            except Exception as e:
                raise RuntimeError(f"Failed to initialize AI components: {e}")
    
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
        
        # Prepare email content in expected format
        email_text = f"Subject: {subject}\nFrom: {sender}\n\n{content}"
        
        # Run CPU-bound AI processing in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        
        try:
            result = await loop.run_in_executor(
                None,
                self._classify_email_sync,
                email_text,
                context or ""
            )
            return result
        except Exception as e:
            return {
                "category": "work_relevant",
                "confidence": 0.5,
                "reasoning": f"Classification failed: {str(e)}",
                "alternatives": [],
                "error": str(e)
            }
    
    def _classify_email_sync(self, email_content: str, context: str) -> Dict[str, Any]:
        """Synchronous email classification for thread pool execution."""
        try:
            # Use the enhanced classification method with explanation
            result = self.ai_processor.classify_email_with_explanation(
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
        
        loop = asyncio.get_event_loop()
        
        try:
            result = await loop.run_in_executor(
                None,
                self._extract_action_items_sync,
                email_content,
                context or ""
            )
            return result
        except Exception as e:
            return {
                "action_items": [],
                "urgency": "unknown",
                "deadline": None,
                "confidence": 0.0,
                "due_date": None,
                "action_required": "Unable to extract action items",
                "explanation": f"Action item extraction failed: {str(e)}",
                "relevance": "Unknown relevance due to processing error",
                "links": [],
                "error": str(e)
            }
    
    def _extract_action_items_sync(self, email_content: str, context: str) -> Dict[str, Any]:
        """Synchronous action item extraction for thread pool execution."""
        try:
            # Parse email content to extract components
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
            
            # Use the summerize_action_item prompty template
            inputs = {
                'context': context,
                'username': 'User',  # Default username
                'subject': subject,
                'sender': sender,
                'date': 'Recent',
                'body': body
            }
            
            result = self.ai_processor.execute_prompty('summerize_action_item.prompty', inputs)
            
            # Parse JSON result
            if isinstance(result, str):
                try:
                    parsed_result = json.loads(result)
                except json.JSONDecodeError:
                    # Fallback parsing
                    parsed_result = {
                        "due_date": "No specific deadline",
                        "action_required": "Review email content",
                        "explanation": "Unable to parse structured response",
                        "relevance": "Email requires attention",
                        "links": []
                    }
            else:
                parsed_result = result
            
            # Convert to expected API format
            return {
                "action_items": [parsed_result.get("action_required", "Review email")] if parsed_result.get("action_required") else [],
                "urgency": "medium",  # Default urgency
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
        
        loop = asyncio.get_event_loop()
        
        try:
            result = await loop.run_in_executor(
                None,
                self._generate_summary_sync,
                email_content,
                summary_type
            )
            return result
        except Exception as e:
            return {
                "summary": f"Unable to generate summary: {str(e)}",
                "key_points": [],
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _generate_summary_sync(self, email_content: str, summary_type: str) -> Dict[str, Any]:
        """Synchronous summary generation for thread pool execution."""
        try:
            # Parse email content to extract components
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
            
            # Use the email_one_line_summary prompty template
            inputs = {
                'context': f'Summary type: {summary_type}',
                'username': 'User',  # Default username
                'subject': subject,
                'sender': sender,
                'date': 'Recent',
                'body': body
            }
            
            result = self.ai_processor.execute_prompty('email_one_line_summary.prompty', inputs)
            
            # Process result
            summary_text = str(result).strip() if result else "Unable to generate summary"
            
            # Generate key points (simple extraction)
            key_points = []
            if len(summary_text) > 20:  # If we have a meaningful summary
                # Extract potential key points from the summary
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
        
        loop = asyncio.get_event_loop()
        
        try:
            result = await loop.run_in_executor(
                None,
                self._analyze_holistically_sync,
                emails
            )
            return result
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
            # Convert emails to format expected by AIProcessor
            email_data_list = []
            for email in emails:
                email_data = {
                    'entry_id': email.get('id', ''),
                    'subject': email.get('subject', ''),
                    'sender': email.get('sender', email.get('from', '')),
                    'sender_name': email.get('sender_name', email.get('from', '')),
                    'received_time': email.get('date', email.get('received_time', '')),
                    'body': email.get('body', email.get('content', ''))
                }
                email_data_list.append(email_data)
            
            # Use AIProcessor's holistic analysis
            analysis, notes = self.ai_processor.analyze_inbox_holistically(email_data_list)
            
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
    
    async def get_available_templates(self) -> Dict[str, Any]:
        """Get list of available prompt templates.
        
        Returns:
            Dict containing template names and descriptions
        """
        templates_dir = Path(__file__).parent.parent.parent / "prompts"
        
        if not templates_dir.exists():
            return {
                "templates": [],
                "descriptions": {}
            }
        
        templates = []
        descriptions = {}
        
        for template_file in templates_dir.glob("*.prompty"):
            template_name = template_file.name
            templates.append(template_name)
            
            # Try to read description from template
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract description from YAML frontmatter
                    if content.startswith('---'):
                        parts = content.split('---', 2)
                        if len(parts) >= 2:
                            yaml_content = parts[1]
                            for line in yaml_content.split('\n'):
                                if line.strip().startswith('description:'):
                                    desc = line.split('description:', 1)[1].strip()
                                    descriptions[template_name] = desc.strip('"\'')
                                    break
            except Exception:
                descriptions[template_name] = "No description available"
        
        return {
            "templates": sorted(templates),
            "descriptions": descriptions
        }


def get_ai_service() -> AIService:
    """FastAPI dependency for AI service (following T1's pattern)."""
    return AIService()