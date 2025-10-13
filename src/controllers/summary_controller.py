"""Summary Controller - Handles summary generation and task management logic."""

from typing import Dict, List, Optional, Tuple
from datetime import datetime


class SummaryController:
    """Controller for summary generation and task management operations."""
    
    def __init__(self, summary_generator, task_persistence, email_processor):
        """Initialize controller with required services.
        
        Args:
            summary_generator: Service for summary generation
            task_persistence: Service for task storage
            email_processor: Service for email workflow processing
        """
        self.summary_generator = summary_generator
        self.task_persistence = task_persistence
        self.email_processor = email_processor
    
    def generate_summary(self, action_items_data: Dict, email_suggestions: List[Dict]) -> Tuple[Dict, str]:
        """Generate comprehensive summary including persistent tasks.
        
        Args:
            action_items_data: Current batch action items
            email_suggestions: List of email suggestions
            
        Returns:
            Tuple of (summary_sections dict, saved_summary_path str)
        """
        # Perform detailed processing if needed
        if email_suggestions:
            print("\n🔍 Performing detailed AI processing for comprehensive summaries...")
            try:
                action_items_data = self.email_processor.process_detailed_analysis(email_suggestions)
                print("✅ Detailed processing completed for summary")
            except Exception as e:
                print(f"❌ Error during detailed processing: {e}")
                raise
        
        # Generate summary sections from current batch
        current_batch_sections = self.summary_generator.build_summary_sections(action_items_data)
        
        # Get comprehensive summary with previous outstanding tasks
        summary_sections = self.task_persistence.get_comprehensive_summary(current_batch_sections)
        
        # Save current batch tasks to persistent storage
        batch_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.task_persistence.save_outstanding_tasks(current_batch_sections, batch_timestamp)
        
        # Save HTML summary for browser viewing
        saved_summary_path = self.summary_generator.save_focused_summary(summary_sections, batch_timestamp)
        
        return summary_sections, saved_summary_path
    
    def get_task_statistics(self) -> Dict:
        """Get task statistics.
        
        Returns:
            Dictionary containing task statistics
        """
        return self.task_persistence.get_task_statistics()
    
    def mark_tasks_completed(self, task_ids: List[str]) -> int:
        """Mark tasks as completed.
        
        Args:
            task_ids: List of task IDs to mark as complete
            
        Returns:
            Number of tasks marked complete
        """
        self.task_persistence.mark_tasks_completed(task_ids)
        return len(task_ids)
    
    def load_outstanding_tasks(self) -> Dict:
        """Load outstanding tasks from persistence.
        
        Returns:
            Dictionary of outstanding tasks by section
        """
        return self.task_persistence.load_outstanding_tasks()
    
    def clear_fyi_items(self) -> int:
        """Clear all FYI items.
        
        Returns:
            Number of items cleared
        """
        return self.task_persistence.clear_fyi_items()
    
    def clear_newsletter_items(self) -> int:
        """Clear all newsletter items.
        
        Returns:
            Number of items cleared
        """
        return self.task_persistence.clear_newsletter_items()
    
    def dismiss_event(self, task_id: str) -> bool:
        """Dismiss a single optional event.
        
        Args:
            task_id: ID of the event to dismiss
            
        Returns:
            True if event was dismissed
        """
        outstanding_tasks = self.task_persistence.load_outstanding_tasks()
        
        if 'optional_events' in outstanding_tasks:
            original_count = len(outstanding_tasks['optional_events'])
            outstanding_tasks['optional_events'] = [
                event for event in outstanding_tasks['optional_events']
                if event.get('task_id') != task_id
            ]
            new_count = len(outstanding_tasks['optional_events'])
            
            if original_count > new_count:
                self.task_persistence._save_tasks_to_file(
                    self.task_persistence.tasks_file,
                    {
                        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'tasks': outstanding_tasks
                    }
                )
                print(f"🗑️ Dismissed optional event: {task_id}")
                return True
        
        return False
