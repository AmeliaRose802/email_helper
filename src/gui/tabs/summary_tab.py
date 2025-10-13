#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summary Tab - Email summary and task management interface (VIEW ONLY - NO BUSINESS LOGIC)."""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import List, Dict, Any, Callable, Optional
from gui.helpers import open_url


class SummaryTab:
    """Summary and task management tab - pure view component.
    
    This view delegates all business logic to the SummaryController.
    """
    
    def __init__(
        self,
        parent,
        on_generate_summary_callback: Callable,
        on_mark_task_complete_callback: Callable,
        on_load_outstanding_tasks_callback: Callable,
        on_clear_fyi_callback: Callable,
        on_export_summary_callback: Optional[Callable] = None
    ):
        """Initialize summary tab view.
        
        Args:
            parent: Parent widget
            on_generate_summary_callback: Callback for generate summary button
            on_mark_task_complete_callback: Callback for marking tasks complete
            on_load_outstanding_tasks_callback: Callback for loading outstanding tasks
            on_clear_fyi_callback: Callback for clearing FYI items
            on_export_summary_callback: Optional callback for exporting summary
        """
        self.parent = parent
        self.on_generate_summary_callback = on_generate_summary_callback
        self.on_mark_task_complete_callback = on_mark_task_complete_callback
        self.on_load_outstanding_tasks_callback = on_load_outstanding_tasks_callback
        self.on_clear_fyi_callback = on_clear_fyi_callback
        self.on_export_summary_callback = on_export_summary_callback
        
        self.task_checkboxes: List[tk.Checkbutton] = []
        self.task_vars: List[tk.BooleanVar] = []
        self.task_labels: List[str] = []
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create all UI widgets."""
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Header with controls
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(
            header_frame,
            text="📋 Email Summary & Action Items",
            font=('Segoe UI', 14, 'bold')
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        button_frame = ttk.Frame(header_frame)
        button_frame.pack(side=tk.RIGHT)
        
        self.generate_btn = ttk.Button(
            button_frame,
            text="🔄 Generate Summary",
            command=self.on_generate_summary_callback,
            style="Accent.TButton"
        )
        self.generate_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="📥 Load Outstanding Tasks",
            command=self.on_load_outstanding_tasks_callback
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="✓ Mark Selected Complete",
            command=self._on_mark_complete_click
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="🗑️ Clear FYI",
            command=self.on_clear_fyi_callback
        ).pack(side=tk.LEFT, padx=5)
        
        if self.on_export_summary_callback:
            ttk.Button(
                button_frame,
                text="💾 Export",
                command=self.on_export_summary_callback
            ).pack(side=tk.LEFT, padx=5)
        
        # Summary text area
        self.summary_text = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=('Segoe UI', 10),
            padx=10,
            pady=10
        )
        self.summary_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Tag configuration for different sections
        self.summary_text.tag_config("heading", font=('Segoe UI', 12, 'bold'), spacing1=10, spacing3=5)
        self.summary_text.tag_config("subheading", font=('Segoe UI', 11, 'bold'), spacing1=8, spacing3=3)
        self.summary_text.tag_config("action_item", font=('Segoe UI', 10), lmargin1=20, lmargin2=20)
        self.summary_text.tag_config("fyi_item", font=('Segoe UI', 10), lmargin1=20, lmargin2=20, foreground="#666666")
        self.summary_text.tag_config("hyperlink", foreground="blue", underline=True)
        self.summary_text.tag_config("completed", font=('Segoe UI', 10), overstrike=True, foreground="#999999")
        
        # Bind link clicks
        self.summary_text.tag_bind("hyperlink", "<Button-1>", self._on_link_click)
        self.summary_text.tag_bind("hyperlink", "<Enter>", lambda e: self.summary_text.config(cursor="hand2"))
        self.summary_text.tag_bind("hyperlink", "<Leave>", lambda e: self.summary_text.config(cursor=""))
        
        # Initial message
        self._show_initial_message()
    
    def _show_initial_message(self):
        """Show initial welcome message."""
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        
        msg = '''Welcome to the Summary Tab! 📋

This is where you'll see:
• 🎯 Action Items - Tasks that require your attention
• 📰 Newsletter Summaries - Quick summaries of newsletters
• ℹ️ FYI Items - Information-only emails for your awareness
• 🎉 Optional Items - Optional meetings and events

To get started:
1. Process emails in the Processing tab
2. Review and categorize in the Editing tab  
3. Click "Generate Summary" above to create your focused summary

Your summary will appear here with interactive task tracking! 🚀'''
        
        self.summary_text.insert(tk.END, msg)
        self.summary_text.config(state=tk.DISABLED)
    
    def _on_mark_complete_click(self):
        """Handle mark complete button click."""
        selected_indices = []
        for i, var in enumerate(self.task_vars):
            if var.get():
                selected_indices.append(i)
        
        if not selected_indices:
            messagebox.showinfo("No Selection", "Please select tasks to mark as complete.")
            return
        
        # Get task identifiers
        task_ids = [self.task_labels[i] for i in selected_indices]
        self.on_mark_task_complete_callback(task_ids)
    
    def _on_link_click(self, event):
        """Handle hyperlink click in summary."""
        index = self.summary_text.index(f"@{event.x},{event.y}")
        for tag_range in self.summary_text.tag_ranges("hyperlink"):
            if self.summary_text.compare(index, ">=", tag_range[0]) and \
               self.summary_text.compare(index, "<=", tag_range[1]):
                url = self.summary_text.get(tag_range[0], tag_range[1])
                open_url(url)
                break
    
    # Public methods for updating UI from controller
    
    def display_summary(self, summary_data: Dict[str, Any]):
        """Display the summary with all sections.
        
        Args:
            summary_data: Dictionary containing:
                - action_items: List of action item dicts
                - newsletters: List of newsletter summary dicts
                - fyi_items: List of FYI email dicts
                - optional_items: List of optional event dicts
                - outstanding_tasks: List of outstanding task dicts from previous runs
        """
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        
        # Clear task tracking
        self.task_checkboxes.clear()
        self.task_vars.clear()
        self.task_labels.clear()
        
        # Header
        self.summary_text.insert(tk.END, "📋 Your Email Summary\n", "heading")
        self.summary_text.insert(tk.END, f"Generated: {summary_data.get('generated_time', 'Unknown')}\n\n")
        
        # Outstanding tasks from previous runs
        outstanding = summary_data.get('outstanding_tasks', [])
        if outstanding:
            self.summary_text.insert(tk.END, "⏳ Outstanding Tasks from Previous Runs\n", "subheading")
            for task in outstanding:
                self._insert_task_item(task, is_outstanding=True)
            self.summary_text.insert(tk.END, "\n")
        
        # Action items
        action_items = summary_data.get('action_items', [])
        if action_items:
            self.summary_text.insert(tk.END, f"🎯 Action Items ({len(action_items)})\n", "subheading")
            for item in action_items:
                self._insert_task_item(item)
            self.summary_text.insert(tk.END, "\n")
        
        # Newsletter summaries
        newsletters = summary_data.get('newsletters', [])
        if newsletters:
            self.summary_text.insert(tk.END, f"📰 Newsletter Summaries ({len(newsletters)})\n", "subheading")
            for newsletter in newsletters:
                self._insert_newsletter(newsletter)
            self.summary_text.insert(tk.END, "\n")
        
        # FYI items
        fyi_items = summary_data.get('fyi_items', [])
        if fyi_items:
            self.summary_text.insert(tk.END, f"ℹ️ FYI Items ({len(fyi_items)})\n", "subheading")
            for fyi in fyi_items:
                self._insert_fyi_item(fyi)
            self.summary_text.insert(tk.END, "\n")
        
        # Optional items
        optional_items = summary_data.get('optional_items', [])
        if optional_items:
            self.summary_text.insert(tk.END, f"🎉 Optional Events ({len(optional_items)})\n", "subheading")
            for optional in optional_items:
                self._insert_optional_item(optional)
            self.summary_text.insert(tk.END, "\n")
        
        # Summary stats
        total_items = len(action_items) + len(outstanding)
        self.summary_text.insert(tk.END, f"\n📊 Summary: {total_items} tasks, {len(newsletters)} newsletters, {len(fyi_items)} FYI items, {len(optional_items)} optional events\n")
        
        self.summary_text.config(state=tk.DISABLED)
    
    def _insert_task_item(self, task: Dict[str, Any], is_outstanding: bool = False):
        """Insert a task item with checkbox.
        
        Args:
            task: Task dictionary with 'summary', 'deadline', 'email_subject', etc.
            is_outstanding: Whether this is an outstanding task from a previous run
        """
        # Create checkbox for task completion
        var = tk.BooleanVar(value=False)
        self.task_vars.append(var)
        
        # Create task identifier (for tracking completion)
        task_id = f"{task.get('email_subject', 'Unknown')}:{task.get('summary', 'Unknown')[:50]}"
        self.task_labels.append(task_id)
        
        # Insert checkbox window
        pos = self.summary_text.index(tk.INSERT)
        checkbox = ttk.Checkbutton(self.summary_text, variable=var, text="")
        self.summary_text.window_create(pos, window=checkbox)
        self.task_checkboxes.append(checkbox)
        
        # Insert task text
        prefix = "⏰ " if is_outstanding else "• "
        task_text = f" {prefix}{task.get('summary', 'No summary')}"
        if task.get('deadline'):
            task_text += f" [Due: {task['deadline']}]"
        task_text += f" ({task.get('email_subject', 'Unknown email')})\n"
        
        tag = "completed" if task.get('completed') else "action_item"
        self.summary_text.insert(tk.END, task_text, tag)
    
    def _insert_newsletter(self, newsletter: Dict[str, Any]):
        """Insert a newsletter summary.
        
        Args:
            newsletter: Newsletter dict with 'subject', 'summary', 'key_points'
        """
        self.summary_text.insert(tk.END, f"• {newsletter.get('subject', 'Unknown Newsletter')}\n", "action_item")
        self.summary_text.insert(tk.END, f"  Summary: {newsletter.get('summary', 'No summary available')}\n", "fyi_item")
        if newsletter.get('key_points'):
            for point in newsletter['key_points']:
                self.summary_text.insert(tk.END, f"    - {point}\n", "fyi_item")
        self.summary_text.insert(tk.END, "\n")
    
    def _insert_fyi_item(self, fyi: Dict[str, Any]):
        """Insert an FYI item.
        
        Args:
            fyi: FYI dict with 'subject', 'from', 'summary'
        """
        text = f"• {fyi.get('subject', 'Unknown')} (from {fyi.get('from', 'Unknown')})\n"
        if fyi.get('summary'):
            text += f"  {fyi['summary']}\n"
        self.summary_text.insert(tk.END, text, "fyi_item")
    
    def _insert_optional_item(self, optional: Dict[str, Any]):
        """Insert an optional event item.
        
        Args:
            optional: Optional event dict with 'subject', 'date', 'time', 'relevance'
        """
        text = f"• {optional.get('subject', 'Unknown Event')}"
        if optional.get('date'):
            text += f" - {optional['date']}"
        if optional.get('time'):
            text += f" at {optional['time']}"
        text += "\n"
        if optional.get('relevance'):
            text += f"  Relevance: {optional['relevance']}\n"
        self.summary_text.insert(tk.END, text, "action_item")
    
    def set_generate_button_state(self, enabled: bool):
        """Set generate button state.
        
        Args:
            enabled: Whether button should be enabled
        """
        self.generate_btn.config(state=tk.NORMAL if enabled else tk.DISABLED)
    
    def clear_summary(self):
        """Clear the summary display."""
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.config(state=tk.DISABLED)
        self.task_checkboxes.clear()
        self.task_vars.clear()
        self.task_labels.clear()
    
    def show_error(self, error_message: str):
        """Show an error message in the summary area.
        
        Args:
            error_message: Error message to display
        """
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, f"❌ Error generating summary:\n\n{error_message}\n\nPlease try again.")
        self.summary_text.config(state=tk.DISABLED)
    
    def append_text(self, text: str, tag: Optional[str] = None):
        """Append text to summary area.
        
        Args:
            text: Text to append
            tag: Optional tag for formatting
        """
        self.summary_text.config(state=tk.NORMAL)
        if tag:
            self.summary_text.insert(tk.END, text, tag)
        else:
            self.summary_text.insert(tk.END, text)
        self.summary_text.see(tk.END)
        self.summary_text.config(state=tk.DISABLED)
