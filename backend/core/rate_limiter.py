"""Rate limiting utility for Email Helper API.

This module provides centralized rate limiting functionality to prevent
overwhelming external services, particularly Azure OpenAI.
"""

import asyncio
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """Centralized rate limiter for external service calls."""
    
    def __init__(self):
        """Initialize rate limiter with default delays."""
        self.delays = {
            'ai_classification': 0.2,  # 200ms between classifications
            'ai_extraction': 0.3,       # 300ms for extraction
            'ai_holistic': 0.5,         # 500ms for holistic analysis
            'ai_summary': 0.2,          # 200ms for summaries
            'database': 0.0,            # No delay for DB operations
            'default': 0.1
        }
    
    async def wait(self, operation_type: str = 'default') -> None:
        """Add rate limiting delay for specified operation type.
        
        Args:
            operation_type: Type of operation requiring rate limiting
        """
        delay = self.delays.get(operation_type, self.delays['default'])
        
        if delay > 0:
            logger.debug(f"[RATE] Applying {delay}s delay for {operation_type}")
            await asyncio.sleep(delay)
    
    async def ai_request_delay(self) -> None:
        """Standard delay for AI requests."""
        await self.wait('ai_classification')
    
    async def ai_extraction_delay(self) -> None:
        """Delay for AI extraction operations."""
        await self.wait('ai_extraction')
    
    async def holistic_analysis_delay(self) -> None:
        """Delay for holistic analysis operations."""
        await self.wait('ai_holistic')
    
    async def database_delay(self) -> None:
        """Minimal delay for database operations."""
        await self.wait('database')


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    
    return _rate_limiter
