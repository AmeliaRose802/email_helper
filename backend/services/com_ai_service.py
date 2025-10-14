"""COM AI Service Adapter for FastAPI Email Helper API.

This module provides a FastAPI-compatible adapter that wraps the existing 
AIProcessor class for COM-based integration. It reuses existing Azure OpenAI 
configuration and prompty files while providing async patterns for FastAPI.

The COMAIService handles:
- Email classification using Azure OpenAI
- Action item extraction and analysis
- Email summarization for different types
- Duplicate detection across emails
- Batch email analysis for relationships
- Prompty template management

This adapter follows T1.2 requirements for Wave 1 foundation tasks.
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


class COMAIService:
    """COM AI service adapter for FastAPI integration.
    
    This service wraps the existing AIProcessor class to provide async
    AI operations for COM-based email processing in the FastAPI backend.
    
    The service maintains compatibility with existing:
    - Azure OpenAI configuration from src/azure_config.py
    - Prompty files in prompts/ directory
    - Email classification and analysis features
    - Accuracy tracking and feedback collection
    
    Attributes:
        ai_processor (AIProcessor): Wrapped AI processor instance
        azure_config: Azure OpenAI configuration
        _initialized (bool): Lazy initialization status flag
    
    Example:
        >>> service = COMAIService()
        >>> result = await service.classify_email("Subject: Meeting\\n\\nJoin us...")
        >>> print(result['category'])
        'optional_event'
    """
    
    def __init__(self):
        """Initialize COM AI service with lazy loading."""
        self.ai_processor = None
        self.azure_config = None
        self._initialized = False
        
    def _ensure_initialized(self):
        """Lazy initialization of AI components.
        
        Raises:
            RuntimeError: If AI dependencies are not available or initialization fails
        """
        if not self._initialized:
            if AIProcessor is None or get_azure_config is None:
                raise RuntimeError("AI dependencies not available")
            
            try:
                self.ai_processor = AIProcessor()
                self.azure_config = get_azure_config()
                self._initialized = True
            except Exception as e:
                raise RuntimeError(f"Failed to initialize AI components: {e}")
    
    async def classify_email(
        self, 
        email_content: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Classify an email and return structured results.
        
        This method uses the existing AIProcessor classification with
        explanation functionality to provide detailed categorization.
        
        Args:
            email_content: Full email text including subject, sender, and body
            context: Optional additional context for classification
            
        Returns:
            Dictionary with classification results:
            - category (str): Primary classification category
            - confidence (float): Confidence score (0.0 to 1.0)
            - reasoning (str): Explanation of classification decision
            - alternatives (List): Alternative category suggestions
            - requires_review (bool): Whether manual review is needed
            - error (str, optional): Error message if classification failed
        
        Example:
            >>> result = await service.classify_email("Subject: Report\\n\\nReview this.")
            >>> print(result['category'])
            'required_personal_action'
        """
        self._ensure_initialized()
        
        # Run CPU-bound AI processing in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        
        try:
            result = await loop.run_in_executor(
                None,
                self._classify_email_sync,
                email_content,
                context or ""
            )
            return result
        except Exception as e:
            return {
                "category": "work_relevant",
                "confidence": 0.5,
                "reasoning": f"Classification failed: {str(e)}",
                "alternatives": [],
                "requires_review": True,
                "error": str(e)
            }
    
    def _classify_email_sync(self, email_content: str, context: str) -> Dict[str, Any]:
        """Synchronous email classification for thread pool execution.
        
        Args:
            email_content: Full email text
            context: Additional context
            
        Returns:
            Classification result dictionary
        """
        try:
            # Use the enhanced classification method with explanation
            result = self.ai_processor.classify_email_with_explanation(
                email_content=email_content,
                learning_data=[]  # Empty learning data for now
            )
            
            # Ensure result is in expected format
            if isinstance(result, dict):
                category = result.get('category', 'work_relevant')
                confidence = result.get('confidence', 0.8)
                
                # Determine if review is required based on confidence thresholds
                requires_review = self._requires_review(category, confidence)
                
                return {
                    'category': category,
                    'confidence': confidence,
                    'reasoning': result.get('explanation', 'Email classified'),
                    'alternatives': result.get('alternatives', []),
                    'requires_review': requires_review
                }
            else:
                # Fallback for non-dict results
                category = str(result) if result else 'work_relevant'
                return {
                    'category': category,
                    'confidence': 0.8,
                    'reasoning': 'Email classified successfully',
                    'alternatives': [],
                    'requires_review': True  # Default to requiring review
                }
                
        except Exception as e:
            raise  # Re-raise to be caught by async wrapper
    
    def _requires_review(self, category: str, confidence: float) -> bool:
        """Determine if classification requires manual review.
        
        Uses asymmetric confidence thresholds from AIProcessor.
        
        Args:
            category: Classification category
            confidence: Confidence score (0.0 to 1.0)
            
        Returns:
            True if manual review is required, False otherwise
        """
        if not hasattr(self.ai_processor, 'CONFIDENCE_THRESHOLDS'):
            return True  # Default to requiring review if thresholds unavailable
            
        threshold = self.ai_processor.CONFIDENCE_THRESHOLDS.get(category, 1.0)
        return confidence < threshold
    
    async def extract_action_items(
        self,
        email_content: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract action items from email content.
        
        Uses the summerize_action_item.prompty template to extract
        structured action item details.
        
        Args:
            email_content: Full email text
            context: Optional additional context
            
        Returns:
            Dictionary with action item details:
            - action_items (List): List of extracted action items
            - action_required (str): Primary action description
            - due_date (str): Action deadline if available
            - explanation (str): Why this is an action item
            - relevance (str): Relevance to user
            - links (List): Related URLs or attachments
            - confidence (float): Confidence score
            - error (str, optional): Error message if extraction failed
        
        Example:
            >>> result = await service.extract_action_items("Subject: Task\\n\\nComplete by Friday")
            >>> print(result['due_date'])
            '2024-01-15'
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
                "action_required": f"Unable to extract action items: {str(e)}",
                "due_date": "",
                "explanation": "Action item extraction failed",
                "relevance": "",
                "links": [],
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _extract_action_items_sync(self, email_content: str, context: str) -> Dict[str, Any]:
        """Synchronous action item extraction for thread pool execution.
        
        Args:
            email_content: Full email text
            context: Additional context
            
        Returns:
            Action items result dictionary
        """
        try:
            # Use prompty file for action item extraction
            inputs = {
                "email_content": email_content
            }
            
            if context:
                inputs["context"] = context
            
            # Execute the summerize_action_item prompty
            result = self.ai_processor.execute_prompty(
                "summerize_action_item.prompty",
                inputs=inputs
            )
            
            # Parse result if it's a JSON string
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    # Fallback parsing for non-JSON responses
                    result = {
                        "action_required": result[:200] if result else "Review email content",
                        "explanation": "Unable to parse structured response",
                        "due_date": "",
                        "relevance": "",
                        "links": []
                    }
            
            # Ensure dictionary structure
            if not isinstance(result, dict):
                result = {
                    "action_required": str(result),
                    "explanation": "",
                    "due_date": "",
                    "relevance": "",
                    "links": []
                }
            
            # Format response with all expected fields
            return {
                "action_items": [result] if result.get("action_required") else [],
                "action_required": result.get("action_required", "No action required"),
                "due_date": result.get("due_date", ""),
                "explanation": result.get("explanation", ""),
                "relevance": result.get("relevance", ""),
                "links": result.get("links", []),
                "confidence": 0.8  # Default confidence for successful extraction
            }
            
        except Exception as e:
            raise  # Re-raise to be caught by async wrapper
    
    async def generate_summary(
        self,
        email_content: str,
        summary_type: str = "brief"
    ) -> Dict[str, Any]:
        """Generate a summary of email content.
        
        Uses the email_one_line_summary.prompty template for brief summaries.
        
        Args:
            email_content: Full email text
            summary_type: Type of summary ("brief", "detailed", etc.)
            
        Returns:
            Dictionary with summary details:
            - summary (str): Generated summary text
            - key_points (List[str]): Key points from email
            - confidence (float): Confidence score
            - error (str, optional): Error message if generation failed
        
        Example:
            >>> result = await service.generate_summary("Subject: Meeting\\n\\nScheduled for tomorrow")
            >>> print(result['summary'])
            'Meeting scheduled for tomorrow'
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
        """Synchronous summary generation for thread pool execution.
        
        Args:
            email_content: Full email text
            summary_type: Type of summary to generate
            
        Returns:
            Summary result dictionary
        """
        try:
            # Use prompty file for summary generation
            inputs = {
                "email_content": email_content
            }
            
            # Execute the email_one_line_summary prompty for brief summaries
            result = self.ai_processor.execute_prompty(
                "email_one_line_summary.prompty",
                inputs=inputs
            )
            
            # Parse result
            if isinstance(result, str):
                summary_text = result.strip()
            else:
                summary_text = str(result)
            
            # Extract key points from summary
            key_points = []
            if summary_text:
                # Simple key point extraction (split by sentence)
                sentences = [s.strip() for s in summary_text.split('.') if s.strip()]
                key_points = sentences[:3]  # Take up to 3 key points
            
            return {
                "summary": summary_text if summary_text else "Unable to generate summary",
                "key_points": key_points,
                "confidence": 0.8 if summary_text else 0.5
            }
            
        except Exception as e:
            raise  # Re-raise to be caught by async wrapper
    
    async def detect_duplicates(
        self,
        emails: List[Dict[str, Any]]
    ) -> List[str]:
        """Detect duplicate emails in a list.
        
        Uses the email_duplicate_detection.prompty template to identify
        duplicate or very similar emails.
        
        Args:
            emails: List of email dictionaries with 'id', 'subject', 'content'
            
        Returns:
            List of email IDs that are duplicates
        
        Example:
            >>> emails = [{'id': '1', 'subject': 'Test', 'content': 'Hello'}]
            >>> duplicates = await service.detect_duplicates(emails)
            >>> print(duplicates)
            []
        """
        self._ensure_initialized()
        
        loop = asyncio.get_event_loop()
        
        try:
            result = await loop.run_in_executor(
                None,
                self._detect_duplicates_sync,
                emails
            )
            return result
        except Exception as e:
            print(f"Error detecting duplicates: {e}")
            return []  # Return empty list on error
    
    def _detect_duplicates_sync(self, emails: List[Dict[str, Any]]) -> List[str]:
        """Synchronous duplicate detection for thread pool execution.
        
        Args:
            emails: List of email dictionaries
            
        Returns:
            List of duplicate email IDs
        """
        try:
            if len(emails) <= 1:
                return []  # No duplicates possible
            
            # Build input for duplicate detection
            email_summaries = []
            for email in emails:
                summary = {
                    "id": email.get("id", ""),
                    "subject": email.get("subject", ""),
                    "content": email.get("content", "")[:500]  # Truncate long content
                }
                email_summaries.append(summary)
            
            inputs = {
                "emails": json.dumps(email_summaries)
            }
            
            # Execute the email_duplicate_detection prompty
            result = self.ai_processor.execute_prompty(
                "email_duplicate_detection.prompty",
                inputs=inputs
            )
            
            # Parse result
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    return []  # Return empty on parse error
            
            # Extract duplicate IDs
            if isinstance(result, dict):
                return result.get("duplicate_ids", [])
            elif isinstance(result, list):
                return result
            else:
                return []
            
        except Exception as e:
            print(f"Error in duplicate detection: {e}")
            return []
    
    async def get_available_templates(self) -> Dict[str, Any]:
        """Get list of available prompty templates.
        
        Returns:
            Dictionary with template information:
            - templates (List[str]): List of template filenames
            - descriptions (Dict[str, str]): Template descriptions
        
        Example:
            >>> result = await service.get_available_templates()
            >>> print(result['templates'])
            ['email_classifier.prompty', 'action_item.prompty', ...]
        """
        # Get prompts directory from ai_processor
        prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        
        if not prompts_dir.exists():
            return {
                "templates": [],
                "descriptions": {}
            }
        
        # List all .prompty files
        templates = []
        descriptions = {}
        
        for prompty_file in prompts_dir.glob("*.prompty"):
            templates.append(prompty_file.name)
            
            # Try to extract description from file
            try:
                with open(prompty_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Look for description in YAML frontmatter
                    if content.startswith('---'):
                        parts = content.split('---', 2)
                        if len(parts) >= 2:
                            import re
                            desc_match = re.search(r'description:\s*(.+)', parts[1])
                            if desc_match:
                                descriptions[prompty_file.name] = desc_match.group(1).strip()
            except Exception:
                pass  # Skip description if parsing fails
        
        return {
            "templates": sorted(templates),
            "descriptions": descriptions
        }


def get_com_ai_service() -> COMAIService:
    """FastAPI dependency for COM AI service.
    
    Returns:
        COMAIService instance for dependency injection
    
    Example:
        >>> from fastapi import Depends
        >>> @app.get("/classify")
        >>> async def classify(service: COMAIService = Depends(get_com_ai_service)):
        >>>     return await service.classify_email(...)
    """
    return COMAIService()
