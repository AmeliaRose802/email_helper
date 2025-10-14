"""AI Processor Adapter for Backend Integration.

This module provides an adapter that wraps the existing AIProcessor class
to implement the AIProvider interface, enabling seamless integration with
the FastAPI backend without duplicating existing AI functionality.

The adapter maintains full backward compatibility while providing a clean
interface for dependency injection and testing.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add src to Python path if needed
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.interfaces import AIProvider
from ai_processor import AIProcessor


class AIProcessorAdapter(AIProvider):
    """Adapter wrapping AIProcessor to implement AIProvider interface.
    
    This adapter delegates all AI operations to the existing AIProcessor
    implementation, providing a standardized interface for the backend API
    without duplicating functionality.
    
    The adapter handles:
    - Email classification using Azure OpenAI
    - Action item extraction and analysis
    - Batch email analysis for relationships
    - Summary generation for different email types
    - User context integration (job role, skills)
    - Accuracy tracking and feedback collection
    
    Attributes:
        ai_processor (AIProcessor): Wrapped AI processor instance
        initialized (bool): Initialization status flag
    
    Example:
        >>> adapter = AIProcessorAdapter()
        >>> result = adapter.classify_email(email_content)
        >>> print(result['category'])
        'required_personal_action'
    """
    
    def __init__(self, ai_processor: Optional[AIProcessor] = None):
        """Initialize the adapter with optional AIProcessor instance.
        
        Args:
            ai_processor: Optional existing AIProcessor instance.
                         If None, creates a new instance.
        """
        self.ai_processor = ai_processor or AIProcessor()
        self.initialized = True
    
    def classify_email(
        self, 
        email_content: str, 
        context: str = ""
    ) -> Dict[str, Any]:
        """Classify an email and return structured results.
        
        This method wraps AIProcessor's classification functionality,
        using the enhanced classification with explanation method for
        better accuracy and transparency.
        
        Args:
            email_content: Full email text including subject and body
            context: Additional context for classification (optional)
        
        Returns:
            Dictionary with classification results:
            - category: Primary classification category
            - confidence: Confidence score (0.0 to 1.0)
            - reasoning: Explanation of classification decision
            - alternatives: Alternative category suggestions
            - requires_review: Boolean indicating if manual review needed
        
        Example:
            >>> result = adapter.classify_email("Subject: Meeting tomorrow\\n\\nJoin us for...")
            >>> print(result)
            {
                'category': 'optional_event',
                'confidence': 0.85,
                'reasoning': 'Email contains meeting invitation...',
                'alternatives': [{'category': 'work_relevant', 'confidence': 0.75}],
                'requires_review': False
            }
        """
        try:
            # Use the enhanced classification method with explanation
            result = self.ai_processor.classify_email_with_explanation(
                email_content=email_content,
                learning_data=[]  # Empty learning data for now
            )
            
            # Ensure result is in standardized format
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
            print(f"Error in email classification: {e}")
            # Return safe fallback
            return {
                'category': 'work_relevant',
                'confidence': 0.5,
                'reasoning': f'Classification failed: {str(e)}',
                'alternatives': [],
                'requires_review': True,
                'error': str(e)
            }
    
    def analyze_batch(
        self, 
        emails: List[Dict[str, Any]], 
        context: str = ""
    ) -> Dict[str, Any]:
        """Analyze a batch of emails for relationships and priority.
        
        This method performs holistic analysis across multiple emails to identify:
        - Related emails and conversation threads
        - Priority and urgency indicators
        - Action items across multiple emails
        - Overall inbox health and organization
        
        Args:
            emails: List of email dictionaries with content
            context: Additional context for analysis (optional)
        
        Returns:
            Dictionary with batch analysis results:
            - total_emails: Count of emails analyzed
            - high_priority: Count of high-priority emails
            - action_required: Count of emails needing action
            - threads: Identified conversation threads
            - recommendations: Suggested actions
            - summary: Overall batch summary
        
        Example:
            >>> emails = [{'subject': '...', 'body': '...'}, ...]
            >>> result = adapter.analyze_batch(emails)
            >>> print(result['high_priority'])
            5
        """
        try:
            # Prepare emails for holistic analysis
            email_contexts = []
            for email in emails:
                subject = email.get('subject', 'No subject')
                sender = email.get('sender', 'Unknown')
                body = email.get('body', '')
                
                email_text = f"Subject: {subject}\nFrom: {sender}\n\n{body}"
                email_contexts.append(email_text)
            
            # Use AIProcessor's holistic analysis
            analysis = self.ai_processor.holistic_inbox_analysis(
                emails=emails,
                context=context
            )
            
            # Process and structure the results
            result = {
                'total_emails': len(emails),
                'high_priority': 0,
                'action_required': 0,
                'threads': [],
                'recommendations': [],
                'summary': ''
            }
            
            # Extract structured data from analysis
            if isinstance(analysis, dict):
                result.update({
                    'high_priority': analysis.get('high_priority_count', 0),
                    'action_required': analysis.get('action_required_count', 0),
                    'threads': analysis.get('conversation_threads', []),
                    'recommendations': analysis.get('recommendations', []),
                    'summary': analysis.get('summary', '')
                })
            elif isinstance(analysis, str):
                # Parse string result if needed
                result['summary'] = analysis
                
                # Simple heuristic counting from emails
                for email in emails:
                    if 'required' in email.get('subject', '').lower():
                        result['action_required'] += 1
                    if 'urgent' in email.get('subject', '').lower():
                        result['high_priority'] += 1
            
            return result
            
        except Exception as e:
            print(f"Error in batch analysis: {e}")
            # Return safe fallback
            return {
                'total_emails': len(emails),
                'high_priority': 0,
                'action_required': 0,
                'threads': [],
                'recommendations': ['Unable to analyze batch due to error'],
                'summary': f'Batch analysis failed: {str(e)}',
                'error': str(e)
            }
    
    def extract_action_items(
        self, 
        email_content: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """Extract action items from email content.
        
        Args:
            email_content: Full email text
            context: Additional context
        
        Returns:
            Dictionary with action item details:
            - action_items: List of extracted action items
            - due_date: Extracted deadline
            - urgency: Urgency level (high/medium/low)
            - action_required: Summary of required action
            - explanation: Detailed explanation
            - relevance: Relevance assessment
            - links: Extracted relevant links
        """
        try:
            # Parse email content
            lines = email_content.split('\n')
            subject = "No subject"
            sender = "Unknown sender"
            body = email_content
            
            for line in lines[:5]:
                if line.startswith('Subject:'):
                    subject = line.replace('Subject:', '').strip()
                elif line.startswith('From:'):
                    sender = line.replace('From:', '').strip()
                elif line.strip() == '':
                    body = '\n'.join(lines[lines.index(line)+1:])
                    break
            
            # Use summerize_action_item prompty
            inputs = {
                'context': context,
                'username': 'User',
                'subject': subject,
                'sender': sender,
                'date': 'Recent',
                'body': body
            }
            
            result = self.ai_processor.execute_prompty(
                'summerize_action_item.prompty',
                inputs
            )
            
            # Parse and structure result
            if isinstance(result, dict):
                return {
                    'action_items': [result.get('action_required', 'Review email')] if result.get('action_required') else [],
                    'due_date': result.get('due_date'),
                    'urgency': 'medium',
                    'action_required': result.get('action_required'),
                    'explanation': result.get('explanation'),
                    'relevance': result.get('relevance'),
                    'links': result.get('links', [])
                }
            else:
                # Fallback parsing
                return {
                    'action_items': ['Review email content'],
                    'due_date': 'No specific deadline',
                    'urgency': 'medium',
                    'action_required': str(result),
                    'explanation': 'Action items extracted',
                    'relevance': 'Requires review',
                    'links': []
                }
                
        except Exception as e:
            print(f"Error extracting action items: {e}")
            return {
                'action_items': [],
                'due_date': None,
                'urgency': 'unknown',
                'action_required': 'Unable to extract action items',
                'explanation': f'Error: {str(e)}',
                'relevance': 'Unknown',
                'links': [],
                'error': str(e)
            }
    
    def generate_summary(
        self,
        email_content: str,
        summary_type: str = "brief"
    ) -> Dict[str, Any]:
        """Generate email summary.
        
        Args:
            email_content: Email content to summarize
            summary_type: Type of summary (brief or detailed)
        
        Returns:
            Dictionary with summary and key points
        """
        try:
            # Parse email content
            lines = email_content.split('\n')
            subject = "No subject"
            sender = "Unknown sender"
            body = email_content
            
            for line in lines[:5]:
                if line.startswith('Subject:'):
                    subject = line.replace('Subject:', '').strip()
                elif line.startswith('From:'):
                    sender = line.replace('From:', '').strip()
                elif line.strip() == '':
                    body = '\n'.join(lines[lines.index(line)+1:])
                    break
            
            # Use email_one_line_summary prompty
            inputs = {
                'context': f'Summary type: {summary_type}',
                'username': 'User',
                'subject': subject,
                'sender': sender,
                'date': 'Recent',
                'body': body
            }
            
            result = self.ai_processor.execute_prompty(
                'email_one_line_summary.prompty',
                inputs
            )
            
            summary_text = str(result).strip() if result else "Unable to generate summary"
            
            # Extract key points
            key_points = []
            if len(summary_text) > 20:
                sentences = summary_text.split('.')
                key_points = [s.strip() for s in sentences if len(s.strip()) > 10][:3]
            
            return {
                'summary': summary_text,
                'key_points': key_points,
                'confidence': 0.8 if len(summary_text) > 20 else 0.5
            }
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            return {
                'summary': f'Unable to generate summary: {str(e)}',
                'key_points': [],
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _requires_review(self, category: str, confidence: float) -> bool:
        """Determine if manual review is required based on category and confidence.
        
        Args:
            category: Classification category
            confidence: Confidence score
        
        Returns:
            bool: True if manual review required, False otherwise
        """
        # Get threshold from AIProcessor
        threshold = self.ai_processor.CONFIDENCE_THRESHOLDS.get(
            category, 
            1.0  # Default to always review if category not found
        )
        
        # Require review if confidence is below threshold
        return confidence < threshold
