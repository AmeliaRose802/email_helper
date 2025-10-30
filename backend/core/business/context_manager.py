"""User Context Manager - Handles user-specific configuration and context.

This module manages user context data including job role, skills profile,
and other user-specific configuration used for AI processing personalization.
"""

import os
import logging

logger = logging.getLogger(__name__)


class UserContextManager:
    """Manages user-specific context for AI processing.
    
    This class handles loading and providing user context data such as
    job summaries, skills profiles, and role information that helps
    personalize AI responses for the specific user.
    
    Attributes:
        user_data_dir: Directory path for user-specific configuration files
        job_summary_file: Path to user's job context markdown file
        job_skills_file: Path to user's skills profile file
        job_role_context_file: Path to user's role context file
    """
    
    def __init__(self, user_data_dir: str):
        """Initialize user context manager.
        
        Args:
            user_data_dir: Directory containing user-specific configuration
        """
        self.user_data_dir = user_data_dir
        self.job_summary_file = os.path.join(user_data_dir, 'job_summery.md')
        self.job_skills_file = os.path.join(user_data_dir, 'job_skill_summery.md')
        self.job_role_context_file = os.path.join(user_data_dir, 'job_role_context.md')
        self._username_file = os.path.join(user_data_dir, 'username.txt')
    
    def get_username(self) -> str:
        """Get the user's username from configuration.
        
        Returns:
            str: The user's username/email alias, or 'user' if not configured.
        """
        if os.path.exists(self._username_file):
            with open(self._username_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return "user"
    
    def get_job_context(self) -> str:
        """Get user's job context from markdown file.
        
        Returns:
            str: Job context content or 'Job context unavailable'
        """
        if os.path.exists(self.job_summary_file):
            return self._parse_prompty_file(self.job_summary_file)
        return "Job context unavailable"
    
    def get_job_skills(self) -> str:
        """Get user's skills profile.
        
        Returns:
            str: Skills profile content or 'Job skills unavailable'
        """
        if os.path.exists(self.job_skills_file):
            with open(self.job_skills_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return "Job skills unavailable"
    
    def get_job_role_context(self) -> str:
        """Get user's detailed role context.
        
        Returns:
            str: Role context content or 'Job role context unavailable'
        """
        if os.path.exists(self.job_role_context_file):
            with open(self.job_role_context_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return "Job role context unavailable"
    
    def get_standard_context(self) -> str:
        """Get combined standard context for AI prompts.
        
        Returns:
            str: Formatted context string with job info, skills, and role
        """
        return f"""Job Context: {self.get_job_context()}
Skills Profile: {self.get_job_skills()}
Role Details: {self.get_job_role_context()}"""
    
    def create_email_inputs(self, email_content: dict, context: str) -> dict:
        """Create standardized input dict for email processing prompts.
        
        Args:
            email_content: Dict with email data (subject, sender, body, etc.)
            context: Context string to include
            
        Returns:
            dict: Formatted inputs for prompty execution
        """
        return {
            'context': context,
            'job_role_context': self.get_job_role_context(),
            'username': self.get_username(),
            'subject': email_content.get('subject', ''),
            'sender': email_content.get('sender', ''),
            'date': email_content.get('date', ''),
            'body': email_content.get('body', '')[:8000]
        }
    
    def _parse_prompty_file(self, file_path: str) -> str:
        """Parse a prompty/markdown file, stripping YAML frontmatter if present.
        
        Args:
            file_path: Path to file to parse
            
        Returns:
            str: File content without frontmatter
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                return parts[2].strip()
        return content
