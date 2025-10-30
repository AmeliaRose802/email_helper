"""COM Action Item Extraction Service.

Handles extraction of action items from emails using Azure OpenAI.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class COMActionExtractionService:
    """Service for extracting action items from emails.
    
    Uses prompty templates to extract structured action item data.
    """

    def __init__(self, ai_processor, azure_config):
        """Initialize action extraction service.
        
        Args:
            ai_processor: AIProcessor instance for AI operations
            azure_config: Azure OpenAI configuration
        """
        self.ai_processor = ai_processor
        self.azure_config = azure_config
        
        # Performance optimization: Cache user settings
        self._user_settings_cache: Optional[Tuple[str, str, str]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=10)

    def _get_cached_user_settings(self) -> Tuple[str, str, str]:
        """Get user settings with caching."""
        now = datetime.now()
        if (self._user_settings_cache is not None and
            self._cache_timestamp is not None and
            now < self._cache_timestamp + self._cache_ttl):
            return self._user_settings_cache

        job_role_context = ""
        custom_interests = ""
        username = ""

        try:
            import sqlite3
            db_path = Path(__file__).parent.parent.parent / 'runtime_data' / 'database' / 'email_helper_history.db'

            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT username, job_context, newsletter_interests FROM user_settings WHERE user_id = 1")
                row = cursor.fetchone()
                conn.close()

                if row:
                    username = row[0] or ""
                    job_role_context = row[1] or ""
                    custom_interests = row[2] or ""
        except Exception as e:
            logger.debug(f"[Action Extraction] Database load failed: {e}")

        try:
            user_data_path = Path(__file__).parent.parent.parent / 'user_specific_data'

            if not job_role_context and (user_data_path / 'job_role_context.md').exists():
                job_role_context = (user_data_path / 'job_role_context.md').read_text(encoding='utf-8')

            if not custom_interests and (user_data_path / 'custom_interests.md').exists():
                custom_interests = (user_data_path / 'custom_interests.md').read_text(encoding='utf-8')

            if not username and (user_data_path / 'username.txt').exists():
                username = (user_data_path / 'username.txt').read_text(encoding='utf-8').strip()
        except Exception as e:
            logger.warning(f"[Action Extraction] File fallback failed: {e}")

        self._user_settings_cache = (job_role_context, custom_interests, username)
        self._cache_timestamp = now
        return self._user_settings_cache

    def invalidate_user_settings_cache(self):
        """Invalidate user settings cache."""
        self._user_settings_cache = None
        self._cache_timestamp = None

    async def extract_action_items(
        self,
        email_content: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract action items from email content.

        Args:
            email_content: Full email text
            context: Optional additional context

        Returns:
            Dictionary with action item details
        """
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
        """Synchronous action item extraction."""
        try:
            lines = email_content.split('\n')
            subject = "No subject"
            sender = "Unknown sender"
            date = "Recent"
            body = email_content

            for i, line in enumerate(lines[:10]):
                if line.startswith('Subject:'):
                    subject = line.replace('Subject:', '').strip()
                elif line.startswith('From:'):
                    sender = line.replace('From:', '').strip()
                elif line.startswith('Date:'):
                    date = line.replace('Date:', '').strip()
                elif line.strip() == '' and i > 0:
                    body = '\n'.join(lines[i+1:])
                    break

            if body == email_content:
                body_start = 0
                for i, line in enumerate(lines[:5]):
                    if line.startswith('Subject:') or line.startswith('From:') or line.startswith('Date:'):
                        body_start = i + 1
                if body_start > 0:
                    body = '\n'.join(lines[body_start:])

            job_role_context, custom_interests, username = self._get_cached_user_settings()

            if not username:
                username = "User"
                if hasattr(self.ai_processor, 'get_username'):
                    username = self.ai_processor.get_username()

            inputs = {
                "context": job_role_context or context or "Email analysis for action item extraction",
                "username": username,
                "subject": subject,
                "sender": sender,
                "date": date,
                "body": body[:8000]
            }

            if custom_interests:
                inputs["custom_interests"] = custom_interests

            result = self.ai_processor.execute_prompty(
                "summerize_action_item.prompty",
                inputs=inputs
            )

            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    logger.warning(f"[Action Extraction] Failed to parse JSON")
                    result = {
                        "action_required": "Review email content",
                        "explanation": "Unable to parse structured response",
                        "due_date": "",
                        "relevance": "",
                        "links": [],
                        "error": "JSON parse failed"
                    }

            if not isinstance(result, dict):
                result = {
                    "action_required": "Review email content",
                    "explanation": "AI returned non-structured response",
                    "due_date": "",
                    "relevance": "",
                    "links": [],
                    "error": "Invalid response format"
                }

            response = {
                "action_items": [result] if result.get("action_required") else [],
                "action_required": result.get("action_required", "No action required"),
                "due_date": result.get("due_date", ""),
                "explanation": result.get("explanation", ""),
                "relevance": result.get("relevance", ""),
                "links": result.get("links", []),
                "confidence": 0.8
            }

            if "error" in result:
                response["error"] = result["error"]

            return response

        except Exception as e:
            raise
