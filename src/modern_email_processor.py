"""Modernized EmailProcessor with dependency injection and consolidated logic.

This updated version of EmailProcessor uses the service factory pattern,
consolidates common processing logic, and eliminates code duplication
while maintaining all existing functionality.
"""

from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional
import logging

from core.base_processor import BaseProcessor
from core.business_logic import EmailWorkflow, UIStateManager
from utils import *


class ModernEmailProcessor(BaseProcessor):
    """Modernized email processor with dependency injection and clean architecture."""
    
    def __init__(self, service_factory):
        super().__init__("ModernEmailProcessor")
        self.factory = service_factory
        
        # Get services from factory
        self.outlook_manager = service_factory.get_outlook_manager()
        self.ai_processor = service_factory.get_ai_processor()
        self.email_analyzer = service_factory.get_email_analyzer()
        self.summary_generator = service_factory.get_summary_generator()
        self.task_persistence = service_factory.get_task_persistence()
        
        # Create workflow orchestrator
        self.workflow = EmailWorkflow(
            self.outlook_manager,
            self.ai_processor,
            self.task_persistence
        )
        
        # Data storage with cleaner structure
        self.processing_data = {
            'action_items': defaultdict(list),
            'email_suggestions': [],
            'summary_sections': {},
            'processing_stats': {}
        }
    
    def process_emails(self, max_emails: int = 50, folder: str = "Inbox") -> Dict[str, Any]:
        """Process emails using the modern workflow."""
        try:
            self.logger.info(f"Starting email processing: {max_emails} emails from {folder}")
            self.reset_cancellation()
            
            # Set up progress tracking
            def progress_handler(progress: int):
                self.update_progress(progress)
                self.logger.debug(f"Processing progress: {progress}%")
            
            self.workflow.set_progress_callback(progress_handler)
            
            # Execute the workflow
            future = self.workflow.process_batch(folder, max_emails)
            result = future.result()  # Block until completion
            
            if result['success']:
                # Organize results for UI consumption
                self._organize_processing_results(result['data'])
                
                self.logger.info(f"Email processing completed successfully: {result['data']['total_count']} emails")
                return self.create_result(True, self.processing_data, "Processing completed successfully")
            else:
                self.logger.error(f"Email processing failed: {result['message']}")
                return result
                
        except Exception as e:
            self.logger.error(f"Error in process_emails: {e}")
            return self.create_result(False, message=f"Processing failed: {e}")
    
    def _organize_processing_results(self, workflow_data: Dict[str, Any]):
        """Organize workflow results for UI consumption."""
        emails = workflow_data.get('emails', [])
        tasks = workflow_data.get('tasks', [])
        batch_analysis = workflow_data.get('batch_analysis', {})
        
        # Reset data storage
        self.processing_data = {
            'action_items': defaultdict(list),
            'email_suggestions': [],
            'summary_sections': {},
            'processing_stats': {}
        }
        
        # Organize emails by category
        for email in emails:
            classification = email.get('classification', {})
            category = classification.get('action_type', 'fyi')
            
            # Create suggestion format for UI compatibility
            suggestion = {
                'email_data': email,
                'suggestion': category,
                'priority': classification.get('priority', 'medium'),
                'reasoning': classification.get('reasoning', ''),
                'action_required': classification.get('action_required', ''),
                'due_date': classification.get('due_date'),
                'confidence_score': classification.get('confidence_score', 0.0)
            }
            
            self.processing_data['email_suggestions'].append(suggestion)
            self.processing_data['action_items'][category].append(suggestion)
        
        # Generate summary sections
        self.processing_data['summary_sections'] = self.summary_generator.organize_summary_sections(
            dict(self.processing_data['action_items'])
        )
        
        # Calculate processing stats
        self.processing_data['processing_stats'] = {
            'total_emails': len(emails),
            'total_tasks': len(tasks),
            'categories': {cat: len(items) for cat, items in self.processing_data['action_items'].items()},
            'processed_at': workflow_data.get('processed_at'),
            'batch_analysis': batch_analysis
        }
    
    def get_action_items_data(self) -> Dict[str, List]:
        """Get organized action items data."""
        return dict(self.processing_data['action_items'])
    
    def get_email_suggestions(self) -> List[Dict]:
        """Get email suggestions for UI display."""
        return self.processing_data['email_suggestions']
    
    def get_summary_sections(self) -> Dict[str, Any]:
        """Get organized summary sections."""
        return self.processing_data['summary_sections']
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.processing_data['processing_stats']
    
    def update_suggestion(self, suggestion_index: int, new_category: str, 
                         user_feedback: Optional[str] = None) -> bool:
        """Update a suggestion with user feedback."""
        try:
            if suggestion_index < 0 or suggestion_index >= len(self.processing_data['email_suggestions']):
                return False
            
            suggestion = self.processing_data['email_suggestions'][suggestion_index]
            old_category = suggestion['suggestion']
            
            # Update the suggestion
            suggestion['suggestion'] = new_category
            suggestion['user_modified'] = True
            suggestion['user_feedback'] = user_feedback
            suggestion['modified_at'] = datetime.now().isoformat()
            
            # Move between action item categories
            self.processing_data['action_items'][old_category].remove(suggestion)
            self.processing_data['action_items'][new_category].append(suggestion)
            
            # Record feedback for AI improvement
            if user_feedback:
                self.ai_processor.record_user_feedback(
                    suggestion['email_data'],
                    old_category,
                    new_category,
                    user_feedback
                )
            
            self.logger.info(f"Updated suggestion {suggestion_index}: {old_category} -> {new_category}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating suggestion: {e}")
            return False
    
    def save_results(self) -> bool:
        """Save processing results to persistent storage."""
        try:
            # Extract tasks from action items
            tasks = []
            for category, items in self.processing_data['action_items'].items():
                if category in ['required_personal_action', 'team_action', 'optional_action']:
                    for item in items:
                        email_data = item['email_data']
                        task = {
                            'email_id': email_data.get('entry_id'),
                            'subject': email_data.get('subject'),
                            'sender': email_data.get('sender'),
                            'due_date': item.get('due_date'),
                            'priority': item.get('priority', 'medium'),
                            'action_required': item.get('action_required'),
                            'category': category,
                            'status': 'outstanding',
                            'created_at': datetime.now().isoformat()
                        }
                        tasks.append(task)
            
            # Save to task persistence
            success = self.task_persistence.save_outstanding_tasks(tasks)
            
            if success:
                self.logger.info(f"Saved {len(tasks)} tasks to persistent storage")
            else:
                self.logger.error("Failed to save tasks to persistent storage")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
            return False
    
    def clear_processing_data(self):
        """Clear all processing data."""
        self.processing_data = {
            'action_items': defaultdict(list),
            'email_suggestions': [],
            'summary_sections': {},
            'processing_stats': {}
        }
        self.logger.info("Processing data cleared")


# Backward compatibility wrapper
class EmailProcessor(ModernEmailProcessor):
    """Backward compatibility wrapper for existing code."""
    
    def __init__(self, outlook_manager, ai_processor, email_analyzer, summary_generator):
        # Create a service factory for compatibility
        from core.service_factory import ServiceFactory
        
        factory = ServiceFactory()
        factory.override_service('outlook_manager', outlook_manager)
        factory.override_service('ai_processor', ai_processor)
        factory.override_service('email_analyzer', email_analyzer) 
        factory.override_service('summary_generator', summary_generator)
        
        super().__init__(factory)
        
        # For backward compatibility, expose the old interface
        self.action_items_data = self.processing_data['action_items']
        self.email_suggestions = self.processing_data['email_suggestions']