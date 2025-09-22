#!/usr/bin/env python3
"""
Email Service for Email Helper

Handles email processing business logic and coordination between
email-related backend components and the GUI.
"""

from typing import Dict, List, Any, Optional, Callable
import logging
import threading

logger = logging.getLogger(__name__)


class EmailService:
    """Service layer for email processing business logic."""
    
    def __init__(self, outlook_manager=None, ai_processor=None, email_analyzer=None, 
                 summary_generator=None, email_processor=None, task_persistence=None):
        """
        Initialize the email service.
        
        Args:
            outlook_manager: OutlookManager instance
            ai_processor: AIProcessor instance  
            email_analyzer: EmailAnalyzer instance
            summary_generator: SummaryGenerator instance
            email_processor: EmailProcessor instance
            task_persistence: TaskPersistence instance
        """
        self.outlook_manager = outlook_manager
        self.ai_processor = ai_processor
        self.email_analyzer = email_analyzer
        self.summary_generator = summary_generator
        self.email_processor = email_processor
        self.task_persistence = task_persistence
        
        # Processing state
        self.processing_cancelled = False
        self.email_suggestions = []
        self.action_items_data = {}
        self.summary_sections = {}
        
        # Callbacks for UI updates
        self.progress_callback: Optional[Callable[[float, str], None]] = None
        self.completion_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self.error_callback: Optional[Callable[[str, str], None]] = None
        
    def register_progress_callback(self, callback: Callable[[float, str], None]) -> None:
        """Register callback for progress updates."""
        self.progress_callback = callback
        
    def register_completion_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register callback for processing completion."""
        self.completion_callback = callback
        
    def register_error_callback(self, callback: Callable[[str, str], None]) -> None:
        """Register callback for error notifications."""
        self.error_callback = callback
        
    def process_emails_async(self, max_emails: int = 50) -> None:
        """
        Start email processing in background thread.
        
        Args:
            max_emails: Maximum number of emails to process
        """
        if not self._validate_components():
            return
            
        self.processing_cancelled = False
        
        # Reset processing state
        self.email_suggestions = []
        self.action_items_data = {}
        self.summary_sections = {}
        
        # Start background processing
        processing_thread = threading.Thread(
            target=self._process_emails_background,
            args=(max_emails,),
            daemon=True
        )
        processing_thread.start()
        
    def _process_emails_background(self, max_emails: int) -> None:
        """
        Background email processing method.
        
        Args:
            max_emails: Maximum number of emails to process
        """
        try:
            self._update_progress(5, "Retrieving conversations...")
            
            # Get email conversations
            conversation_data = self.outlook_manager.get_emails_with_full_conversations(
                days_back=None, max_emails=max_emails
            )
            
            if self.processing_cancelled:
                return
                
            self._update_progress(15, f"Found {len(conversation_data)} conversations. Starting AI analysis...")
            
            # Process conversations
            total_conversations = len(conversation_data)
            for i, (conversation_id, conv_info) in enumerate(conversation_data, 1):
                if self.processing_cancelled:
                    return
                    
                progress = 25 + (70 * i / total_conversations)
                self._update_progress(progress, f"Processing {i}/{total_conversations}")
                
                self._process_single_conversation(conversation_id, conv_info, i, total_conversations)
                
            # Store results
            self.email_suggestions = self.email_processor.get_email_suggestions()
            
            # Apply holistic analysis
            self._update_progress(95, "Applying holistic intelligence...")
            self.email_suggestions = self._apply_holistic_inbox_analysis(self.email_suggestions)
            
            # Reprocess action items
            self._reprocess_action_items_after_holistic_changes()
            
            self._update_progress(100, "Processing complete")
            
            # Notify completion
            if self.completion_callback:
                result_summary = {
                    'email_count': len(self.email_suggestions),
                    'action_items': len(self.action_items_data),
                    'processed_successfully': True
                }
                self.completion_callback(result_summary)
                
        except Exception as e:
            logger.error(f"Error in email processing: {e}", exc_info=True)
            if self.error_callback:
                self.error_callback("Email Processing Error", str(e))
                
    def _process_single_conversation(self, conversation_id: str, conv_info: Dict[str, Any], 
                                   index: int, total: int) -> None:
        """
        Process a single email conversation.
        
        Args:
            conversation_id: Conversation identifier
            conv_info: Conversation information
            index: Current conversation index
            total: Total conversations to process
        """
        try:
            # Delegate to email processor with existing logic
            if hasattr(self.email_processor, 'process_single_conversation'):
                # Learning data for accuracy tracking
                learning_data = {
                    'session_start': True,
                    'total_emails': total,
                    'current_index': index
                }
                
                # Use existing method if available
                self.email_processor.process_single_conversation(
                    conversation_id, conv_info, index, total, learning_data
                )
            else:
                logger.warning("Email processor doesn't have process_single_conversation method")
                
        except Exception as e:
            logger.error(f"Error processing conversation {conversation_id}: {e}")
            
    def _apply_holistic_inbox_analysis(self, email_suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply holistic analysis to email suggestions.
        
        Args:
            email_suggestions: List of email suggestions
            
        Returns:
            Updated email suggestions
        """
        try:
            if hasattr(self.email_processor, '_apply_holistic_inbox_analysis'):
                return self.email_processor._apply_holistic_inbox_analysis(email_suggestions)
            else:
                logger.warning("Email processor doesn't have holistic analysis method")
                return email_suggestions
        except Exception as e:
            logger.error(f"Error in holistic analysis: {e}")
            return email_suggestions
            
    def _reprocess_action_items_after_holistic_changes(self) -> None:
        """Reprocess action items after holistic modifications."""
        try:
            if hasattr(self.email_processor, '_reprocess_action_items_after_holistic_changes'):
                self.email_processor._reprocess_action_items_after_holistic_changes()
        except Exception as e:
            logger.error(f"Error reprocessing action items: {e}")
            
    def cancel_processing(self) -> None:
        """Cancel ongoing email processing."""
        self.processing_cancelled = True
        logger.info("Email processing cancelled by user")
        
    def get_email_suggestions(self) -> List[Dict[str, Any]]:
        """Get processed email suggestions."""
        return self.email_suggestions
        
    def get_action_items_data(self) -> Dict[str, Any]:
        """Get action items data."""
        return self.action_items_data
        
    def get_summary_sections(self) -> Dict[str, Any]:
        """Get summary sections."""
        return self.summary_sections
        
    def apply_category_change(self, email_index: int, new_category: str, explanation: str = '') -> bool:
        """
        Apply category change to an email.
        
        Args:
            email_index: Index of email to change
            new_category: New category to apply
            explanation: Optional explanation for change
            
        Returns:
            True if change was applied successfully
        """
        try:
            if hasattr(self.email_processor, 'edit_suggestion'):
                self.email_processor.edit_suggestion(email_index, new_category, explanation)
                return True
            else:
                logger.error("Email processor doesn't support category changes")
                return False
        except Exception as e:
            logger.error(f"Error applying category change: {e}")
            return False
            
    def apply_to_outlook(self) -> bool:
        """
        Apply categorization changes to Outlook.
        
        Returns:
            True if changes were applied successfully
        """
        try:
            if hasattr(self.email_processor, 'apply_to_outlook'):
                self.email_processor.apply_to_outlook()
                return True
            else:
                logger.error("Email processor doesn't support Outlook application")
                return False
        except Exception as e:
            logger.error(f"Error applying to Outlook: {e}")
            return False
            
    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate comprehensive email summary.
        
        Returns:
            Summary sections dictionary
        """
        try:
            if self.task_persistence:
                self.summary_sections = self.task_persistence.get_comprehensive_summary(
                    self.action_items_data
                )
                return self.summary_sections
            else:
                logger.error("Task persistence not available for summary generation")
                return {}
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {}
            
    def _update_progress(self, progress: float, message: str) -> None:
        """Update progress via callback."""
        if self.progress_callback:
            self.progress_callback(progress, message)
            
    def _validate_components(self) -> bool:
        """Validate that required components are available."""
        required = [
            ('outlook_manager', self.outlook_manager),
            ('email_processor', self.email_processor)
        ]
        
        for name, component in required:
            if component is None:
                if self.error_callback:
                    self.error_callback("Configuration Error", f"Missing required component: {name}")
                return False
                
        return True