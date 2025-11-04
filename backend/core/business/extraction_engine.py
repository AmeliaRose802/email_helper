"""Email Extraction Engine - Action item extraction and summarization.

Pure business logic for extracting action items, generating summaries,
and processing email content for different categories.

This is PURE BUSINESS LOGIC - no async, no FastAPI, no framework dependencies.
"""

import logging
from typing import Dict
from datetime import datetime

from backend.core.infrastructure.json_utils import parse_json_with_fallback
from backend.core.infrastructure.text_utils import (
    clean_markdown_formatting,
    truncate_with_ellipsis,
    add_bullet_if_needed
)

logger = logging.getLogger(__name__)


class ExtractionEngine:
    """Handles content extraction and summarization for emails.

    This service provides:
    - Action item extraction with deadlines and relevance
    - One-line email summaries
    - FYI summaries
    - Newsletter summaries
    - Event relevance assessment
    """

    def __init__(self, prompt_executor, context_manager):
        """Initialize extraction service.

        Args:
            prompt_executor: Object with execute_prompty method
            context_manager: UserContextManager for context
        """
        self.prompt_executor = prompt_executor
        self.context_manager = context_manager

    def extract_action_item_details(self, email_content: dict, context: str = "") -> Dict:
        """Extract structured action item details from email.

        Args:
            email_content: Email data dict
            context: Additional context string

        Returns:
            dict: Action details with action_required, due_date, explanation, links, relevance
        """
        inputs = self.context_manager.create_email_inputs(email_content, context)
        result = self.prompt_executor.execute_prompty('summerize_action_item.prompty', inputs)

        if not result or not result.strip():
            return {
                "action_required": f"Review email: {email_content.get('subject', 'Unknown')[:100]}",
                "due_date": "No specific deadline",
                "explanation": "AI processing unavailable - please review manually",
                "links": [],
                "relevance": "Manual review needed"
            }

        fallback_data = {
            "action_required": f"Review email: {email_content.get('subject', 'Unknown')[:100]}",
            "due_date": "No specific deadline",
            "explanation": "AI parsing failed - please review manually",
            "links": [],
            "relevance": "Unable to parse - manual review needed"
        }

        return parse_json_with_fallback(result, fallback_data)

    def generate_email_summary(self, email_content: dict) -> str:
        """Generate concise one-line email summary.

        Args:
            email_content: Email data dict

        Returns:
            str: One-line summary, max 120 characters
        """
        context = self.context_manager.get_standard_context()
        inputs = self.context_manager.create_email_inputs(email_content, context)
        result = self.prompt_executor.execute_prompty('email_one_line_summary.prompty', inputs)

        if result and result.strip():
            summary = clean_markdown_formatting(result.strip().split('\n')[0])
            return truncate_with_ellipsis(summary, 120)

        return f"No summary - {email_content.get('subject', 'Unknown')[:50]}"

    def generate_fyi_summary(self, email_content: dict, context: str) -> str:
        """Generate FYI-specific summary with bullet point.

        Args:
            email_content: Email data dict
            context: Context string

        Returns:
            str: Bulleted FYI summary
        """
        inputs = self.context_manager.create_email_inputs(email_content, context)
        result = self.prompt_executor.execute_prompty('fyi_summary.prompty', inputs)

        if result and result.strip():
            summary = result.strip().split('\n')[0]
            return add_bullet_if_needed(summary)

        return f"• {email_content.get('subject', 'Unknown')[:80]}"

    def generate_newsletter_summary(self, email_content: dict, context: str) -> str:
        """Generate newsletter-specific summary.

        Args:
            email_content: Email data dict
            context: Context string

        Returns:
            str: Newsletter summary with formatting
        """
        inputs = self.context_manager.create_email_inputs(email_content, context)
        result = self.prompt_executor.execute_prompty('newsletter_summary.prompty', inputs)

        if result and result.strip():
            return clean_markdown_formatting(result.strip())

        sender = email_content.get('sender', 'Unknown')
        subject = email_content.get('subject', 'No summary')
        return f"Newsletter from {sender}: {subject}"

    def assess_event_relevance(self, subject: str, body: str, context: str) -> str:
        """Assess relevance of event invitation.

        Args:
            subject: Event subject line
            body: Event email body
            context: User context

        Returns:
            str: Relevance assessment text
        """
        email_content = {
            'subject': subject,
            'sender': 'Unknown',
            'body': body[:3000],
            'date': ''
        }

        inputs = self.context_manager.create_email_inputs(email_content, context)
        inputs['current_date'] = datetime.now().strftime('%Y-%m-%d')

        result = self.prompt_executor.execute_prompty('event_relevance_assessment.prompty', inputs)

        if result and result.strip():
            response = result.strip()
            # Handle fallback messages
            if any(phrase in response.lower() for phrase in
                   ['content filter', 'unavailable', 'blocked']):
                return response
            return response

        return "Professional development opportunity"
