#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Email Helper Application - Main orchestrator following MVC architecture.

This module provides the main application class that wires together:
- Controllers (business logic)
- ViewModels (data transformation)
- Views (UI components)

NO BUSINESS LOGIC should exist in this file - only wiring and coordination.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import List, Dict, Any, Optional
import logging

# Controllers
from controllers import (
    EmailProcessingController,
    EmailEditingController,
    SummaryController,
    AccuracyController
)

# ViewModels
from viewmodels import EmailSuggestionViewModel, EmailDetailViewModel

# Views
from gui.tabs import ProcessingTab, EditingTab, SummaryTab, AccuracyTab

# Service Factory
from core.service_factory import ServiceFactory

logger = logging.getLogger(__name__)


class EmailHelperApp:
    """Main application orchestrator following MVC architecture.
    
    This class wires controllers to views and handles coordination between components.
    All business logic is delegated to controller classes.
    """
    
    # Category mapping for display (actual category IDs)
    CATEGORY_MAPPING = {
        'required_personal_action': 'Required Personal Action',
        'team_action': 'Team Action',
        'optional_action': 'Optional Action',
        'job_listing': 'Job Listing',
        'optional_event': 'Optional Event',
        'work_relevant': 'Work Relevant',
        'fyi': 'FYI',
        'newsletter': 'Newsletter',
        'spam_to_delete': 'Spam To Delete'
    }
    
    # Category priority for sorting
    CATEGORY_PRIORITY = {
        'required_personal_action': 1,
        'team_action': 2,
        'optional_action': 3,
        'job_listing': 4,
        'optional_event': 5,
        'work_relevant': 6,
        'fyi': 7,
        'newsletter': 8,
        'spam_to_delete': 9
    }
    
    def __init__(self, root):
        """Initialize the application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Email Helper - AI-Powered Email Management")
        self.root.geometry("1400x900")
        
        # State
        self.email_suggestions: List[Dict[str, Any]] = []
        self.processing_cancelled = False
        
        # Initialize service factory
        self.service_factory = ServiceFactory()
        
        # Initialize controllers
        self._init_controllers()
        
        # Create UI
        self._create_ui()
        
        logger.info("Email Helper Application initialized")
    
    def _init_controllers(self):
        """Initialize all controllers."""
        # Get services from factory
        outlook_manager = self.service_factory.get_outlook_manager()
        ai_processor = self.service_factory.get_ai_processor()
        email_analyzer = self.service_factory.get_email_analyzer()
        email_processor = self.service_factory.get_email_processor()
        task_persistence = self.service_factory.get_task_persistence()
        summary_generator = self.service_factory.get_summary_generator()
        accuracy_tracker = self.service_factory.get_accuracy_tracker()
        db_migrations = self.service_factory.get_database_migrations()
        
        # Apply database migrations
        db_migrations.apply_migrations()
        
        # Create controllers with dependencies
        self.processing_controller = EmailProcessingController(
            outlook_manager,
            ai_processor,
            email_analyzer,
            email_processor,
            task_persistence
        )
        self.editing_controller = EmailEditingController(
            ai_processor,
            email_processor,
            task_persistence
        )
        self.summary_controller = SummaryController(
            summary_generator,
            task_persistence,
            email_processor
        )
        self.accuracy_controller = AccuracyController(
            accuracy_tracker,
            task_persistence,
            db_migrations
        )
    
    def _create_ui(self):
        """Create the main UI structure."""
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tab containers
        self.processing_frame = ttk.Frame(self.notebook)
        self.editing_frame = ttk.Frame(self.notebook)
        self.summary_frame = ttk.Frame(self.notebook)
        self.accuracy_frame = ttk.Frame(self.notebook)
        
        # Add tabs to notebook
        self.notebook.add(self.processing_frame, text="1. Processing")
        self.notebook.add(self.editing_frame, text="2. Review & Edit")
        self.notebook.add(self.summary_frame, text="3. Summary")
        self.notebook.add(self.accuracy_frame, text="4. Accuracy Dashboard")
        
        # Create tab views with callbacks
        self.processing_tab = ProcessingTab(
            self.processing_frame,
            on_start_callback=self.on_start_processing,
            on_cancel_callback=self.on_cancel_processing,
            on_dashboard_callback=self.show_accuracy_dashboard
        )
        
        self.editing_tab = EditingTab(
            self.editing_frame,
            category_mapping=list(self.CATEGORY_MAPPING.keys()),
            on_email_select_callback=self.on_email_select,
            on_category_change_callback=self.on_category_change,
            on_apply_category_callback=self.on_apply_category,
            on_apply_to_outlook_callback=self.on_apply_to_outlook,
            on_generate_summary_callback=self.on_generate_summary,
            on_sort_callback=self.on_sort_column
        )
        
        self.summary_tab = SummaryTab(
            self.summary_frame,
            on_generate_summary_callback=self.on_generate_summary,
            on_mark_task_complete_callback=self.on_mark_tasks_complete,
            on_load_outstanding_tasks_callback=self.on_load_outstanding_tasks,
            on_clear_fyi_callback=self.on_clear_fyi
        )
        
        self.accuracy_tab = AccuracyTab(
            self.accuracy_frame,
            on_refresh_callback=self.on_refresh_accuracy
        )
        
        # Apply theme
        self._apply_theme()
    
    def _apply_theme(self):
        """Apply visual theme to the application."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Define accent button style
        style.configure(
            'Accent.TButton',
            background='#0078D4',
            foreground='white',
            borderwidth=0,
            focuscolor='none',
            padding=(10, 5)
        )
        style.map(
            'Accent.TButton',
            background=[('active', '#005A9E')]
        )
    
    # Processing callbacks
    
    def on_start_processing(self, max_emails: int):
        """Start email processing workflow.
        
        Args:
            max_emails: Maximum number of emails to process
        """
        logger.info(f"Starting email processing for {max_emails} emails")
        
        # Update UI
        self.processing_tab.set_buttons_state(start_enabled=False, cancel_enabled=True)
        self.processing_tab.clear_progress()
        self.processing_tab.add_log_message(f"🚀 Starting to process {max_emails} emails...\n")
        
        # Reset state
        self.processing_cancelled = False
        self.email_suggestions.clear()
        
        # Start processing in background thread
        thread = threading.Thread(
            target=self._process_emails_thread,
            args=(max_emails,),
            daemon=True
        )
        thread.start()
    
    def _process_emails_thread(self, max_emails: int):
        """Background thread for email processing.
        
        Args:
            max_emails: Maximum number of emails to process
        """
        try:
            # Progress callback
            def on_progress(percent: float, message: str):
                self.root.after(0, self.processing_tab.update_progress, percent, message)
                return not self.processing_cancelled
            
            # Log callback
            def on_log(message: str):
                self.root.after(0, self.processing_tab.add_log_message, message)
            
            # Delegate to controller - this starts a background thread and returns it
            processing_thread = self.processing_controller.start_email_processing(
                max_emails=max_emails,
                progress_callback=on_progress,
                log_callback=on_log
            )
            
            # Wait for the thread to complete
            processing_thread.join()
            
            # Get the results from the controller
            self.email_suggestions = self.processing_controller.get_email_suggestions()
            
            # Create results dict for UI update
            results = {
                'suggestions': self.email_suggestions,
                'action_items': self.processing_controller.get_action_items_data()
            }
            
            # Update UI on main thread
            self.root.after(0, self._on_processing_complete, results)
            
        except Exception as e:
            logger.error(f"Error in processing thread: {e}", exc_info=True)
            self.root.after(0, self._on_processing_error, str(e))
    
    def _on_processing_complete(self, results: Dict[str, Any]):
        """Handle processing completion.
        
        Args:
            results: Processing results from controller
        """
        # Update UI
        self.processing_tab.set_buttons_state(start_enabled=True, cancel_enabled=False)
        self.processing_tab.add_log_message(f"\n✅ Processing complete! Analyzed {len(self.email_suggestions)} emails.")
        self.processing_tab.add_log_message("📝 Switch to the 'Review & Edit' tab to review and categorize emails.")
        
        # Load emails into editing tab
        self._load_emails_into_editing_tab()
        
        # Switch to editing tab
        self.notebook.select(self.editing_frame)
        
        messagebox.showinfo(
            "Processing Complete",
            f"Successfully processed {len(self.email_suggestions)} emails!\n\n"
            "Review the suggestions in the 'Review & Edit' tab."
        )
    
    def _on_processing_error(self, error_message: str):
        """Handle processing error.
        
        Args:
            error_message: Error message
        """
        self.processing_tab.set_buttons_state(start_enabled=True, cancel_enabled=False)
        self.processing_tab.add_log_message(f"\n❌ Error: {error_message}")
        
        messagebox.showerror("Processing Error", f"An error occurred during processing:\n\n{error_message}")
    
    def on_cancel_processing(self):
        """Cancel email processing."""
        self.processing_cancelled = True
        self.processing_tab.add_log_message("\n⚠️ Cancelling processing...")
        self.processing_tab.set_buttons_state(start_enabled=True, cancel_enabled=False)
    
    # Editing callbacks
    
    def _load_emails_into_editing_tab(self):
        """Load processed emails into editing tab."""
        # Transform to view models
        viewmodels = [
            EmailSuggestionViewModel(suggestion, self.CATEGORY_PRIORITY)
            for suggestion in self.email_suggestions
        ]
        
        # Load into view
        self.editing_tab.load_emails(viewmodels)
    
    def on_email_select(self):
        """Handle email selection in editing tab."""
        index = self.editing_tab.get_selected_email_index()
        if index is None or index >= len(self.email_suggestions):
            self.editing_tab.clear_details()
            return
        
        # Get email data
        suggestion = self.email_suggestions[index]
        
        # Transform to detail view model
        detail_vm = EmailDetailViewModel(suggestion)
        
        # Check if modified
        is_modified = suggestion.get('user_modified', False)
        
        # Display in view
        self.editing_tab.show_email_details(detail_vm, is_modified)
    
    def on_category_change(self):
        """Handle category dropdown change."""
        # Mark apply button as enabled (auto-save on change)
        self.editing_tab.set_apply_button_state(True)
        
        # Auto-apply the change
        self.on_apply_category("")
    
    def on_apply_category(self, explanation: str):
        """Apply category change to selected email.
        
        Args:
            explanation: Optional explanation for the change
        """
        index = self.editing_tab.get_selected_email_index()
        if index is None or index >= len(self.email_suggestions):
            return
        
        # Get new category
        new_category = self.editing_tab.get_category()
        if not new_category:
            return
        
        # Get current suggestion
        suggestion = self.email_suggestions[index]
        old_category = suggestion.get('ai_suggestion', '')
        
        if new_category == old_category:
            return
        
        # Delegate to controller
        success = self.editing_controller.edit_suggestion(
            email_suggestions=self.email_suggestions,
            email_index=index,
            new_category=new_category,
            user_explanation=explanation
        )
        
        if not success:
            logger.error(f"Failed to edit suggestion at index {index}")
            return
        
        # Get the updated suggestion
        updated_suggestion = self.email_suggestions[index]
        
        # Update in list
        self.email_suggestions[index] = updated_suggestion
        
        # Update view
        vm = EmailSuggestionViewModel(updated_suggestion, self.CATEGORY_PRIORITY)
        self.editing_tab.update_email_in_tree(index, vm)
        
        # Refresh details
        self.on_email_select()
        
        logger.info(f"Category changed from '{old_category}' to '{new_category}' for email at index {index}")
    
    def on_sort_column(self, column: str):
        """Sort emails by column.
        
        Args:
            column: Column name to sort by
        """
        # Delegate to controller
        self.email_suggestions = self.editing_controller.sort_suggestions(
            self.email_suggestions,
            column,
            self.editing_tab.sort_reverse,
            self.CATEGORY_PRIORITY
        )
        
        # Toggle sort direction
        self.editing_tab.sort_reverse = not self.editing_tab.sort_reverse
        
        # Reload view
        self._load_emails_into_editing_tab()
    
    def on_apply_to_outlook(self):
        """Apply categorization to Outlook."""
        if not self.email_suggestions:
            messagebox.showwarning("No Emails", "No emails to apply to Outlook.")
            return
        
        # Apply categorizations using the email processor
        try:
            # Get the email processor from service factory
            email_processor = self.service_factory.get_email_processor()
            outlook_manager = self.service_factory.get_outlook_manager()
            
            # Ensure Outlook is connected
            if not hasattr(outlook_manager, 'outlook') or outlook_manager.outlook is None:
                outlook_manager.connect_to_outlook()
            
            # Apply categorizations
            count = 0
            for suggestion in self.email_suggestions:
                try:
                    email_obj = suggestion.get('email_object')
                    category = suggestion.get('ai_suggestion', '')
                    
                    if email_obj and category:
                        outlook_manager.categorize_email(email_obj, category)
                        count += 1
                except Exception as e:
                    logger.warning(f"Failed to categorize email: {e}")
                    continue
            
            messagebox.showinfo(
                "Success",
                f"Successfully applied {count} categorizations to Outlook!"
            )
            
        except Exception as e:
            logger.error(f"Error applying to Outlook: {e}", exc_info=True)
            messagebox.showerror("Error", f"Error applying to Outlook:\n\n{str(e)}")
    
    # Summary callbacks
    
    def on_generate_summary(self):
        """Generate email summary."""
        if not self.email_suggestions:
            messagebox.showwarning("No Emails", "Process emails first before generating a summary.")
            return
        
        logger.info("Generating email summary")
        
        try:
            # Get action items data from email processor
            action_items_data = self.processing_controller.get_action_items_data()
            
            # Delegate to controller
            summary_sections, saved_path = self.summary_controller.generate_summary(
                action_items_data,
                self.email_suggestions
            )
            
            # Display in view
            self.summary_tab.display_summary(summary_sections)
            
            # Switch to summary tab
            self.notebook.select(self.summary_frame)
            
            messagebox.showinfo("Summary Generated", "Email summary has been generated successfully!")
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}", exc_info=True)
            self.summary_tab.show_error(str(e))
            messagebox.showerror("Error", f"Error generating summary:\n\n{str(e)}")
    
    def on_mark_tasks_complete(self, task_ids: List[str]):
        """Mark tasks as complete.
        
        Args:
            task_ids: List of task identifiers to mark complete
        """
        try:
            # Delegate to controller
            result = self.summary_controller.mark_tasks_completed(task_ids)
            
            if result.get('success'):
                messagebox.showinfo(
                    "Tasks Completed",
                    f"Marked {result.get('count', 0)} task(s) as complete!"
                )
                # Refresh summary
                self.on_generate_summary()
            else:
                messagebox.showerror("Error", "Failed to mark tasks as complete.")
                
        except Exception as e:
            logger.error(f"Error marking tasks complete: {e}", exc_info=True)
            messagebox.showerror("Error", f"Error marking tasks complete:\n\n{str(e)}")
    
    def on_load_outstanding_tasks(self):
        """Load outstanding tasks from previous runs."""
        try:
            # Delegate to controller
            tasks = self.summary_controller.load_outstanding_tasks()
            
            if tasks:
                messagebox.showinfo(
                    "Outstanding Tasks",
                    f"Loaded {len(tasks)} outstanding task(s) from previous runs."
                )
                # Display would be handled by re-generating summary with outstanding tasks
            else:
                messagebox.showinfo("No Outstanding Tasks", "No outstanding tasks found.")
                
        except Exception as e:
            logger.error(f"Error loading outstanding tasks: {e}", exc_info=True)
            messagebox.showerror("Error", f"Error loading outstanding tasks:\n\n{str(e)}")
    
    def on_clear_fyi(self):
        """Clear FYI items from summary."""
        response = messagebox.askyesno(
            "Clear FYI Items",
            "Are you sure you want to clear all FYI items from the summary?"
        )
        
        if response:
            try:
                # Delegate to controller
                self.summary_controller.clear_fyi_items()
                
                # Refresh summary
                self.on_generate_summary()
                
                messagebox.showinfo("FYI Cleared", "FYI items have been cleared.")
                
            except Exception as e:
                logger.error(f"Error clearing FYI: {e}", exc_info=True)
                messagebox.showerror("Error", f"Error clearing FYI items:\n\n{str(e)}")
    
    # Accuracy callbacks
    
    def on_refresh_accuracy(self):
        """Refresh accuracy metrics."""
        logger.info("Refreshing accuracy metrics")
        
        try:
            # Delegate to controller
            metrics_data = self.accuracy_controller.get_dashboard_metrics()
            
            # Display in view
            self.accuracy_tab.display_metrics(metrics_data)
            
        except Exception as e:
            logger.error(f"Error refreshing accuracy metrics: {e}", exc_info=True)
            self.accuracy_tab.show_error(str(e))
            messagebox.showerror("Error", f"Error loading accuracy metrics:\n\n{str(e)}")
    
    def show_accuracy_dashboard(self):
        """Show accuracy dashboard tab."""
        self.notebook.select(self.accuracy_frame)
        self.on_refresh_accuracy()
    
    def run(self):
        """Start the application main loop."""
        logger.info("Starting Email Helper application")
        self.root.mainloop()


def main():
    """Main entry point for the application."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run application
    root = tk.Tk()
    app = EmailHelperApp(root)
    app.run()


if __name__ == '__main__':
    main()
