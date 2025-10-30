"""AI Summarizer - Email Summarization and Content Generation.

This module handles email summarization tasks including one-line summaries,
FYI summaries, newsletter summaries, and event relevance assessment.
"""

import logging
from datetime import datetime
from utils import clean_markdown_formatting, truncate_with_ellipsis, add_bullet_if_needed
from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class AISummarizer:
    """Handles email summarization and content generation.
    
    This class is responsible for generating various types of summaries
    including one-line summaries, FYI summaries, newsletter summaries,
    and event relevance assessments.
    """
    
    def __init__(self, prompt_manager: PromptManager):
        """Initialize the summarizer.
        
        Args:
            prompt_manager: PromptManager instance for executing prompts
        """
        self.prompt_manager = prompt_manager
    
    def generate_email_summary(self, email_content, context):
        """Generate one-line email summary.
        
        Args:
            email_content: Email data to summarize
            context: Job context and user information
            
        Returns:
            str: One-line email summary
        """
        inputs = self._create_email_inputs(email_content, context)
        result = self.prompt_manager.execute_prompty('email_one_line_summary.prompty', inputs)
        
        if result and result.strip():
            summary = clean_markdown_formatting(result.strip().split('\n')[0])
            return truncate_with_ellipsis(summary, 120)
        return f"No summary - {email_content.get('subject', 'Unknown')[:50]}"
    
    def generate_fyi_summary(self, email_content, context):
        """Generate FYI summary with bullet point.
        
        Args:
            email_content: Email data to summarize
            context: Job context and user information
            
        Returns:
            str: FYI summary with bullet point
        """
        inputs = self._create_email_inputs(email_content, context)
        result = self.prompt_manager.execute_prompty('fyi_summary.prompty', inputs)
        
        if result and result.strip():
            summary = result.strip().split('\n')[0]
            return add_bullet_if_needed(summary)
        return f"• {email_content.get('subject', 'Unknown')[:80]}"
    
    def generate_newsletter_summary(self, email_content, context):
        """Generate newsletter summary.
        
        Args:
            email_content: Email data to summarize
            context: Job context and user information
            
        Returns:
            str: Newsletter summary
        """
        inputs = self._create_email_inputs(email_content, context)
        result = self.prompt_manager.execute_prompty('newsletter_summary.prompty', inputs)
        
        if result and result.strip():
            return clean_markdown_formatting(result.strip())
        return f"Newsletter from {email_content.get('sender', 'Unknown')}: {email_content.get('subject', 'No summary')}"
    
    def assess_event_relevance(self, subject, body, context):
        """Assess event relevance to user's job context.
        
        Args:
            subject: Event subject/title
            body: Event description
            context: Job context and user information
            
        Returns:
            str: Relevance assessment
        """
        email_content = {
            'subject': subject,
            'sender': 'Unknown',
            'body': body[:3000],
            'date': ''
        }
        
        inputs = self._create_email_inputs(email_content, context)
        inputs['current_date'] = datetime.now().strftime('%Y-%m-%d')
        result = self.prompt_manager.execute_prompty('event_relevance_assessment.prompty', inputs)
        
        if result and result.strip():
            response = result.strip()
            # If it's a fallback message, return it as-is
            if any(phrase in response.lower() for phrase in ['content filter', 'unavailable', 'blocked']):
                return response
            return response
        return "Professional development opportunity"
    
    def _create_email_inputs(self, email_content, context):
        """Create input dictionary for email summarization prompts."""
        return {
            'context': context,
            'subject': email_content.get('subject', ''),
            'sender': email_content.get('sender', ''),
            'date': email_content.get('date', ''),
            'body': email_content.get('body', '')[:8000]
        }
