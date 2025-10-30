"""COM Duplicate Detection Service.

Handles detection and deduplication of similar emails and content.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class COMDuplicateDetectionService:
    """Service for detecting and deduplicating emails and content.
    
    Uses AI to identify duplicate or highly similar content items.
    """

    def __init__(self, ai_processor, azure_config):
        """Initialize duplicate detection service.
        
        Args:
            ai_processor: AIProcessor instance for AI operations
            azure_config: Azure OpenAI configuration
        """
        self.ai_processor = ai_processor
        self.azure_config = azure_config

    async def detect_duplicates(
        self,
        emails: List[Dict[str, Any]]
    ) -> List[str]:
        """Detect duplicate emails in a list.

        Args:
            emails: List of email dictionaries with 'id', 'subject', 'content'

        Returns:
            List of email IDs that are duplicates
        """
        loop = asyncio.get_event_loop()

        try:
            result = await loop.run_in_executor(
                None,
                self._detect_duplicates_sync,
                emails
            )
            return result
        except Exception as e:
            logger.error(f"Error detecting duplicates: {e}")
            return []

    def _detect_duplicates_sync(self, emails: List[Dict[str, Any]]) -> List[str]:
        """Synchronous duplicate detection."""
        try:
            if len(emails) <= 1:
                return []

            email_summaries = []
            for email in emails:
                summary = {
                    "id": email.get("id", ""),
                    "subject": email.get("subject", ""),
                    "content": email.get("content", "")[:500]
                }
                email_summaries.append(summary)

            inputs = {
                "emails": json.dumps(email_summaries)
            }

            result = self.ai_processor.execute_prompty(
                "email_duplicate_detection.prompty",
                inputs=inputs
            )

            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    return []

            if isinstance(result, dict):
                return result.get("duplicate_ids", [])
            elif isinstance(result, list):
                return result
            else:
                return []

        except Exception as e:
            logger.error(f"Error in duplicate detection: {e}")
            return []

    async def deduplicate_content(
        self,
        content_items: List[Dict[str, Any]],
        content_type: str = "fyi"
    ) -> Dict[str, Any]:
        """Deduplicate similar content items using AI analysis.

        Args:
            content_items: List of content dictionaries with 'id', 'content', metadata
            content_type: Type of content ('fyi', 'newsletter', etc.)

        Returns:
            Dictionary with deduplication results
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self._deduplicate_content_sync,
                content_items,
                content_type
            )

        except Exception as e:
            logger.error(f"Error in content deduplication: {e}")
            return {
                "deduplicated_items": content_items,
                "removed_duplicates": [],
                "statistics": {
                    "original_count": len(content_items),
                    "deduplicated_count": len(content_items),
                    "duplicates_removed": 0,
                    "merge_operations": 0,
                    "error": str(e)
                }
            }

    def _deduplicate_content_sync(
        self,
        content_items: List[Dict[str, Any]],
        content_type: str
    ) -> Dict[str, Any]:
        """Synchronous content deduplication."""
        try:
            formatted_items = []
            for idx, item in enumerate(content_items):
                formatted_items.append({
                    "id": item.get("id", idx),
                    "content": item.get("content", ""),
                    "metadata": item.get("metadata", {})
                })

            inputs = {
                "content_items": json.dumps(formatted_items, indent=2),
                "content_type": content_type,
                "threshold": "high"
            }

            result = self.ai_processor.execute_prompty(
                "content_deduplication.prompty",
                inputs=inputs
            )

            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    return {
                        "deduplicated_items": content_items,
                        "removed_duplicates": [],
                        "statistics": {
                            "original_count": len(content_items),
                            "deduplicated_count": len(content_items),
                            "duplicates_removed": 0,
                            "merge_operations": 0,
                            "error": "Failed to parse AI response"
                        }
                    }

            if isinstance(result, dict):
                return {
                    "deduplicated_items": result.get("deduplicated_items", content_items),
                    "removed_duplicates": result.get("removed_duplicates", []),
                    "statistics": result.get("statistics", {
                        "original_count": len(content_items),
                        "deduplicated_count": len(result.get("deduplicated_items", content_items)),
                        "duplicates_removed": len(result.get("removed_duplicates", [])),
                        "merge_operations": len(result.get("removed_duplicates", []))
                    })
                }
            else:
                return {
                    "deduplicated_items": content_items,
                    "removed_duplicates": [],
                    "statistics": {
                        "original_count": len(content_items),
                        "deduplicated_count": len(content_items),
                        "duplicates_removed": 0,
                        "merge_operations": 0,
                        "error": "Unexpected AI response format"
                    }
                }

        except Exception as e:
            logger.error(f"Error in _deduplicate_content_sync: {e}")
            return {
                "deduplicated_items": content_items,
                "removed_duplicates": [],
                "statistics": {
                    "original_count": len(content_items),
                    "deduplicated_count": len(content_items),
                    "duplicates_removed": 0,
                    "merge_operations": 0,
                    "error": str(e)
                }
            }
