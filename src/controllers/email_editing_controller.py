"""Email Editing Controller - Handles email suggestion editing business logic."""

from typing import Dict, List, Optional


class EmailEditingController:
    """Controller for email editing and reclassification operations."""
    
    def __init__(self, ai_processor, email_processor, task_persistence):
        """Initialize controller with required services.
        
        Args:
            ai_processor: Service for AI processing
            email_processor: Service for email workflow processing  
            task_persistence: Service for task storage
        """
        self.ai_processor = ai_processor
        self.email_processor = email_processor
        self.task_persistence = task_persistence
    
    def edit_suggestion(self, email_suggestions: List[Dict], email_index: int,
                       new_category: str, user_explanation: str) -> bool:
        """Edit an email suggestion's category.
        
        Args:
            email_suggestions: List of all email suggestions
            email_index: Index of the email to edit
            new_category: New category for the email
            user_explanation: User's explanation for the change
            
        Returns:
            True if edit was successful
        """
        if email_index >= len(email_suggestions):
            return False
        
        suggestion_data = email_suggestions[email_index]
        old_category = suggestion_data['ai_suggestion']
        
        # Update the suggestion
        suggestion_data['ai_suggestion'] = new_category
        
        # Update action items data
        self._update_action_items_for_reclassification(
            suggestion_data, old_category, new_category)
        
        # Record the change for accuracy tracking
        email_data = suggestion_data.get('email_data', {})
        email_info = {
            'subject': email_data.get('subject', 'Unknown'),
            'sender': email_data.get('sender_name', 'Unknown'),
            'date': email_data.get('received_time', 'Unknown'),
            'body': email_data.get('body', '')[:500]
        }
        self.ai_processor.record_suggestion_modification(
            email_info, old_category, new_category, user_explanation)
        
        return True
    
    def _update_action_items_for_reclassification(self, suggestion_data: Dict,
                                                  old_category: str, new_category: str):
        """Update email suggestions when an email is reclassified."""
        email_data = suggestion_data.get('email_data', {})
        
        print(f"🔄 Reclassifying email '{email_data.get('subject', 'Unknown')[:50]}' from '{old_category}' to '{new_category}'")
        
        # Update the suggestion data
        for suggestion in self.email_processor.email_suggestions:
            suggestion_email_data = suggestion.get('thread_data', {})
            if (suggestion_email_data.get('topic', '') == email_data.get('subject', '') or
                suggestion.get('email_object', {}) and 
                getattr(suggestion['email_object'], 'Subject', '') == email_data.get('subject', '')):
                
                suggestion['ai_suggestion'] = new_category
                suggestion['explanation'] = f"Manually reclassified as {new_category.replace('_', ' ')} from {old_category.replace('_', ' ')}."
                
                print(f"✅ Updated suggestion data for deferred processing")
                break
        
        # Clear old action items data
        action_items_data = self.email_processor.action_items_data
        if old_category in action_items_data:
            items_to_remove = []
            for i, item in enumerate(action_items_data[old_category]):
                if (item.get('email_subject') == email_data.get('subject') and 
                    item.get('email_sender') == email_data.get('sender_name')):
                    items_to_remove.append(i)
            
            for i in reversed(items_to_remove):
                action_items_data[old_category].pop(i)
    
    def sort_suggestions(self, email_suggestions: List[Dict], column: str,
                        reverse: bool, category_priority: Dict[str, int]) -> List[Dict]:
        """Sort email suggestions by column.
        
        Args:
            email_suggestions: List of email suggestions to sort
            column: Column to sort by ('Subject', 'From', 'Category', 'AI Summary', 'Date')
            reverse: Whether to sort in reverse order
            category_priority: Priority mapping for categories
            
        Returns:
            Sorted list of suggestions
        """
        items_with_sort_keys = []
        
        for i, suggestion in enumerate(email_suggestions):
            email_data = suggestion['email_data']
            
            if column == 'Subject':
                sort_key = email_data.get('subject', '').lower()
            elif column == 'From':
                sort_key = email_data.get('sender_name', email_data.get('sender', '')).lower()
            elif column == 'Category':
                sort_key = category_priority.get(suggestion.get('ai_suggestion', ''), 99)
            elif column == 'AI Summary':
                sort_key = suggestion.get('ai_summary', '').lower()
            elif column == 'Date':
                received_time = email_data.get('received_time')
                sort_key = received_time.timestamp() if hasattr(received_time, 'timestamp') else 0
            else:
                sort_key = ''
            
            items_with_sort_keys.append((i, sort_key))
        
        items_with_sort_keys.sort(key=lambda x: x[1], reverse=reverse)
        
        return [email_suggestions[i] for i, _ in items_with_sort_keys]
