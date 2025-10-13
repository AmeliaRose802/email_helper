"""Email Suggestion ViewModel - Transforms email data for UI display."""

from typing import Dict, List, Optional
from datetime import datetime


class EmailSuggestionViewModel:
    """ViewModel for email suggestions display."""
    
    def __init__(self, suggestion_data: Dict, category_priority: Dict[str, int]):
        """Initialize ViewModel with suggestion data.
        
        Args:
            suggestion_data: Raw suggestion data from controller
            category_priority: Priority mapping for categories
        """
        self.suggestion_data = suggestion_data
        self.category_priority = category_priority
    
    @property
    def subject(self) -> str:
        """Get formatted subject for display."""
        email_data = self.suggestion_data.get('email_data', {})
        thread_data = self.suggestion_data.get('thread_data', {})
        thread_count = thread_data.get('thread_count', 1)
        
        if thread_count > 1:
            subject = f"🧵 {thread_data.get('topic', email_data.get('subject', 'Unknown'))} ({thread_count} emails)"
        else:
            subject = email_data.get('subject', 'Unknown Subject')
        
        # Add priority indicator
        holistic_priority = self.suggestion_data.get('holistic_priority')
        if holistic_priority == 'high':
            subject = f"🔴 {subject}"
        elif holistic_priority == 'medium':
            subject = f"🟡 {subject}"
        
        # Truncate long text
        if not subject.startswith('🧵'):
            subject = subject[:47] + "..." if len(subject) > 50 else subject
        
        return subject
    
    @property
    def sender(self) -> str:
        """Get formatted sender for display."""
        email_data = self.suggestion_data.get('email_data', {})
        thread_data = self.suggestion_data.get('thread_data', {})
        thread_count = thread_data.get('thread_count', 1)
        
        if thread_count > 1:
            participants = thread_data.get('participants', [email_data.get('sender_name', 'Unknown')])
            sender = f"{len(participants)} participants"
        else:
            sender = email_data.get('sender_name', email_data.get('sender', 'Unknown Sender'))
        
        # Truncate
        if not sender.endswith('participants'):
            sender = sender[:22] + "..." if len(sender) > 25 else sender
        
        return sender
    
    @property
    def category(self) -> str:
        """Get formatted category for display."""
        suggestion = self.suggestion_data['ai_suggestion']
        initial_classification = self.suggestion_data.get('initial_classification', suggestion)
        
        category = suggestion.replace('_', ' ').title()
        if initial_classification != suggestion:
            category = f"{category} (was {initial_classification.replace('_', ' ').title()})"
        
        return category
    
    @property
    def ai_summary(self) -> str:
        """Get formatted AI summary for display."""
        ai_summary = self.suggestion_data.get('ai_summary', 'No summary')
        processing_notes = self.suggestion_data.get('processing_notes', [])
        
        if processing_notes:
            ai_summary = f"🔄 {ai_summary} | {'; '.join(processing_notes[:1])}"
        
        # Truncate
        ai_summary = ai_summary[:47] + "..." if len(ai_summary) > 50 else ai_summary
        
        return ai_summary
    
    @property
    def date(self) -> str:
        """Get formatted date for display."""
        email_data = self.suggestion_data.get('email_data', {})
        received_time = email_data.get('received_time', 'Unknown Date')
        
        if hasattr(received_time, 'strftime'):
            return received_time.strftime('%m-%d %H:%M')
        else:
            return str(received_time)[:10] if received_time != 'Unknown Date' else 'Unknown'
    
    @property
    def sort_key(self) -> any:
        """Get sort key for this suggestion."""
        return self.category_priority.get(self.suggestion_data.get('ai_suggestion', ''), 99)
    
    def to_tree_values(self) -> tuple:
        """Convert to treeview row values.
        
        Returns:
            Tuple of (subject, sender, category, ai_summary, date)
        """
        return (self.subject, self.sender, self.category, self.ai_summary, self.date)


class EmailDetailViewModel:
    """ViewModel for detailed email view."""
    
    def __init__(self, suggestion_data: Dict):
        """Initialize ViewModel with suggestion data.
        
        Args:
            suggestion_data: Raw suggestion data from controller
        """
        self.suggestion_data = suggestion_data
    
    @property
    def ai_summary(self) -> str:
        """Get AI summary."""
        return self.suggestion_data.get('ai_summary', 'No summary available')
    
    @property
    def processing_notes(self) -> List[str]:
        """Get processing notes."""
        return self.suggestion_data.get('processing_notes', [])
    
    @property
    def initial_classification(self) -> str:
        """Get initial classification."""
        return self.suggestion_data.get('initial_classification', 
                                       self.suggestion_data['ai_suggestion'])
    
    @property
    def current_classification(self) -> str:
        """Get current classification."""
        return self.suggestion_data['ai_suggestion']
    
    @property
    def holistic_notes(self) -> List[str]:
        """Get holistic notes."""
        return self.suggestion_data.get('holistic_notes', [])
    
    @property
    def holistic_priority(self) -> Optional[str]:
        """Get holistic priority."""
        return self.suggestion_data.get('holistic_priority')
    
    @property
    def email_body(self) -> str:
        """Get email body."""
        email_data = self.suggestion_data.get('email_data', {})
        return email_data.get('body', 'No content available')
    
    @property
    def was_reclassified(self) -> bool:
        """Check if email was reclassified."""
        return self.initial_classification != self.current_classification
