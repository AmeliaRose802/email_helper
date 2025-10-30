"""COM Email Summarization Service.

Handles generation of email summaries using Azure OpenAI.
"""

import asyncio
import logging
import os
import sqlite3
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class COMSummarizationService:
    """Service for generating email summaries.
    
    Supports multiple summary types: brief, detailed, newsletter, FYI.
    """

    def __init__(self, ai_processor, azure_config):
        """Initialize summarization service.
        
        Args:
            ai_processor: AIProcessor instance for AI operations
            azure_config: Azure OpenAI configuration
        """
        self.ai_processor = ai_processor
        self.azure_config = azure_config

    async def generate_summary(
        self,
        email_content: str,
        summary_type: str = "brief"
    ) -> Dict[str, Any]:
        """Generate a summary of email content.

        Args:
            email_content: Full email text
            summary_type: Type of summary ("brief", "detailed", "newsletter", "fyi")

        Returns:
            Dictionary with summary details
        """
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
        """Synchronous summary generation."""
        try:
            lines = email_content.split('\n')
            subject = ""
            sender = ""
            body = email_content

            for i, line in enumerate(lines[:10]):
                if line.startswith('Subject:'):
                    subject = line.replace('Subject:', '').strip()
                elif line.startswith('From:'):
                    sender = line.replace('From:', '').strip()
                elif line.strip() == '' and (subject or sender):
                    body = '\n'.join(lines[i+1:])
                    break

            if not subject and not sender:
                body = email_content

            # Load user context
            context = ""
            username = "User"
            custom_interests = ""
            try:
                user_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'user_specific_data')

                # Try database first
                try:
                    db_path = Path(__file__).parent.parent.parent / 'runtime_data' / 'email_helper_history.db'
                    if db_path.exists():
                        conn = sqlite3.connect(str(db_path))
                        cursor = conn.execute("SELECT username, job_context, newsletter_interests FROM user_settings WHERE user_id = 1")
                        row = cursor.fetchone()
                        if row:
                            if row[0]:
                                username = row[0]
                            if row[1]:
                                context = row[1]
                            if row[2]:
                                custom_interests = row[2]
                        conn.close()
                except Exception:
                    pass

                # File fallback
                if not context:
                    job_context_path = os.path.join(user_data_dir, 'job_role_context.md')
                    if os.path.exists(job_context_path):
                        with open(job_context_path, 'r', encoding='utf-8') as f:
                            context = f.read()

                if not custom_interests:
                    custom_interests_path = os.path.join(user_data_dir, 'custom_interests.md')
                    if os.path.exists(custom_interests_path):
                        with open(custom_interests_path, 'r', encoding='utf-8') as f:
                            custom_interests = f.read()

                if username == "User":
                    username_path = os.path.join(user_data_dir, 'username.txt')
                    if os.path.exists(username_path):
                        with open(username_path, 'r', encoding='utf-8') as f:
                            username = f.read().strip()
            except Exception:
                pass

            inputs = {
                "context": context,
                "username": username,
                "subject": subject,
                "sender": sender,
                "date": "",
                "body": body
            }

            if custom_interests:
                inputs["custom_interests"] = custom_interests

            # Select prompt based on summary type
            if summary_type == "detailed":
                if custom_interests:
                    prompt_file = "newsletter_summary_custom.prompty"
                else:
                    prompt_file = "newsletter_summary.prompty"
            elif summary_type == "fyi" or summary_type == "brief":
                prompt_file = "fyi_summary.prompty"
            else:
                prompt_file = "email_one_line_summary.prompty"

            result = self.ai_processor.execute_prompty(
                prompt_file,
                inputs=inputs
            )

            if isinstance(result, str):
                summary_text = result.strip()
            else:
                summary_text = str(result)

            # Extract key points
            key_points = []
            if summary_text:
                sentences = [s.strip() for s in summary_text.split('.') if s.strip()]
                key_points = sentences[:3]

            return {
                "summary": summary_text if summary_text else "Unable to generate summary",
                "key_points": key_points,
                "confidence": 0.8 if summary_text else 0.5
            }

        except Exception as e:
            raise
