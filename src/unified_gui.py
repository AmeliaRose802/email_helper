#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unified GUI for Email Helper - Main Application Interface.

This module provides the primary graphical user interface for the Email Helper
application, integrating all components into a cohesive user experience for
email management, AI processing, and task tracking.

The UnifiedEmailGUI class serves as the main application window and orchestrates
interactions between:
- Email loading and display from Outlook
- AI-powered email classification and analysis  
- Task creation, management, and completion tracking
- Summary generation and formatted display
- User feedback collection for accuracy improvements
- Settings and configuration management

Key Features:
- Tabbed interface for different workflow stages
- Real-time processing with progress indicators
- Integrated task management with Outlook email movement
- Comprehensive summary generation with multiple output formats
- User correction and feedback system for AI improvement
- Persistent task storage across sessions

This module follows the project's GUI patterns and integrates with all core
backend components while maintaining a responsive user experience.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
import threading
import os
import webbrowser
import sys
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from outlook_manager import OutlookManager
from ai_processor import AIProcessor
from email_analyzer import EmailAnalyzer
from summary_generator import SummaryGenerator
from email_processor import EmailProcessor
from task_persistence import TaskPersistence


class UnifiedEmailGUI:
    """Unified GUI application for email management and AI processing.
    
    This class provides a comprehensive graphical user interface for the email helper
    system, integrating email processing, AI analysis, task management, and user
    interaction components into a single unified application window.
    
    The GUI handles:
    - Email loading and display from Outlook
    - AI-powered email classification and analysis
    - Task creation and management
    - Summary generation and display
    - User feedback collection and accuracy tracking
    
    Attributes:
        outlook_manager (OutlookManager): Handles Outlook COM integration
        ai_processor (AIProcessor): Manages AI processing and Azure OpenAI calls
        email_analyzer (EmailAnalyzer): Analyzes and categorizes emails
        summary_generator (SummaryGenerator): Generates formatted summaries
        email_processor (EmailProcessor): Orchestrates email processing workflow
        task_persistence (TaskPersistence): Manages task storage and lifecycle
        email_suggestions (list): Storage for email categorization suggestions
        action_items_data (dict): Current batch action items organized by category
        summary_sections (dict): Generated summary sections for display
        processing_cancelled (bool): Flag for cancelling long-running operations
    """
    
    def __init__(self):
        # Initialize components
        self.outlook_manager = OutlookManager()
        self.ai_processor = AIProcessor()
        self.email_analyzer = EmailAnalyzer(self.ai_processor)
        self.summary_generator = SummaryGenerator()
        self.email_processor = EmailProcessor(
            self.outlook_manager,
            self.ai_processor,
            self.email_analyzer,
            self.summary_generator
        )
        self.task_persistence = TaskPersistence()  # Add task persistence
        
        # Data storage
        self.email_suggestions = []
        self.action_items_data = {}
        self.summary_sections = {}
        self.processing_cancelled = False
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("AI Email Management")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Create GUI components
        self.create_widgets()
        
        # Initialize Outlook connection
        self.outlook_manager.connect_to_outlook()
    
    def create_widgets(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Email Processing
        self.processing_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.processing_frame, text="1. Process Emails")
        self.create_processing_tab()
        
        # Tab 2: Email Review & Editing
        self.editing_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.editing_frame, text="2. Review & Edit")
        self.create_editing_tab()
        
        # Tab 3: Summary Generation & Viewing
        self.summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_frame, text="3. Summary & Results")
        self.create_summary_tab()
        
        # Tab 4: Accuracy Dashboard
        self.accuracy_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.accuracy_frame, text="4. Accuracy Dashboard")
        self.create_accuracy_tab()
        
        # Create status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 5))
        
        # Initially disable tabs 1, 3 (enable summary tab immediately for task viewing)
        self.notebook.tab(1, state="disabled")  # Review & Edit tab - requires email processing
        self.notebook.tab(3, state="disabled")  # Accuracy Dashboard - requires email processing
    
    def create_processing_tab(self):
        # Email count selection
        self.email_count_var = tk.StringVar(value="50")
        email_count_frame = ttk.Frame(self.processing_frame)
        email_count_frame.pack(pady=20)
        
        ttk.Label(email_count_frame, text="Number of emails:").pack(side=tk.LEFT)
        for count in [25, 50, 100, 200]:
            ttk.Radiobutton(email_count_frame, text=str(count), variable=self.email_count_var, 
                           value=str(count)).pack(side=tk.LEFT, padx=5)
        
        # Custom option
        self.custom_count_entry = ttk.Entry(email_count_frame, width=10)
        self.custom_count_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Processing controls
        control_frame = ttk.Frame(self.processing_frame)
        control_frame.pack(pady=20)
        
        self.start_processing_btn = ttk.Button(control_frame, text="Start Processing", 
                                              command=self.start_email_processing)
        self.start_processing_btn.pack(side=tk.LEFT, padx=5)
        
        self.cancel_processing_btn = ttk.Button(control_frame, text="Cancel", 
                                               command=self.cancel_processing, 
                                               state=tk.DISABLED)
        self.cancel_processing_btn.pack(side=tk.LEFT, padx=5)
        
        # Accuracy Dashboard access button
        self.accuracy_btn = ttk.Button(control_frame, text="📊 Accuracy Dashboard", 
                                      command=self.open_accuracy_dashboard)
        self.accuracy_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress section
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.processing_frame, variable=self.progress_var, 
                                          maximum=100)
        self.progress_bar.pack(pady=10, fill=tk.X, padx=20)
        
        self.progress_text = scrolledtext.ScrolledText(self.processing_frame, height=15, 
                                                      state=tk.DISABLED, wrap=tk.WORD)
        self.progress_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    def create_editing_tab(self):
        # Main container
        main_frame = ttk.Frame(self.editing_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Create email list
        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        columns = ('Subject', 'From', 'Category', 'AI Summary', 'Date')
        self.email_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)
        
        # Initialize sorting state
        self.sort_column = None
        self.sort_reverse = False
        
        # Configure columns with sorting
        for col in columns:
            self.email_tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            
        self.email_tree.column('Subject', width=250)
        self.email_tree.column('From', width=150)
        self.email_tree.column('Category', width=150)
        self.email_tree.column('AI Summary', width=300)
        self.email_tree.column('Date', width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.email_tree.yview)
        self.email_tree.configure(yscrollcommand=scrollbar.set)
        
        self.email_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.email_tree.bind('<<TreeviewSelect>>', self.on_email_select)
        
        # Details panel
        details_frame = ttk.LabelFrame(main_frame, text="Email Details", padding="10")
        details_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        details_frame.columnconfigure(1, weight=1)
        details_frame.rowconfigure(4, weight=1)
        
        ttk.Label(details_frame, text="Category:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(details_frame, textvariable=self.category_var, 
                                          values=self.get_category_display_names(), 
                                          state="readonly")
        self.category_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        ttk.Label(details_frame, text="Category:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(details_frame, textvariable=self.category_var, 
                                          values=self.get_category_display_names(), 
                                          state="readonly")
        self.category_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        self.category_combo.bind('<<ComboboxSelected>>', self.on_category_change)
        
        # Add info label about auto-apply
        info_label = ttk.Label(details_frame, text="ℹ️ Changes apply automatically when category changes or switching emails", 
                              font=('Segoe UI', 8), foreground="#666666")
        info_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(details_frame, text="Reason (optional):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.explanation_var = tk.StringVar()
        self.explanation_entry = ttk.Entry(details_frame, textvariable=self.explanation_var)
        self.explanation_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        self.apply_btn = ttk.Button(details_frame, text="Manual Apply", 
                                   command=self.apply_category_change, state=tk.DISABLED)
        self.apply_btn.grid(row=3, column=1, sticky=tk.E, pady=5, padx=(5, 0))
        
        self.preview_text = scrolledtext.ScrolledText(details_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        self.preview_text.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
        self.current_email_index = None
        self.original_category = None
        
        # Controls
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=(15, 0))
        
        ttk.Button(button_frame, text="Apply to Outlook", 
                  command=self.apply_to_outlook).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Generate Summary", 
                  command=self.proceed_to_summary).pack(side=tk.LEFT, padx=5)
    
    def create_summary_tab(self):
        main_frame = ttk.Frame(self.summary_frame, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Control frame with task management buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(pady=(0, 20))
        
        self.generate_summary_btn = ttk.Button(control_frame, text="Generate Summary", 
                                              command=self.generate_summary)
        self.generate_summary_btn.pack(side=tk.LEFT, padx=5)
        
        # View Outstanding Tasks button for accessing persistent tasks without email processing
        ttk.Button(control_frame, text="View Outstanding Tasks", 
                  command=self.view_outstanding_tasks_only).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Open in Browser", 
                  command=self.open_summary_in_browser).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Task Statistics", 
                  command=self.show_task_statistics).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Mark Tasks Complete", 
                  command=self.show_task_completion_dialog).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Process New Batch", 
                  command=self.start_new_session).pack(side=tk.LEFT, padx=5)
        
        # Enhanced summary text widget with rich formatting
        self.summary_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, 
                                                     height=20, state=tk.DISABLED,
                                                     font=('Segoe UI', 10))
        self.summary_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Configure rich text formatting tags for summary display
        self._configure_summary_text_tags()
    
    def _configure_summary_text_tags(self):
        """Configure rich text formatting tags for beautiful summary display"""
        # Main title
        self.summary_text.tag_configure("main_title", 
                                       font=("Segoe UI", 16, "bold"), 
                                       foreground="#007acc",
                                       justify="center")
        
        # Subtitle
        self.summary_text.tag_configure("subtitle", 
                                       font=("Segoe UI", 12), 
                                       foreground="#666666",
                                       justify="center")
        
        # Overview stats
        self.summary_text.tag_configure("overview_title", 
                                       font=("Segoe UI", 14, "bold"), 
                                       foreground="#005a8b")
        
        self.summary_text.tag_configure("overview_stats", 
                                       font=("Segoe UI", 11), 
                                       background="#e8f4fd",
                                       foreground="#005a8b")
        
        # Section headers with different colors
        self.summary_text.tag_configure("section_required", 
                                       font=("Segoe UI", 13, "bold"), 
                                       foreground="#dc3545",
                                       background="#ffe6e6")
        
        self.summary_text.tag_configure("section_team", 
                                       font=("Segoe UI", 13, "bold"), 
                                       foreground="#856404",
                                       background="#fff3cd")
        
        self.summary_text.tag_configure("section_optional", 
                                       font=("Segoe UI", 13, "bold"), 
                                       foreground="#0c5460",
                                       background="#d1ecf1")
        
        self.summary_text.tag_configure("section_jobs", 
                                       font=("Segoe UI", 13, "bold"), 
                                       foreground="#155724",
                                       background="#d4edda")
        
        self.summary_text.tag_configure("section_events", 
                                       font=("Segoe UI", 13, "bold"), 
                                       foreground="#4c1d95",
                                       background="#f8e8ff")
        
        self.summary_text.tag_configure("section_fyi", 
                                       font=("Segoe UI", 13, "bold"), 
                                       foreground="#0369a1",
                                       background="#f0f8ff")
        
        self.summary_text.tag_configure("section_newsletter", 
                                       font=("Segoe UI", 13, "bold"), 
                                       foreground="#ea580c",
                                       background="#fff8dc")
        
        # Item titles
        self.summary_text.tag_configure("item_title", 
                                       font=("Segoe UI", 11, "bold"), 
                                       foreground="#333333")
        
        # Completed item titles (with green checkmark styling)
        self.summary_text.tag_configure("item_title_completed", 
                                       font=("Segoe UI", 11, "bold"), 
                                       foreground="#228B22")
        
        # Item metadata (from, date, etc.)
        self.summary_text.tag_configure("item_meta", 
                                       font=("Segoe UI", 9), 
                                       foreground="#666666")
        
        # Item content labels
        self.summary_text.tag_configure("content_label", 
                                       font=("Segoe UI", 10, "bold"), 
                                       foreground="#555555")
        
        # Item content text
        self.summary_text.tag_configure("content_text", 
                                       font=("Segoe UI", 10), 
                                       foreground="#333333")
        
        # Links
        self.summary_text.tag_configure("link", 
                                       font=("Segoe UI", 9, "underline"), 
                                       foreground="#007acc")
        
        # Separators
        self.summary_text.tag_configure("separator", 
                                       font=("Consolas", 8), 
                                       foreground="#cccccc")
        
        # Empty section message
        self.summary_text.tag_configure("empty_section", 
                                       font=("Segoe UI", 10, "italic"), 
                                       foreground="#999999",
                                       justify="center")
        
        # Completion status styling
        self.summary_text.tag_configure("completion_status", 
                                       font=("Segoe UI", 10, "bold"), 
                                       foreground="#228B22")
        
        # Completion notes
        self.summary_text.tag_configure("completion_note", 
                                       font=("Segoe UI", 9, "italic"), 
                                       foreground="#555555")
        
        # Configure link click behavior
        self.summary_text.tag_bind("link", "<Button-1>", self._on_summary_link_click)
        self.summary_text.tag_bind("link", "<Enter>", lambda e: self.summary_text.config(cursor="hand2"))
        self.summary_text.tag_bind("link", "<Leave>", lambda e: self.summary_text.config(cursor=""))
    
    def create_accuracy_tab(self):
        """Create the accuracy dashboard tab with comprehensive analytics"""
        main_frame = ttk.Frame(self.accuracy_frame, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title and controls section
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(title_frame, text="📊 Accuracy Dashboard", 
                 font=("Segoe UI", 16, "bold"), foreground="#007acc").pack(side=tk.LEFT)
        
        # Control buttons
        button_frame = ttk.Frame(title_frame)
        button_frame.pack(side=tk.RIGHT)
        
        ttk.Button(button_frame, text="🔄 Refresh", 
                  command=self.refresh_accuracy_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📤 Export CSV", 
                  command=self.export_accuracy_data).pack(side=tk.LEFT, padx=5)
        
        # Create notebook for different views
        self.accuracy_notebook = ttk.Notebook(main_frame)
        self.accuracy_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Overview & Metrics
        self.metrics_frame = ttk.Frame(self.accuracy_notebook)
        self.accuracy_notebook.add(self.metrics_frame, text="📈 Overview")
        self.create_metrics_view()
        
        # Tab 2: Time Series Analysis
        self.trends_frame = ttk.Frame(self.accuracy_notebook)
        self.accuracy_notebook.add(self.trends_frame, text="📊 Trends")
        self.create_trends_view()
        
        # Tab 3: Category Performance
        self.categories_frame = ttk.Frame(self.accuracy_notebook)
        self.accuracy_notebook.add(self.categories_frame, text="🏷️ Categories")
        self.create_categories_view()
        
        # Tab 4: Session Details
        self.sessions_frame = ttk.Frame(self.accuracy_notebook)
        self.accuracy_notebook.add(self.sessions_frame, text="📋 Sessions")
        self.create_sessions_view()
    
    def create_metrics_view(self):
        """Create the overview metrics view"""
        # Key metrics cards at the top
        metrics_container = ttk.Frame(self.metrics_frame)
        metrics_container.pack(fill=tk.X, padx=20, pady=20)
        
        # Create metric cards
        self.overall_accuracy_label = ttk.Label(metrics_container, 
                                               text="Overall Accuracy\n---%", 
                                               font=("Segoe UI", 12, "bold"),
                                               anchor="center", width=15)
        self.overall_accuracy_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.seven_day_label = ttk.Label(metrics_container, 
                                        text="7-Day Average\n---%", 
                                        font=("Segoe UI", 12, "bold"),
                                        anchor="center", width=15)
        self.seven_day_label.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        self.total_sessions_label = ttk.Label(metrics_container, 
                                             text="Total Sessions\n---", 
                                             font=("Segoe UI", 12, "bold"),
                                             anchor="center", width=15)
        self.total_sessions_label.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        
        self.total_emails_label = ttk.Label(metrics_container, 
                                           text="Total Emails\n---", 
                                           font=("Segoe UI", 12, "bold"),
                                           anchor="center", width=15)
        self.total_emails_label.grid(row=0, column=3, padx=10, pady=10, sticky="nsew")
        
        # Configure grid weights
        for i in range(4):
            metrics_container.columnconfigure(i, weight=1)
        
        # Trend indicator
        self.trend_frame = ttk.LabelFrame(self.metrics_frame, text="Accuracy Trend", padding="10")
        self.trend_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.trend_label = ttk.Label(self.trend_frame, 
                                    text="📊 Trend: Analyzing...", 
                                    font=("Segoe UI", 11))
        self.trend_label.pack()
        
        # Recent activity summary
        self.activity_frame = ttk.LabelFrame(self.metrics_frame, text="Recent Activity", padding="10")
        self.activity_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.activity_text = scrolledtext.ScrolledText(self.activity_frame, 
                                                      height=10, 
                                                      wrap=tk.WORD,
                                                      font=("Consolas", 9))
        self.activity_text.pack(fill=tk.BOTH, expand=True)
    
    def create_trends_view(self):
        """Create the trends analysis view"""
        # Date range selection
        controls_frame = ttk.Frame(self.trends_frame)
        controls_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(controls_frame, text="Time Range:").pack(side=tk.LEFT, padx=5)
        
        self.time_range_var = tk.StringVar(value="30 days")
        range_combo = ttk.Combobox(controls_frame, textvariable=self.time_range_var,
                                  values=["7 days", "30 days", "90 days", "1 year", "All time"],
                                  state="readonly", width=12)
        range_combo.pack(side=tk.LEFT, padx=5)
        range_combo.bind("<<ComboboxSelected>>", self.update_trends_chart)
        
        ttk.Label(controls_frame, text="Granularity:").pack(side=tk.LEFT, padx=(20,5))
        
        self.granularity_var = tk.StringVar(value="daily")
        granularity_combo = ttk.Combobox(controls_frame, textvariable=self.granularity_var,
                                        values=["daily", "weekly", "monthly"],
                                        state="readonly", width=10)
        granularity_combo.pack(side=tk.LEFT, padx=5)
        granularity_combo.bind("<<ComboboxSelected>>", self.update_trends_chart)
        
        ttk.Button(controls_frame, text="Update Chart", 
                  command=self.update_trends_chart).pack(side=tk.LEFT, padx=20)
        
        # Chart area placeholder
        self.trends_chart_frame = ttk.LabelFrame(self.trends_frame, text="Accuracy Trends Over Time", padding="10")
        self.trends_chart_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.trends_chart_label = ttk.Label(self.trends_chart_frame, 
                                           text="📈 Chart will appear here after clicking 'Update Chart'\n\n" +
                                                "This will show accuracy trends over time with configurable granularity.",
                                           font=("Segoe UI", 11),
                                           anchor="center")
        self.trends_chart_label.pack(expand=True)
    
    def create_categories_view(self):
        """Create the category performance view"""
        # Controls
        controls_frame = ttk.Frame(self.categories_frame)
        controls_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(controls_frame, text="Analysis Period:").pack(side=tk.LEFT, padx=5)
        
        self.category_period_var = tk.StringVar(value="30 days")
        period_combo = ttk.Combobox(controls_frame, textvariable=self.category_period_var,
                                   values=["7 days", "30 days", "90 days", "All time"],
                                   state="readonly", width=12)
        period_combo.pack(side=tk.LEFT, padx=5)
        period_combo.bind("<<ComboboxSelected>>", self.update_category_analysis)
        
        ttk.Button(controls_frame, text="Analyze Categories", 
                  command=self.update_category_analysis).pack(side=tk.LEFT, padx=20)
        
        # Category performance table
        self.category_table_frame = ttk.LabelFrame(self.categories_frame, text="Category Performance", padding="10")
        self.category_table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create treeview for category data
        self.category_tree = ttk.Treeview(self.category_table_frame, 
                                         columns=("accuracy", "corrections", "sessions"),
                                         show="tree headings", height=15)
        
        self.category_tree.heading("#0", text="Category")
        self.category_tree.heading("accuracy", text="Accuracy %")
        self.category_tree.heading("corrections", text="Corrections")
        self.category_tree.heading("sessions", text="Sessions")
        
        self.category_tree.column("#0", width=200, minwidth=150)
        self.category_tree.column("accuracy", width=100, minwidth=80, anchor="center")
        self.category_tree.column("corrections", width=100, minwidth=80, anchor="center")
        self.category_tree.column("sessions", width=100, minwidth=80, anchor="center")
        
        # Scrollbar for tree
        tree_scroll = ttk.Scrollbar(self.category_table_frame, orient="vertical", command=self.category_tree.yview)
        self.category_tree.configure(yscroll=tree_scroll.set)
        
        self.category_tree.pack(side="left", fill=tk.BOTH, expand=True)
        tree_scroll.pack(side="right", fill="y")
    
    def create_sessions_view(self):
        """Create the sessions detail view"""
        # Controls
        controls_frame = ttk.Frame(self.sessions_frame)
        controls_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(controls_frame, text="Sessions to show:").pack(side=tk.LEFT, padx=5)
        
        self.session_count_var = tk.StringVar(value="20")
        count_combo = ttk.Combobox(controls_frame, textvariable=self.session_count_var,
                                  values=["10", "20", "50", "100"],
                                  state="readonly", width=8)
        count_combo.pack(side=tk.LEFT, padx=5)
        count_combo.bind("<<ComboboxSelected>>", self.update_sessions_list)
        
        ttk.Button(controls_frame, text="Load Sessions", 
                  command=self.update_sessions_list).pack(side=tk.LEFT, padx=20)
        
        # Sessions table
        self.sessions_table_frame = ttk.LabelFrame(self.sessions_frame, text="Recent Sessions", padding="10")
        self.sessions_table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create treeview for session data
        self.sessions_tree = ttk.Treeview(self.sessions_table_frame, 
                                         columns=("date", "accuracy", "emails", "corrections"),
                                         show="tree headings", height=15)
        
        self.sessions_tree.heading("#0", text="Session ID")
        self.sessions_tree.heading("date", text="Date/Time")
        self.sessions_tree.heading("accuracy", text="Accuracy %")
        self.sessions_tree.heading("emails", text="Emails")
        self.sessions_tree.heading("corrections", text="Corrections")
        
        self.sessions_tree.column("#0", width=150, minwidth=120)
        self.sessions_tree.column("date", width=150, minwidth=120)
        self.sessions_tree.column("accuracy", width=100, minwidth=80, anchor="center")
        self.sessions_tree.column("emails", width=80, minwidth=60, anchor="center")
        self.sessions_tree.column("corrections", width=100, minwidth=80, anchor="center")
        
        # Scrollbar for sessions tree
        sessions_scroll = ttk.Scrollbar(self.sessions_table_frame, orient="vertical", command=self.sessions_tree.yview)
        self.sessions_tree.configure(yscroll=sessions_scroll.set)
        
        self.sessions_tree.pack(side="left", fill=tk.BOTH, expand=True)
        sessions_scroll.pack(side="right", fill="y")
    
    def refresh_accuracy_data(self):
        """Refresh all accuracy dashboard data"""
        try:
            # Import accuracy tracker
            from accuracy_tracker import AccuracyTracker
            
            # Initialize tracker with same path logic as ai_processor
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            runtime_base_dir = os.path.join(project_root, 'runtime_data')
            self.accuracy_tracker = AccuracyTracker(runtime_base_dir)
            
            # Update all views
            self.update_metrics_display()
            self.update_trends_chart()
            self.update_category_analysis()
            self.update_sessions_list()
            
            self.status_var.set("Accuracy dashboard refreshed successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh accuracy data:\n{str(e)}")
            self.status_var.set("Error refreshing accuracy dashboard")
    
    def update_metrics_display(self):
        """Update the overview metrics display"""
        try:
            if not hasattr(self, 'accuracy_tracker'):
                self.refresh_accuracy_data()
                return
            
            metrics = self.accuracy_tracker.get_dashboard_metrics()
            
            # Update metric labels
            overall = metrics.get('overall_stats', {})
            self.overall_accuracy_label.config(text=f"Overall Accuracy\n{overall.get('average_accuracy', 0):.1f}%")
            
            recent = metrics.get('recent_performance', {})
            self.seven_day_label.config(text=f"7-Day Average\n{recent.get('last_7_days', 0):.1f}%")
            
            self.total_sessions_label.config(text=f"Total Sessions\n{overall.get('total_sessions', 0)}")
            self.total_emails_label.config(text=f"Total Emails\n{overall.get('total_emails', 0):,}")
            
            # Update trend indicator
            trend = metrics.get('trend_analysis', {})
            trend_direction = trend.get('improvement_trend', 'stable')
            trend_pct = trend.get('trend_percentage', 0)
            
            if trend_direction == 'improving':
                trend_text = f"📈 Improving (+{trend_pct:.1f}%)"
                trend_color = "green"
            elif trend_direction == 'declining':
                trend_text = f"📉 Declining ({trend_pct:.1f}%)"
                trend_color = "red"
            else:
                trend_text = "📊 Stable"
                trend_color = "blue"
            
            self.trend_label.config(text=f"Trend: {trend_text}", foreground=trend_color)
            
            # Update activity summary
            self.activity_text.delete(1.0, tk.END)
            
            activity_summary = f"""📊 ACCURACY DASHBOARD SUMMARY
{'='*50}

📈 Overall Performance:
   • Average Accuracy: {overall.get('average_accuracy', 0):.1f}%
   • Latest Session: {overall.get('latest_accuracy', 0):.1f}%
   • Total Corrections: {overall.get('total_corrections', 0)}

🕒 Recent Performance:
   • Last 7 Days: {recent.get('last_7_days', 0):.1f}% ({recent.get('sessions_last_7_days', 0)} sessions)
   • Last 30 Days: {recent.get('last_30_days', 0):.1f}% ({recent.get('sessions_last_30_days', 0)} sessions)

📊 Session Statistics:
   • Min Accuracy: {metrics.get('session_statistics', {}).get('min_accuracy', 0):.1f}%
   • Max Accuracy: {metrics.get('session_statistics', {}).get('max_accuracy', 0):.1f}%
   • Median Accuracy: {metrics.get('session_statistics', {}).get('median_accuracy', 0):.1f}%

🏷️ Top Correction Categories:"""
            
            # Add category summary
            category_summary = metrics.get('category_summary', {})
            for rank_key in sorted(category_summary.keys()):
                cat_info = category_summary[rank_key]
                activity_summary += f"\n   • {cat_info.get('category', 'Unknown')}: {cat_info.get('corrections', 0)} corrections"
            
            # Add data quality info
            data_quality = metrics.get('data_quality', {})
            date_range = data_quality.get('date_range', {})
            
            activity_summary += f"""

🔍 Data Quality:
   • Total Data Points: {data_quality.get('total_data_points', 0)}
   • Date Range: {date_range.get('earliest', 'N/A')[:10]} to {date_range.get('latest', 'N/A')[:10]}
   • Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            self.activity_text.insert(tk.END, activity_summary)
            
        except Exception as e:
            self.activity_text.delete(1.0, tk.END)
            self.activity_text.insert(tk.END, f"Error loading metrics: {str(e)}")
    
    def update_trends_chart(self, event=None):
        """Update the trends chart (placeholder for now)"""
        try:
            if not hasattr(self, 'accuracy_tracker'):
                self.refresh_accuracy_data()
                return
            
            # Get time range
            time_range = self.time_range_var.get()
            granularity = self.granularity_var.get()
            
            # Calculate date range
            from datetime import datetime, timedelta
            end_date = datetime.now()
            
            if time_range == "7 days":
                start_date = end_date - timedelta(days=7)
            elif time_range == "30 days":
                start_date = end_date - timedelta(days=30)
            elif time_range == "90 days":
                start_date = end_date - timedelta(days=90)
            elif time_range == "1 year":
                start_date = end_date - timedelta(days=365)
            else:  # All time
                start_date = None
            
            # Get time series data
            ts_data = self.accuracy_tracker.get_time_series_data(start_date, end_date, granularity)
            
            # Update chart placeholder
            if ts_data.empty:
                chart_text = f"📈 No data available for {time_range} with {granularity} granularity\n\n" + \
                           "Process some emails to generate accuracy trends data."
            else:
                chart_text = f"📈 Trends for {time_range} ({granularity} granularity)\n\n" + \
                           f"Data Points: {len(ts_data)}\n" + \
                           f"Accuracy Range: {ts_data['accuracy_rate'].min():.1f}% - {ts_data['accuracy_rate'].max():.1f}%\n" + \
                           f"Average: {ts_data['accuracy_rate'].mean():.1f}%\n\n" + \
                           "📊 Chart visualization requires matplotlib integration\n" + \
                           "(Coming in next phase of development)"
            
            self.trends_chart_label.config(text=chart_text)
            
        except Exception as e:
            self.trends_chart_label.config(text=f"Error loading trends: {str(e)}")
    
    def update_category_analysis(self, event=None):
        """Update the category performance analysis"""
        try:
            if not hasattr(self, 'accuracy_tracker'):
                self.refresh_accuracy_data()
                return
            
            # Clear existing data
            for item in self.category_tree.get_children():
                self.category_tree.delete(item)
            
            # Get period
            period_str = self.category_period_var.get()
            days_back = {"7 days": 7, "30 days": 30, "90 days": 90, "All time": 9999}.get(period_str, 30)
            
            # Get category performance data
            category_data = self.accuracy_tracker.get_category_performance_summary(days_back)
            
            if not category_data:
                self.category_tree.insert("", "end", text="No category data available", values=("--", "--", "--"))
                return
            
            # Populate tree
            for category, stats in category_data.items():
                accuracy = stats.get('accuracy_rate', 0)
                corrections = stats.get('total_corrections', 0)
                sessions = stats.get('sessions_involved', 0)
                display_name = stats.get('category_name', category)
                
                self.category_tree.insert("", "end", 
                                         text=display_name,
                                         values=(f"{accuracy:.1f}%", corrections, sessions))
            
        except Exception as e:
            self.category_tree.insert("", "end", text=f"Error: {str(e)}", values=("--", "--", "--"))
    
    def update_sessions_list(self, event=None):
        """Update the sessions list"""
        try:
            if not hasattr(self, 'accuracy_tracker'):
                self.refresh_accuracy_data()
                return
            
            # Clear existing data
            for item in self.sessions_tree.get_children():
                self.sessions_tree.delete(item)
            
            # Get session count
            session_count = int(self.session_count_var.get())
            
            # Get session comparison data
            session_data = self.accuracy_tracker.get_session_comparison_data()
            
            if session_data.empty:
                self.sessions_tree.insert("", "end", text="No session data", 
                                         values=("--", "--", "--", "--"))
                return
            
            # Show recent sessions (limit to requested count)
            recent_sessions = session_data.head(session_count)
            
            for _, session in recent_sessions.iterrows():
                session_id = session.get('session_run_id', 'Unknown')
                date_time = session.get('session_date', 'Unknown')
                if hasattr(date_time, 'strftime'):
                    date_str = date_time.strftime('%Y-%m-%d %H:%M')
                else:
                    date_str = str(date_time)[:16]
                
                accuracy = session.get('current_accuracy', 0)
                emails = session.get('current_emails', 0)
                corrections = session.get('current_modifications', 0)
                
                self.sessions_tree.insert("", "end", 
                                         text=session_id,
                                         values=(date_str, f"{accuracy:.1f}%", emails, corrections))
            
        except Exception as e:
            self.sessions_tree.insert("", "end", text=f"Error: {str(e)}", 
                                     values=("--", "--", "--", "--"))
    
    def export_accuracy_data(self):
        """Export accuracy data to CSV"""
        try:
            if not hasattr(self, 'accuracy_tracker'):
                self.refresh_accuracy_data()
                return
            
            # Export data
            csv_path = self.accuracy_tracker.export_dashboard_data(format='csv')
            
            if csv_path:
                result = messagebox.askyesno("Export Successful", 
                                           f"Accuracy data exported to:\n{csv_path}\n\nOpen file location?")
                if result:
                    import subprocess
                    subprocess.run(['explorer', '/select,', csv_path])
            else:
                messagebox.showwarning("Export Failed", "No data available to export")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data:\n{str(e)}")

    def _on_summary_link_click(self, event):
        """Handle link clicks in the summary display"""
        # Get the tag at the click position
        tags = self.summary_text.tag_names(tk.CURRENT)
        for tag in tags:
            if tag.startswith("link_"):
                # Extract URL from tag
                url = tag.replace("link_", "", 1)
                try:
                    import webbrowser
                    webbrowser.open(url)
                except Exception as e:
                    messagebox.showwarning("Error Opening Link", f"Could not open URL: {url}\n\nError: {str(e)}")
                break
    
    def get_category_display_names(self):
        return [
            "Required Personal Action",
            "Team Action", 
            "Optional Action", 
            "Job Listing",
            "Optional Event",
            "FYI Notice",
            "Newsletter",
            "Work Relevant",
            "Spam To Delete"
        ]
        return [
            "Required Personal Action",
            "Team Action", 
            "Optional Action", 
            "Job Listing",
            "Optional Event",
            "FYI Notice",
            "Newsletter",
            "Work Relevant",
            "Spam To Delete"
        ]
    
    def get_category_internal_name(self, display_name):
        mapping = {
            "Required Personal Action": "required_personal_action",
            "Team Action": "team_action",
            "Optional Action": "optional_action",
            "Job Listing": "job_listing",
            "Optional Event": "optional_event",
            "FYI Notice": "fyi",
            "Newsletter": "newsletter",
            "Work Relevant": "work_relevant",
            "Spam To Delete": "spam_to_delete"
        }
        return mapping.get(display_name, display_name.lower().replace(" ", "_"))
    
    def start_email_processing(self):
        # Get email count
        if self.custom_count_entry.get().strip():
            max_emails = int(self.custom_count_entry.get().strip())
        else:
            max_emails = int(self.email_count_var.get())
        
        # Reset processing state
        self.processing_cancelled = False
        self.start_processing_btn.config(state=tk.DISABLED)
        self.cancel_processing_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.progress_text.config(state=tk.NORMAL)
        self.progress_text.delete(1.0, tk.END)
        self.progress_text.config(state=tk.DISABLED)
        
        self.update_progress(5, "Retrieving conversations...")
        
        conversation_data = self.outlook_manager.get_emails_with_full_conversations(
            days_back=None, max_emails=max_emails)
        
        
        enriched_conversation_data = []
        
        for conversation_id, conv_info in conversation_data:
            emails_with_body = []
            for email in conv_info['emails']:
                body = self.outlook_manager.get_email_body(email)
                emails_with_body.append({
                    'email_object': email,
                    'body': body,
                    'subject': email.Subject,
                    'sender_name': email.SenderName,
                    'received_time': email.ReceivedTime,
                    'entry_id': email.EntryID
                })
            
            if emails_with_body:
                enriched_conv_info = conv_info.copy()
                enriched_conv_info['emails_with_body'] = emails_with_body
                enriched_conv_info['topic'] = conv_info['topic']
                enriched_conv_info['latest_date'] = conv_info['latest_date']
                enriched_conv_info['trigger_subject'] = conv_info['recent_trigger'].Subject
                enriched_conv_info['trigger_sender'] = conv_info['recent_trigger'].SenderName
                enriched_conv_info['trigger_date'] = conv_info['recent_trigger'].ReceivedTime
                
                enriched_conversation_data.append((conversation_id, enriched_conv_info))
        
        conversation_data = enriched_conversation_data
        
        self.update_progress(15, f"Found {len(conversation_data)} conversations. Starting AI analysis...")
        
        # Now start background thread with the retrieved data
        processing_thread = threading.Thread(target=self.process_emails_background, 
                                            args=(conversation_data,), daemon=True)
        processing_thread.start()
    
    def process_emails_background(self, conversation_data):
        self.email_processor._reset_data_storage()
        learning_data = self.ai_processor.load_learning_data()
        
        total_conversations = len(conversation_data)
        self.ai_processor.start_accuracy_session(total_conversations)
        
        for i, (conversation_id, conv_info) in enumerate(conversation_data, 1):
            if self.processing_cancelled:
                return
                
            progress = 25 + (70 * i / total_conversations)
            self.update_progress(progress, f"Processing {i}/{total_conversations}")
            
            self.process_single_conversation(conversation_id, conv_info, i, total_conversations, learning_data)
        
        # Store results
        self.email_suggestions = self.email_processor.get_email_suggestions()
        
        # Apply holistic inbox analysis to refine suggestions
        self.update_progress(95, "Applying holistic intelligence...")
        self.email_suggestions = self._apply_holistic_inbox_analysis(self.email_suggestions)
        
        # Reprocess action items after holistic modifications
        self._reprocess_action_items_after_holistic_changes()
        
        # Synchronize GUI's action_items_data with the updated email processor data
        self.action_items_data = self.email_processor.action_items_data.copy()
        print(f"📊 Final sync complete. Action items categories: {list(self.action_items_data.keys())}")
        
        # Finalize accuracy tracking session
        total_emails_processed = len(self.email_suggestions)
        categories_used = set(suggestion['ai_suggestion'] for suggestion in self.email_suggestions)
        print(f"🎯 FINALIZING ACCURACY SESSION: {total_emails_processed} emails, {len(categories_used)} categories")
        self.ai_processor.finalize_accuracy_session(
            success_count=total_emails_processed, 
            error_count=0, 
            categories_used=categories_used
        )
        print("✅ Accuracy session finalized!")
        
        self.update_progress(100, "Processing complete")
        self.root.after(0, self.on_processing_complete)
        self.root.after(0, self.reset_processing_ui)
    
    def process_single_conversation(self, conversation_id, conv_info, index, total, learning_data):
        emails_with_body = conv_info.get('emails_with_body', [])
        if not emails_with_body:
            return
        
        # Choose representative email from enriched data (most recent)
        representative_email_data = emails_with_body[0]
        
        # Create email content dict using pre-extracted data
        email_content = {
            'subject': representative_email_data['subject'],
            'sender': representative_email_data['sender_name'],
            'body': representative_email_data['body'],
            'received_time': representative_email_data['received_time']
        }
        
        # Add thread context if needed
        thread_count = len(emails_with_body)
        if thread_count > 1:
            thread_context = self._build_thread_context_from_enriched_data(emails_with_body, representative_email_data)
            email_content['body'] += f"\n\n--- CONVERSATION THREAD CONTEXT ---\n{thread_context}"
        
        # Generate AI summary and classify
        ai_summary = self.ai_processor.generate_email_summary(email_content)
        initial_suggestion = self.ai_processor.classify_email(email_content, learning_data)
        
        # Apply intelligent post-processing based on thread context and content
        final_suggestion, processing_notes = self._apply_intelligent_processing(
            initial_suggestion, email_content, thread_context if thread_count > 1 else "", 
            emails_with_body, representative_email_data
        )
        
        # Store email suggestion with enhanced data
        email_suggestion = {
            'email_data': representative_email_data,
            'email_object': representative_email_data['email_object'],
            'ai_suggestion': final_suggestion,
            'ai_summary': ai_summary,
            'initial_classification': initial_suggestion,  # Track original classification
            'processing_notes': processing_notes,  # Track why it was reclassified or marked for deletion
            'thread_data': {
                'conversation_id': conversation_id,
                'thread_count': thread_count,
                'all_emails_data': emails_with_body,
                'all_emails': [email_data['email_object'] for email_data in emails_with_body],
                'participants': list(set(email_data['sender_name'] for email_data in emails_with_body)),
                'latest_date': conv_info.get('latest_date'),
                'topic': conv_info.get('topic')
            }
        }
        
        self.email_processor.email_suggestions.append(email_suggestion)
        
        # Process by category using pre-extracted data (no COM access)
        self._process_email_by_category_with_enriched_data(representative_email_data, email_suggestion['thread_data'], final_suggestion)
    
    def _apply_intelligent_processing(self, initial_classification, email_content, thread_context, emails_with_body, representative_email_data):
        """Apply intelligent post-processing to refine classifications"""
        processing_notes = []
        final_classification = initial_classification
        
        # 1. Check if team action has been resolved by someone else in the thread
        if initial_classification == 'team_action' and thread_context:
            is_resolved, resolution_details = self.ai_processor.detect_resolved_team_action(email_content, thread_context)
            if is_resolved:
                final_classification = 'fyi'
                processing_notes.append(f"Team action reclassified as FYI: {resolution_details}")
                print(f"🔄 Intelligent Reclassification: Team action → FYI")
                print(f"   Reason: {resolution_details}")
        
        # 2. Check if optional items have passed their deadline and should be deleted
        if initial_classification in ['optional_action', 'optional_event']:
            # First get action details to check for deadline info
            try:
                context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}"
                action_details = self.ai_processor.extract_action_item_details(email_content, context)
            except:
                action_details = {}
            
            is_expired, deadline_details = self.ai_processor.check_optional_item_deadline(email_content, action_details)
            if is_expired:
                final_classification = 'spam_to_delete'
                processing_notes.append(f"Optional item marked for deletion: {deadline_details}")
                print(f"🗑️ Intelligent Cleanup: {initial_classification} → Delete")
                print(f"   Reason: {deadline_details}")
        
        # 3. Future: Add more intelligent processing rules here
        # - Check for duplicate requests
        # - Detect if personal actions were delegated to others
        # - Identify newsletters that are no longer relevant
        
        return final_classification, processing_notes
    
    def _build_thread_context_from_enriched_data(self, emails_with_body, representative_email_data):
        thread_context = []
        for email_data in emails_with_body:
            if email_data['entry_id'] == representative_email_data['entry_id']:
                continue
                
            context_entry = (f"From: {email_data['sender_name']}\n"
                           f"Date: {email_data['received_time'].strftime('%Y-%m-%d %H:%M')}\n"
                           f"Subject: {email_data['subject']}\n"
                           f"Content: {email_data['body'][:500]}{'...' if len(email_data['body']) > 500 else ''}")
            thread_context.append(context_entry)
        
        return "\n\n".join(thread_context)
    
    def _apply_holistic_inbox_analysis(self, all_email_suggestions):
        """Apply holistic analysis to refine the entire inbox processing"""
        try:
            print("🧠 Performing holistic inbox analysis...")
            
            # Extract email data for holistic analysis
            email_data_list = []
            email_lookup = {}
            
            for suggestion in all_email_suggestions:
                email_data = suggestion['email_data']
                email_data_list.append(email_data)
                email_lookup[email_data.get('entry_id', str(len(email_lookup)))] = suggestion
            
            # Perform holistic analysis
            analysis, analysis_notes = self.ai_processor.analyze_inbox_holistically(email_data_list)
            
            if not analysis:
                print(f"⚠️ Holistic analysis failed: {analysis_notes}")
                return all_email_suggestions
            
            print(f"✅ Holistic analysis completed: {analysis_notes}")
            
            # Apply analysis results
            modified_suggestions = self._apply_holistic_modifications(all_email_suggestions, analysis, email_lookup)
            
            return modified_suggestions
            
        except Exception as e:
            print(f"⚠️ Holistic analysis error: {e}")
            return all_email_suggestions
    
    def _reprocess_action_items_after_holistic_changes(self):
        """Reprocess action items data to reflect holistic analysis changes"""
        print("🔄 Synchronizing action items after holistic analysis...")
        
        # Create a mapping of email suggestions by EntryID for quick lookup
        suggestion_lookup = {}
        for suggestion in self.email_suggestions:
            entry_id = suggestion.get('email_data', {}).get('entry_id')
            if entry_id:
                suggestion_lookup[entry_id] = suggestion
        
        # Get the current action items from email processor
        current_action_items = self.email_processor.get_action_items_data()
        changes_made = 0
        
        # For each category in action items, check if any emails have been reclassified by holistic analysis
        for category, items in current_action_items.items():
            items_to_remove = []
            items_to_add = []
            
            for i, item in enumerate(items):
                # Try to find the corresponding email suggestion using thread data
                thread_data = item.get('thread_data', {})
                entry_id = thread_data.get('entry_id')
                
                if entry_id and entry_id in suggestion_lookup:
                    suggestion = suggestion_lookup[entry_id]
                    new_category = suggestion['ai_suggestion']
                    
                    # If the category changed due to holistic analysis
                    if new_category != category:
                        items_to_remove.append(i)
                        changes_made += 1
                        print(f"  🔄 Moving item from '{category}' to '{new_category}': {item.get('email_subject', 'Unknown')[:50]}")
                        
                        # Create new item for the new category
                        if new_category not in current_action_items:
                            current_action_items[new_category] = []
                        
                        # Update the item's category reference and add to new category
                        new_item = item.copy()
                        items_to_add.append((new_category, new_item))
            
            # Remove items that were reclassified (in reverse order to maintain indices)
            for i in reversed(items_to_remove):
                items.pop(i)
            
            # Add items to their new categories
            for new_category, new_item in items_to_add:
                current_action_items[new_category].append(new_item)
        
        # Update the email processor with the modified action items data
        self.email_processor.action_items_data = current_action_items
        print(f"✅ Holistic synchronization complete: {changes_made} items moved")
    
    def _apply_holistic_modifications(self, all_email_suggestions, analysis, email_lookup):
        """Apply the holistic analysis results to modify email suggestions"""
        modified_suggestions = all_email_suggestions.copy()
        holistic_notes = []
        
        # 1. Handle superseded actions
        for superseded in analysis.get('superseded_actions', []):
            original_id = superseded.get('original_email_id')
            reason = superseded.get('reason', 'Superseded by newer information')
            
            if original_id in email_lookup:
                suggestion = email_lookup[original_id]
                suggestion['ai_suggestion'] = 'fyi'  # Downgrade to FYI
                suggestion['holistic_notes'] = suggestion.get('holistic_notes', [])
                suggestion['holistic_notes'].append(f"Superseded: {reason}")
                holistic_notes.append(f"Email '{suggestion['email_data'].get('subject', 'Unknown')[:50]}' superseded")
        
        # 2. Handle expired items
        for expired in analysis.get('expired_items', []):
            email_id = expired.get('email_id')
            reason = expired.get('reason', 'Past deadline or event occurred')
            
            if email_id in email_lookup:
                suggestion = email_lookup[email_id]
                suggestion['ai_suggestion'] = 'spam_to_delete'  # Mark for deletion
                suggestion['holistic_notes'] = suggestion.get('holistic_notes', [])
                suggestion['holistic_notes'].append(f"Expired: {reason}")
                holistic_notes.append(f"Email '{suggestion['email_data'].get('subject', 'Unknown')[:50]}' marked for deletion")
        
        # 3. Handle duplicate groups
        for dup_group in analysis.get('duplicate_groups', []):
            keep_id = dup_group.get('keep_email_id')
            archive_ids = dup_group.get('archive_email_ids', [])
            topic = dup_group.get('topic', 'Similar topic')
            
            for archive_id in archive_ids:
                if archive_id in email_lookup and archive_id != keep_id:
                    suggestion = email_lookup[archive_id]
                    suggestion['ai_suggestion'] = 'fyi'  # Downgrade duplicates
                    suggestion['holistic_notes'] = suggestion.get('holistic_notes', [])
                    suggestion['holistic_notes'].append(f"Duplicate of {topic}")
                    holistic_notes.append(f"Duplicate email archived: {topic}")
        
        # 4. Update priority based on truly relevant actions
        for relevant_action in analysis.get('truly_relevant_actions', []):
            canonical_id = relevant_action.get('canonical_email_id')
            priority = relevant_action.get('priority', 'medium')
            why_relevant = relevant_action.get('why_relevant', '')
            
            if canonical_id in email_lookup:
                suggestion = email_lookup[canonical_id]
                suggestion['holistic_priority'] = priority
                suggestion['holistic_notes'] = suggestion.get('holistic_notes', [])
                suggestion['holistic_notes'].append(f"Priority: {priority} - {why_relevant}")
        
        # Log holistic modifications
        if holistic_notes:
            print("🧠 Holistic Intelligence Applied:")
            for note in holistic_notes[:5]:  # Show first 5 modifications
                print(f"   • {note}")
            if len(holistic_notes) > 5:
                print(f"   • ... and {len(holistic_notes) - 5} more modifications")
        
        return modified_suggestions
    
    def _process_email_by_category_with_enriched_data(self, email_data, thread_data, category):
        if not hasattr(self.email_processor, 'action_items_data'):
            self.email_processor.action_items_data = {}
        if category not in self.email_processor.action_items_data:
            self.email_processor.action_items_data[category] = []
            
        email_content = {
            'subject': email_data['subject'],
            'sender': email_data['sender_name'],
            'body': email_data['body'],
            'received_time': email_data['received_time']
        }
        
        if category in ['required_personal_action', 'optional_action', 'team_action']:
            context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}"
            action_details = self.ai_processor.extract_action_item_details(email_content, context)
            
            action_item = {
                'action': action_details.get('action_required', 'Review email'),
                'thread_data': thread_data,
                'email_subject': email_data['subject'],
                'email_sender': email_data['sender_name'],
                'email_date': email_data['received_time'],
                'action_details': action_details
            }
            self.email_processor.action_items_data[category].append(action_item)
            
        elif category == 'optional_event':
            relevance = self.ai_processor.assess_event_relevance(
                email_data['subject'], email_data['body'], self.ai_processor.get_job_context())
            
            event_item = {
                'relevance': relevance,
                'thread_data': thread_data,
                'email_subject': email_data['subject'],
                'email_sender': email_data['sender_name'],
                'email_date': email_data['received_time']
            }
            self.email_processor.action_items_data[category].append(event_item)
        
        elif category == 'fyi':
            context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}"
            fyi_summary = self.ai_processor.generate_fyi_summary(email_content, context)
            
            fyi_item = {
                'summary': fyi_summary,
                'thread_data': thread_data,
                'email_subject': email_data['subject'],
                'email_sender': email_data['sender_name'],
                'email_date': email_data['received_time']
            }
            self.email_processor.action_items_data[category].append(fyi_item)
            
        elif category == 'newsletter':
            context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}"
            newsletter_summary = self.ai_processor.generate_newsletter_summary(email_content, context)
            
            newsletter_item = {
                'summary': newsletter_summary,
                'thread_data': thread_data,
                'email_subject': email_data['subject'],
                'email_sender': email_data['sender_name'],
                'email_date': email_data['received_time']
            }
            self.email_processor.action_items_data[category].append(newsletter_item)
    
    def update_progress(self, value, message):
        def update_ui():
            self.progress_var.set(value)
            self.status_var.set(message)
        self.root.after(0, update_ui)
    
    def update_progress_text(self, message):
        def update_ui():
            self.progress_text.config(state=tk.NORMAL)
            self.progress_text.insert(tk.END, message + "\n")
            self.progress_text.see(tk.END)
            self.progress_text.config(state=tk.DISABLED)
        self.root.after(0, update_ui)
    
    def cancel_processing(self):
        self.processing_cancelled = True
    
    def reset_processing_ui(self):
        self.cancel_processing_btn.config(state=tk.DISABLED)
    
    def on_processing_complete(self):
        self.notebook.tab(1, state="normal")
        self.notebook.tab(3, state="normal")  # Enable accuracy dashboard tab
        self.load_processed_emails()
        self.notebook.select(1)
        
        # Automatically select and display the first email for faster review
        self.root.after(100, self._auto_select_first_email)
    
    def _auto_select_first_email(self):
        """Automatically select the first email when review pane opens"""
        children = self.email_tree.get_children()
        if children:
            # Select the first item
            first_item = children[0]
            self.email_tree.selection_set(first_item)
            self.email_tree.focus(first_item)
            # Display its details
            self.display_email_details(0)
        
    def load_processed_emails(self):
        """Load processed emails into the tree view"""
        self.refresh_email_tree()
    
    def sort_by_column(self, col):
        """Sort the email tree by the specified column"""
        if not hasattr(self, 'email_suggestions') or not self.email_suggestions:
            return
        
        # Toggle sort direction if clicking the same column
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
            self.sort_reverse = False
        
        # Update column header to show sort direction
        for column in ('Subject', 'From', 'Category', 'AI Summary', 'Date'):
            if column == col:
                direction = " ↓" if self.sort_reverse else " ↑"
                self.email_tree.heading(column, text=f"{column}{direction}")
            else:
                self.email_tree.heading(column, text=column)
        
        # Create list of (index, sort_value) pairs
        items_with_sort_keys = []
        for i, suggestion in enumerate(self.email_suggestions):
            email_data = suggestion['email_data']
            
            if col == 'Subject':
                sort_key = email_data.get('subject', '').lower()
            elif col == 'From':
                sort_key = email_data.get('sender_name', email_data.get('sender', '')).lower()
            elif col == 'Category':
                # Sort by category priority: required_personal_action, team_action, etc.
                category_priority = {
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
                sort_key = category_priority.get(suggestion.get('ai_suggestion', ''), 99)
            elif col == 'AI Summary':
                sort_key = suggestion.get('ai_summary', '').lower()
            elif col == 'Date':
                # Sort by date (most recent first when not reversed)
                received_time = email_data.get('received_time')
                if hasattr(received_time, 'timestamp'):
                    sort_key = received_time.timestamp()
                else:
                    sort_key = 0
            else:
                sort_key = ''
            
            items_with_sort_keys.append((i, sort_key))
        
        # Sort the items
        items_with_sort_keys.sort(key=lambda x: x[1], reverse=self.sort_reverse)
        
        # Reorder the email_suggestions list and refresh the tree
        self.email_suggestions = [self.email_suggestions[i] for i, _ in items_with_sort_keys]
        self.refresh_email_tree()
        
        print(f"📊 Sorted by {col} ({'descending' if self.sort_reverse else 'ascending'})")
    
    def refresh_email_tree(self):
        """Refresh the email tree view with current email_suggestions order"""
        # Clear existing items
        for item in self.email_tree.get_children():
            self.email_tree.delete(item)
        
        # Repopulate with sorted data
        for i, suggestion_data in enumerate(self.email_suggestions):
            email_data = suggestion_data.get('email_data', {})
            suggestion = suggestion_data['ai_suggestion']
            initial_classification = suggestion_data.get('initial_classification', suggestion)
            processing_notes = suggestion_data.get('processing_notes', [])
            ai_summary = suggestion_data.get('ai_summary', 'No summary')
            thread_data = suggestion_data.get('thread_data', {})
            thread_count = thread_data.get('thread_count', 1)
            
            # Add processing note indicator to summary if reclassified
            if processing_notes:
                ai_summary = f"🔄 {ai_summary} | {'; '.join(processing_notes[:1])}"  # Show first note
            
            # Handle thread data
            if thread_count > 1:
                participants = thread_data.get('participants', [email_data.get('sender_name', 'Unknown')])
                subject = f"🧵 {thread_data.get('topic', email_data.get('subject', 'Unknown'))} ({thread_count} emails)"
                sender = f"{len(participants)} participants"
            else:
                subject = email_data.get('subject', 'Unknown Subject')
                sender = email_data.get('sender_name', email_data.get('sender', 'Unknown Sender'))
            
            # Format date
            received_time = email_data.get('received_time', 'Unknown Date')
            if hasattr(received_time, 'strftime'):
                date_str = received_time.strftime('%m-%d %H:%M')
            else:
                date_str = str(received_time)[:10] if received_time != 'Unknown Date' else 'Unknown'
            
            # Show both original and final classification if different
            category = suggestion.replace('_', ' ').title()
            if initial_classification != suggestion:
                category = f"{category} (was {initial_classification.replace('_', ' ').title()})"
            
            # Add priority indicator for holistic insights
            holistic_priority = suggestion_data.get('holistic_priority', None)
            if holistic_priority == 'high':
                subject = f"🔴 {subject}"
            elif holistic_priority == 'medium':
                subject = f"🟡 {subject}"
            
            # Truncate long text for better display (but preserve thread indicators)
            if not subject.startswith('🧵'):  # Don't truncate thread subjects
                subject = subject[:47] + "..." if len(subject) > 50 else subject
            if not sender.endswith('participants'):  # Don't truncate participant counts
                sender = sender[:22] + "..." if len(sender) > 25 else sender
            ai_summary = ai_summary[:47] + "..." if len(ai_summary) > 50 else ai_summary
            
            self.email_tree.insert('', 'end', values=(subject, sender, category, ai_summary, date_str))

    def on_email_select(self, event):
        # Auto-apply any pending changes before switching
        self._auto_apply_pending_changes()
        
        selection = self.email_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        index = None
        for i, child in enumerate(self.email_tree.get_children()):
            if child == item:
                index = i
                break
        
        if index is not None and index < len(self.email_suggestions):
            self.display_email_details(index)
    
    def _auto_apply_pending_changes(self):
        """Automatically apply any pending category changes when switching emails"""
        if (self.current_email_index is not None and 
            hasattr(self, 'category_var') and hasattr(self, 'original_category')):
            
            current_category = self.get_category_internal_name(self.category_var.get())
            if current_category != self.original_category:
                # Get explanation if provided, otherwise use default
                explanation = self.explanation_var.get().strip()
                if not explanation:
                    explanation = "Category changed without explanation"
                
                # Apply the change silently
                self.edit_suggestion(self.current_email_index, current_category, explanation)
                
                # Update UI to reflect the change was applied
                self.apply_btn.config(state=tk.DISABLED)
                self.load_processed_emails()  # Refresh list to show updated category
    
    def display_email_details(self, index):
        self.current_email_index = index
        suggestion_data = self.email_suggestions[index]
        email_data = suggestion_data.get('email_data', {})
        suggestion = suggestion_data['ai_suggestion']
        initial_classification = suggestion_data.get('initial_classification', suggestion)
        processing_notes = suggestion_data.get('processing_notes', [])
        ai_summary = suggestion_data.get('ai_summary', 'No summary available')
        
        # Update preview with AI summary first, then email body
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        
        # Configure text tags for better formatting
        self._configure_text_tags()
        
        # Add AI Summary section at the top for faster review
        self.preview_text.insert(tk.END, "🤖 AI SUMMARY:\n", "header")
        self.preview_text.insert(tk.END, f"{ai_summary}\n\n", "summary")
        
        # Show intelligent processing notes if any
        if processing_notes:
            self.preview_text.insert(tk.END, "🧠 INTELLIGENT PROCESSING:\n", "header")
            if initial_classification != suggestion:
                self.preview_text.insert(tk.END, f"Reclassified: {initial_classification} → {suggestion}\n", "metadata")
            for note in processing_notes:
                self.preview_text.insert(tk.END, f"• {note}\n", "metadata")
            self.preview_text.insert(tk.END, "\n", "summary")
        
        # Show holistic insights if available
        holistic_notes = suggestion_data.get('holistic_notes', [])
        holistic_priority = suggestion_data.get('holistic_priority', None)
        if holistic_notes or holistic_priority:
            self.preview_text.insert(tk.END, "🌐 HOLISTIC INSIGHTS:\n", "header")
            if holistic_priority:
                priority_color = {"high": "error", "medium": "warning", "low": "metadata"}.get(holistic_priority, "metadata")
                self.preview_text.insert(tk.END, f"Priority: {holistic_priority.upper()}\n", priority_color)
            for note in holistic_notes:
                self.preview_text.insert(tk.END, f"• {note}\n", "metadata")
            self.preview_text.insert(tk.END, "\n", "summary")
        
        self.preview_text.insert(tk.END, "=" * 50 + "\n", "separator")
        self.preview_text.insert(tk.END, "📧 EMAIL CONTENT:\n\n", "header")
        
        # Process and add email body with clickable links
        body = email_data.get('body', 'No content available')
        self._insert_formatted_email_body(body)
        
        self.preview_text.config(state=tk.DISABLED)
        
        # Update category dropdown
        self.category_var.set(suggestion.replace('_', ' ').title())
        self.original_category = suggestion
        
        # Clear explanation and disable apply button
        self.explanation_var.set("")
        self.apply_btn.config(state=tk.DISABLED)
    
    def _configure_text_tags(self):
        """Configure text formatting tags for better email display"""
        # Header style for section titles
        self.preview_text.tag_configure("header", 
                                       font=("Arial", 10, "bold"), 
                                       foreground="#2c3e50")
        
        # Summary style with light background
        self.preview_text.tag_configure("summary", 
                                       font=("Arial", 9), 
                                       background="#f8f9fa",
                                       foreground="#2c3e50")
        
        # Separator line
        self.preview_text.tag_configure("separator", 
                                       font=("Courier", 8), 
                                       foreground="#bdc3c7")
        
        # Clickable link style
        self.preview_text.tag_configure("link", 
                                       font=("Arial", 9, "underline"), 
                                       foreground="#3498db",
                                       background="#ecf0f1")
        
        # Email metadata style
        self.preview_text.tag_configure("metadata", 
                                       font=("Arial", 8, "italic"), 
                                       foreground="#7f8c8d")
        
        # Normal body text
        self.preview_text.tag_configure("body", 
                                       font=("Arial", 9), 
                                       foreground="#2c3e50")
        
        # Priority colors for holistic insights
        self.preview_text.tag_configure("error", 
                                       font=("Arial", 9, "bold"), 
                                       foreground="#e74c3c")
        
        self.preview_text.tag_configure("warning", 
                                       font=("Arial", 9, "bold"), 
                                       foreground="#f39c12")
        
        # Configure link click behavior
        self.preview_text.tag_bind("link", "<Button-1>", self._on_link_click)
        self.preview_text.tag_bind("link", "<Enter>", lambda e: self.preview_text.config(cursor="hand2"))
        self.preview_text.tag_bind("link", "<Leave>", lambda e: self.preview_text.config(cursor=""))
    
    def _insert_formatted_email_body(self, body):
        """Insert email body with clickable links and better formatting"""
        # Increase body length limit significantly for better context
        if len(body) > 10000:
            body = body[:10000] + "\n\n[... content truncated for readability ...]"
        
        # Clean up common email formatting issues
        body = self._clean_email_formatting(body)
        
        # Find all URLs in the text
        url_pattern = r'http[s]?://[^\s<>"\'\[\](){}|\\^`]+'
        urls = []
        
        # Store URLs and their positions
        for match in re.finditer(url_pattern, body):
            urls.append({
                'start': match.start(),
                'end': match.end(),
                'url': match.group(),
                'display_url': self._create_display_url(match.group())
            })
        
        # Insert text with clickable links
        last_pos = 0
        for url_info in urls:
            # Insert text before the URL
            text_before = body[last_pos:url_info['start']]
            self.preview_text.insert(tk.END, text_before, "body")
            
            # Insert clickable URL
            link_start = self.preview_text.index(tk.END)
            self.preview_text.insert(tk.END, url_info['display_url'], "link")
            link_end = self.preview_text.index(tk.END)
            
            # Store the actual URL for click handling
            self.preview_text.tag_add(f"url_{url_info['start']}", link_start, link_end)
            self.preview_text.tag_configure(f"url_{url_info['start']}", 
                                          foreground="#3498db", 
                                          underline=True)
            self.preview_text.tag_bind(f"url_{url_info['start']}", "<Button-1>", 
                                     lambda e, url=url_info['url']: self._open_url(url))
            
            last_pos = url_info['end']
        
        # Insert remaining text
        remaining_text = body[last_pos:]
        self.preview_text.insert(tk.END, remaining_text, "body")
    
    def _clean_email_formatting(self, body):
        """Clean up common email formatting issues for better readability"""
        # Remove excessive blank lines
        body = re.sub(r'\n{3,}', '\n\n', body)
        
        # Clean up outlook-style forwarded/reply headers
        body = re.sub(r'_{10,}', '\n' + '─' * 40 + '\n', body)
        
        # Clean up common email signatures separators
        body = re.sub(r'-{5,}', '─' * 25, body)
        
        # Remove excessive spaces while preserving intentional formatting
        lines = body.split('\n')
        cleaned_lines = []
        for line in lines:
            # Clean up excessive spaces but preserve indentation
            cleaned_line = re.sub(r'[ \t]{2,}', ' ', line.rstrip())
            cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)
    
    def _create_display_url(self, url):
        """Create a more readable display version of the URL"""
        # Truncate very long URLs for better readability
        if len(url) > 60:
            # Try to show meaningful part of URL
            from urllib.parse import urlparse
            try:
                parsed = urlparse(url)
                domain = parsed.netloc
                path = parsed.path[:30] + '...' if len(parsed.path) > 30 else parsed.path
                return f"{domain}{path}"
            except:
                # Fallback: simple truncation
                return url[:50] + "..."
        return url
    
    def _on_link_click(self, event):
        """Handle link clicks in the text widget"""
        # Get the tag at the click position
        tags = self.preview_text.tag_names(tk.CURRENT)
        for tag in tags:
            if tag.startswith("url_"):
                # This will be handled by the specific URL tag binding
                break
    
    def _open_url(self, url):
        """Open URL in default browser"""
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception as e:
            messagebox.showwarning("Error Opening Link", f"Could not open URL: {url}\n\nError: {str(e)}")
    
    def on_category_change(self, event):
        if self.current_email_index is not None:
            current_category = self.get_category_internal_name(self.category_var.get())
            if current_category != self.original_category:
                # Immediately apply the change when category is changed
                explanation = self.explanation_var.get().strip()
                if not explanation:
                    explanation = "Category changed via dropdown"
                
                self.edit_suggestion(self.current_email_index, current_category, explanation)
                self.original_category = current_category
                
                # Clear explanation field and disable apply button since change is already applied
                self.explanation_var.set("")
                self.apply_btn.config(state=tk.DISABLED)
                
                # Refresh the tree to show the updated category
                self.refresh_email_tree()
            else:
                self.apply_btn.config(state=tk.DISABLED)
    
    def apply_category_change(self):
        if self.current_email_index is None:
            return
        
        new_display_category = self.category_var.get()
        new_category = self.get_category_internal_name(new_display_category)
        explanation = self.explanation_var.get().strip()
        
        # Make explanation optional - use default if empty
        if not explanation:
            explanation = "Manual category change applied"
        
        # Apply the change
        self.edit_suggestion(self.current_email_index, new_category, explanation)
        
        # Update UI
        self.apply_btn.config(state=tk.DISABLED)
        self.explanation_var.set("")
        self.load_processed_emails()  # Refresh list
        
    def edit_suggestion(self, email_index, new_category, user_explanation):
        if email_index >= len(self.email_suggestions):
            return
        
        suggestion_data = self.email_suggestions[email_index]
        old_category = suggestion_data['ai_suggestion']
        
        # Update the suggestion
        suggestion_data['ai_suggestion'] = new_category
        
        # Update the action_items_data to reflect the reclassification
        self._update_action_items_for_reclassification(suggestion_data, old_category, new_category)
        
        # Record the change for accuracy tracking
        email_data = suggestion_data.get('email_data', {})
        email_info = {
            'subject': email_data.get('subject', 'Unknown'),
            'sender': email_data.get('sender_name', 'Unknown'),
            'date': email_data.get('received_time', 'Unknown'),
            'body': email_data.get('body', '')[:500]
        }
        self.ai_processor.record_suggestion_modification(email_info, old_category, new_category, user_explanation)
    
    def _update_action_items_for_reclassification(self, suggestion_data, old_category, new_category):
        """Update email suggestions when an email is reclassified (lightweight, deferred processing)"""
        email_data = suggestion_data.get('email_data', {})
        
        print(f"🔄 Reclassifying email '{email_data.get('subject', 'Unknown')[:50]}' from '{old_category}' to '{new_category}'")
        
        # Just update the suggestion data - detailed processing will happen later
        # Find and update the corresponding email suggestion
        for suggestion in self.email_suggestions:
            suggestion_email_data = suggestion.get('thread_data', {})
            if (suggestion_email_data.get('topic', '') == email_data.get('subject', '') or
                suggestion.get('email_object', {}) and 
                getattr(suggestion['email_object'], 'Subject', '') == email_data.get('subject', '')):
                
                # Update the AI suggestion to the new category
                suggestion['ai_suggestion'] = new_category
                suggestion['explanation'] = f"Manually reclassified as {new_category.replace('_', ' ')} from {old_category.replace('_', ' ')}."
                
                print(f"✅ Updated suggestion data for deferred processing")
                break
        
        # Clear old action items data - it will be regenerated during deferred processing
        # This prevents inconsistent state between review and final processing
        if old_category in self.action_items_data:
            # Find and remove the item with matching email data
            items_to_remove = []
            for i, item in enumerate(self.action_items_data[old_category]):
                if (item.get('email_subject') == email_data.get('subject') and 
                    item.get('email_sender') == email_data.get('sender_name')):
                    items_to_remove.append(i)
            
            # Remove items in reverse order to maintain indices
            for i in reversed(items_to_remove):
                self.action_items_data[old_category].pop(i)
    
    def apply_to_outlook(self):
        # Auto-apply any pending changes before applying to Outlook
        self._auto_apply_pending_changes()
        
        if not self.email_suggestions:
            messagebox.showwarning("No Data", "No email suggestions to apply.")
            return
        
        # NOW perform detailed AI analysis on finalized classifications
        print("\n🚀 Starting detailed processing of finalized email classifications...")
        try:
            self.action_items_data = self.email_processor.process_detailed_analysis(self.email_suggestions)
            print("✅ Detailed processing completed successfully")
        except Exception as e:
            print(f"❌ Error during detailed processing: {e}")
            messagebox.showerror("Processing Error", f"Failed to complete detailed analysis: {e}")
            return
        
        # Calculate folder distribution for user preview
        inbox_categories = {'required_personal_action', 'optional_action', 'job_listing', 'work_relevant'}
        non_inbox_categories = {'team_action', 'optional_event', 'fyi', 'newsletter', 'general_information', 'spam_to_delete'}
        
        # Make counting case-insensitive to handle FYI vs fyi
        inbox_count = sum(1 for s in self.email_suggestions if s['ai_suggestion'].lower() in inbox_categories)
        non_inbox_count = sum(1 for s in self.email_suggestions if s['ai_suggestion'].lower() in non_inbox_categories)
        
        def confirmation_callback(email_count):
            message = f"""Apply categorization to {email_count} emails in Outlook?

📂 FOLDER ORGANIZATION:
🎯 INBOX (Actionable): {inbox_count} emails
   • Required Actions, Optional Actions, Job Listings, Work Relevant
   
📚 OUTSIDE INBOX (Reference): {non_inbox_count} emails  
   • Team Actions, Optional Events, FYI, Newsletters

This will help keep your inbox focused on actionable items only."""
            
            return messagebox.askyesno("Confirm Application", message)
        
        success_count, error_count = self.outlook_manager.apply_categorization_batch(
            self.email_suggestions, 
            confirmation_callback
        )
        
        # Record all accepted suggestions for fine-tuning data (both modified and unmodified)
        if success_count > 0:
            self.ai_processor.record_accepted_suggestions(self.email_suggestions)
        
        messagebox.showinfo("Complete", 
                          f"Categorization applied!\n\n"
                          f"✅ Successfully processed: {success_count}\n"
                          f"🎯 Inbox (actionable): {inbox_count} emails\n"
                          f"📚 Outside inbox (reference): {non_inbox_count} emails\n"
                          f"❌ Errors: {error_count}")
    
    def proceed_to_summary(self):
        self.notebook.tab(2, state="normal")
        self.notebook.select(2)
        # Automatically generate and display the formatted summary
        self.root.after(100, self.generate_summary)
    
    def open_accuracy_dashboard(self):
        """Enable and open the accuracy dashboard tab"""
        self.notebook.tab(3, state="normal")
        self.notebook.select(3)
        # Refresh the accuracy data when opening
        self.root.after(100, self.refresh_accuracy_data)
    
    def generate_summary(self):
        self.generate_summary_btn.config(state=tk.DISABLED)
        
        # Ensure detailed processing is completed before generating summary
        if self.email_suggestions and not self.action_items_data.get('required_personal_action') and not self.action_items_data.get('fyi'):
            print("\n🔍 Performing detailed processing for summary generation...")
            try:
                self.action_items_data = self.email_processor.process_detailed_analysis(self.email_suggestions)
                print("✅ Detailed processing completed for summary")
            except Exception as e:
                print(f"❌ Error during detailed processing: {e}")
                messagebox.showerror("Processing Error", f"Failed to complete detailed analysis: {e}")
                self.generate_summary_btn.config(state=tk.NORMAL)
                return
        
        # Generate summary sections from current batch
        current_batch_sections = self.summary_generator.build_summary_sections(self.action_items_data)
        
        # Get comprehensive summary that includes previous outstanding tasks
        self.summary_sections = self.task_persistence.get_comprehensive_summary(current_batch_sections)
        
        # Save current batch tasks to persistent storage
        batch_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.task_persistence.save_outstanding_tasks(current_batch_sections, batch_timestamp)
        
        # Display beautifully formatted comprehensive summary in the app
        self.display_formatted_summary_in_app(self.summary_sections)
        
        # Also save HTML summary for browser viewing (keep existing functionality)
        self.saved_summary_path = self.summary_generator.save_focused_summary(self.summary_sections, batch_timestamp)
        
        self.generate_summary_btn.config(state=tk.NORMAL)
    
    def display_formatted_summary_in_app(self, summary_sections):
        """Display beautifully formatted summary directly in the application"""
        # Clear existing content
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        
        # Calculate totals including task persistence info
        total_items = sum(len(items) for items in summary_sections.values())
        high_priority = len(summary_sections.get('required_actions', []))
        
        # Get task statistics for context
        task_stats = self.task_persistence.get_task_statistics()
        
        # Count items from previous batches (those with batch_count > 1)
        outstanding_from_previous = 0
        new_from_current = 0
        for key, items in summary_sections.items():
            if key in ['required_actions', 'team_actions', 'optional_actions', 'job_listings', 'optional_events']:
                for item in items:
                    batch_count = item.get('batch_count', 1)
                    if batch_count > 1:
                        outstanding_from_previous += 1
                    else:
                        new_from_current += 1
        
        # Header with comprehensive context
        self.summary_text.insert(tk.END, "📊 Comprehensive Email & Task Summary\n", "main_title")
        self.summary_text.insert(tk.END, "Current Batch + Outstanding Tasks\n\n", "subtitle")
        
        # Overview section with task persistence info
        self.summary_text.insert(tk.END, "📊 Summary Overview\n", "overview_title")
        self.summary_text.insert(tk.END, "═" * 60 + "\n", "separator")
        overview_text = f"Total Items: {total_items}    |    High Priority: {high_priority}\n"
        overview_text += f"New from current batch: {new_from_current}    |    "
        overview_text += f"Outstanding from previous: {outstanding_from_previous}\n"
        
        if task_stats['old_tasks_count'] > 0:
            overview_text += f"⚠️ Tasks older than 7 days: {task_stats['old_tasks_count']}\n"
        
        overview_text += "💡 Comprehensive view - all actionable items in one place!\n\n"
        self.summary_text.insert(tk.END, overview_text, "overview_stats")
        
        # Define sections with their styling
        sections_config = [
            ('required_actions', '🔴 REQUIRED ACTION ITEMS (ME)', 'section_required', self._display_action_items),
            ('team_actions', '👥 TEAM ACTION ITEMS', 'section_team', self._display_action_items),
            ('completed_team_actions', '✅ COMPLETED TEAM ACTIONS', 'section_completed', self._display_completed_team_actions),
            ('optional_actions', '📝 OPTIONAL ACTION ITEMS', 'section_optional', self._display_optional_actions),
            ('job_listings', '💼 JOB LISTINGS', 'section_jobs', self._display_job_listings),
            ('optional_events', '🎪 OPTIONAL EVENTS', 'section_events', self._display_events),
            ('fyi_notices', '📋 FYI NOTICES', 'section_fyi', self._display_fyi_notices),
            ('newsletters', '📰 NEWSLETTERS SUMMARY', 'section_newsletter', self._display_newsletters)
        ]
        
        # Display each section
        for section_key, title, style_tag, display_func in sections_config:
            items = summary_sections.get(section_key, [])
            if not items and section_key in ['required_actions', 'team_actions']:
                # Always show critical sections even if empty
                pass
            elif not items:
                # Skip empty optional sections
                continue
            
            # Section header with count
            section_title = f"{title} ({len(items)})\n"
            self.summary_text.insert(tk.END, section_title, style_tag)
            self.summary_text.insert(tk.END, "─" * len(section_title) + "\n", "separator")
            
            if items:
                display_func(items)
            else:
                self.summary_text.insert(tk.END, f"No {title.split()[-1].lower()} found\n\n", "empty_section")
            
            self.summary_text.insert(tk.END, "\n", "content_text")
        
        # Configure text widget to prevent editing but allow tag clicks
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.bind("<Key>", lambda e: "break")  # Prevent typing
        # Note: No longer need click handler since we're using embedded Button widgets
        
        # Scroll to top for better user experience
        self.summary_text.see("1.0")
    
    def _display_action_items(self, items):
        """Display required or team action items with full details"""
        for i, item in enumerate(items, 1):
            # Item title with persistence indicator
            batch_count = item.get('batch_count', 1)
            title_prefix = ""
            if batch_count > 1:
                title_prefix = f"📅 [{batch_count}x] "  # Show how many batches this task has appeared in
            
            self.summary_text.insert(tk.END, f"{i}. {title_prefix}{item['subject']}\n", "item_title")
            
            # Metadata with first seen info
            self.summary_text.insert(tk.END, f"   From: {item['sender']}", "item_meta")
            if item.get('first_seen'):
                try:
                    first_seen = datetime.strptime(item['first_seen'], '%Y-%m-%d %H:%M:%S')
                    days_old = (datetime.now() - first_seen).days
                    if days_old > 0:
                        self.summary_text.insert(tk.END, f"  |  First seen: {days_old} days ago", "item_meta")
                except:
                    pass
            self.summary_text.insert(tk.END, "\n", "item_meta")
            
            # Action details
            self.summary_text.insert(tk.END, "   Due: ", "content_label")
            self.summary_text.insert(tk.END, f"{item.get('due_date', 'No specific deadline')}\n", "content_text")
            
            self.summary_text.insert(tk.END, "   Action: ", "content_label")
            self.summary_text.insert(tk.END, f"{item.get('action_required', 'Review email')}\n", "content_text")
            
            self.summary_text.insert(tk.END, "   Why: ", "content_label")
            self.summary_text.insert(tk.END, f"{item.get('explanation', 'No explanation available')}\n", "content_text")
            
            # Task ID for completion tracking
            if item.get('task_id'):
                self.summary_text.insert(tk.END, "   Task ID: ", "content_label")
                self.summary_text.insert(tk.END, f"{item['task_id']}\n", "item_meta")
            
            # Inline completion button
            if item.get('task_id'):
                self.summary_text.insert(tk.END, "   ", "content_text")
                
                # Create an actual Button widget embedded in the text widget
                complete_button = tk.Button(
                    self.summary_text,
                    text="✅ Mark Done",
                    command=lambda task_id=item['task_id']: self._mark_single_task_complete(task_id),
                    bg="#4CAF50",
                    fg="white",
                    font=("Arial", 8, "bold"),
                    relief="raised",
                    padx=5,
                    pady=2,
                    cursor="hand2"
                )
                
                # Insert the button widget directly into the text widget
                self.summary_text.window_create(tk.END, window=complete_button)
                
                self.summary_text.insert(tk.END, "\n", "content_text")
            
            # Links
            if item.get('links'):
                self.summary_text.insert(tk.END, "   Links: ", "content_label")
                for j, link in enumerate(item['links'][:2]):
                    link_text = f"Link {j+1}"
                    link_start = self.summary_text.index(tk.END)
                    self.summary_text.insert(tk.END, link_text, "link")
                    link_end = self.summary_text.index(tk.END)
                    
                    # Create unique tag for this link
                    link_tag = f"link_{hash(link)}"
                    self.summary_text.tag_add(link_tag, link_start, link_end)
                    self.summary_text.tag_configure(link_tag, foreground="#007acc", underline=True)
                    self.summary_text.tag_bind(link_tag, "<Button-1>", lambda e, url=link: self._open_url(url))
                    
                    if j < min(len(item['links']), 2) - 1:
                        self.summary_text.insert(tk.END, " | ", "content_text")
                self.summary_text.insert(tk.END, "\n", "content_text")
            
            self.summary_text.insert(tk.END, "\n", "content_text")
    
    def _display_completed_team_actions(self, items):
        """Display completed team action items with completion details"""
        for i, item in enumerate(items, 1):
            # Item title with completion indicator
            self.summary_text.insert(tk.END, f"{i}. ✅ {item['subject']}\n", "item_title_completed")
            
            # Metadata
            self.summary_text.insert(tk.END, f"   From: {item['sender']}", "item_meta")
            if item.get('first_seen'):
                try:
                    first_seen = datetime.strptime(item['first_seen'], '%Y-%m-%d %H:%M:%S')
                    days_old = (datetime.now() - first_seen).days
                    if days_old > 0:
                        self.summary_text.insert(tk.END, f"  |  First seen: {days_old} days ago", "item_meta")
                except:
                    pass
            self.summary_text.insert(tk.END, "\n", "item_meta")
            
            # Original action details (for reference)
            self.summary_text.insert(tk.END, "   Original Action: ", "content_label")
            self.summary_text.insert(tk.END, f"{item.get('action_required', 'Review email')}\n", "content_text")
            
            # Completion details
            self.summary_text.insert(tk.END, "   ✅ Status: ", "content_label")
            self.summary_text.insert(tk.END, "COMPLETED\n", "completion_status")
            
            if item.get('completion_note'):
                self.summary_text.insert(tk.END, "   📝 Note: ", "content_label")
                self.summary_text.insert(tk.END, f"{item['completion_note']}\n", "completion_note")
            
            self.summary_text.insert(tk.END, "\n", "content_text")

    def _display_optional_actions(self, items):
        """Display optional action items with relevance context"""
        for i, item in enumerate(items, 1):
            # Item title with persistence indicator
            batch_count = item.get('batch_count', 1)
            title_prefix = ""
            if batch_count > 1:
                title_prefix = f"📅 [{batch_count}x] "
            
            self.summary_text.insert(tk.END, f"{i}. {title_prefix}{item['subject']}\n", "item_title")
            
            # Metadata with first seen info
            self.summary_text.insert(tk.END, f"   From: {item['sender']}", "item_meta")
            if item.get('first_seen'):
                try:
                    first_seen = datetime.strptime(item['first_seen'], '%Y-%m-%d %H:%M:%S')
                    days_old = (datetime.now() - first_seen).days
                    if days_old > 0:
                        self.summary_text.insert(tk.END, f"  |  First seen: {days_old} days ago", "item_meta")
                except:
                    pass
            self.summary_text.insert(tk.END, "\n", "item_meta")
            
            # Optional action details
            self.summary_text.insert(tk.END, "   What: ", "content_label")
            self.summary_text.insert(tk.END, f"{item.get('action_required', 'Provide feedback')}\n", "content_text")
            
            self.summary_text.insert(tk.END, "   Why relevant: ", "content_label")
            self.summary_text.insert(tk.END, f"{item.get('why_relevant', item.get('explanation', 'No specific reason provided'))}\n", "content_text")
            
            self.summary_text.insert(tk.END, "   Context: ", "content_label")
            self.summary_text.insert(tk.END, f"{item.get('explanation', 'No context available')}\n", "content_text")
            
            # Task ID for completion tracking
            if item.get('task_id'):
                self.summary_text.insert(tk.END, "   Task ID: ", "content_label")
                self.summary_text.insert(tk.END, f"{item['task_id']}\n", "item_meta")
            
            # Inline completion button
            if item.get('task_id'):
                self.summary_text.insert(tk.END, "   ", "content_text")
                
                # Create an actual Button widget embedded in the text widget
                complete_button = tk.Button(
                    self.summary_text,
                    text="✅ Mark Done",
                    command=lambda task_id=item['task_id']: self._mark_single_task_complete(task_id),
                    bg="#4CAF50",
                    fg="white",
                    font=("Arial", 8, "bold"),
                    relief="raised",
                    padx=5,
                    pady=2,
                    cursor="hand2"
                )
                
                # Insert the button widget directly into the text widget
                self.summary_text.window_create(tk.END, window=complete_button)
                
                self.summary_text.insert(tk.END, "\n", "content_text")
            
            # Links
            if item.get('links'):
                self.summary_text.insert(tk.END, "   Links: ", "content_label")
                for j, link in enumerate(item['links'][:2]):
                    link_text = f"Link {j+1}"
                    link_start = self.summary_text.index(tk.END)
                    self.summary_text.insert(tk.END, link_text, "link")
                    link_end = self.summary_text.index(tk.END)
                    
                    # Create unique tag for this link
                    link_tag = f"link_{hash(link)}"
                    self.summary_text.tag_add(link_tag, link_start, link_end)
                    self.summary_text.tag_configure(link_tag, foreground="#007acc", underline=True)
                    self.summary_text.tag_bind(link_tag, "<Button-1>", lambda e, url=link: self._open_url(url))
                    
                    if j < min(len(item['links']), 2) - 1:
                        self.summary_text.insert(tk.END, " | ", "content_text")
                self.summary_text.insert(tk.END, "\n", "content_text")
            
            self.summary_text.insert(tk.END, "\n", "content_text")
    
    def _display_job_listings(self, items):
        """Display job listings with qualification match"""
        for i, item in enumerate(items, 1):
            # Item title with persistence indicator
            batch_count = item.get('batch_count', 1)
            title_prefix = ""
            if batch_count > 1:
                title_prefix = f"📅 [{batch_count}x] "
            
            self.summary_text.insert(tk.END, f"{i}. {title_prefix}{item['subject']}\n", "item_title")
            
            # Metadata with first seen info
            self.summary_text.insert(tk.END, f"   From: {item['sender']}", "item_meta")
            if item.get('first_seen'):
                try:
                    first_seen = datetime.strptime(item['first_seen'], '%Y-%m-%d %H:%M:%S')
                    days_old = (datetime.now() - first_seen).days
                    if days_old > 0:
                        self.summary_text.insert(tk.END, f"  |  First seen: {days_old} days ago", "item_meta")
                except:
                    pass
            self.summary_text.insert(tk.END, "\n", "item_meta")
            
            # Job details
            self.summary_text.insert(tk.END, "   Match: ", "content_label")
            self.summary_text.insert(tk.END, f"{item['qualification_match']}\n", "content_text")
            
            self.summary_text.insert(tk.END, "   Due: ", "content_label")
            self.summary_text.insert(tk.END, f"{item.get('due_date', 'No specific deadline')}\n", "content_text")
            
            # Task ID for completion tracking
            if item.get('task_id'):
                self.summary_text.insert(tk.END, "   Task ID: ", "content_label")
                self.summary_text.insert(tk.END, f"{item['task_id']}\n", "item_meta")
            
            # Inline completion button
            if item.get('task_id'):
                self.summary_text.insert(tk.END, "   ", "content_text")
                
                # Create an actual Button widget embedded in the text widget
                complete_button = tk.Button(
                    self.summary_text,
                    text="✅ Mark Done",
                    command=lambda task_id=item['task_id']: self._mark_single_task_complete(task_id),
                    bg="#4CAF50",
                    fg="white",
                    font=("Arial", 8, "bold"),
                    relief="raised",
                    padx=5,
                    pady=2,
                    cursor="hand2"
                )
                
                # Insert the button widget directly into the text widget
                self.summary_text.window_create(tk.END, window=complete_button)
                
                self.summary_text.insert(tk.END, "\n", "content_text")
            
            # Links
            if item.get('links'):
                self.summary_text.insert(tk.END, "   Apply: ", "content_label")
                for j, link in enumerate(item['links'][:2]):
                    link_text = f"Apply {j+1}"
                    link_start = self.summary_text.index(tk.END)
                    self.summary_text.insert(tk.END, link_text, "link")
                    link_end = self.summary_text.index(tk.END)
                    
                    # Create unique tag for this link
                    link_tag = f"link_{hash(link)}"
                    self.summary_text.tag_add(link_tag, link_start, link_end)
                    self.summary_text.tag_configure(link_tag, foreground="#007acc", underline=True)
                    self.summary_text.tag_bind(link_tag, "<Button-1>", lambda e, url=link: self._open_url(url))
                    
                    if j < min(len(item['links']), 2) - 1:
                        self.summary_text.insert(tk.END, " | ", "content_text")
                self.summary_text.insert(tk.END, "\n", "content_text")
            
            self.summary_text.insert(tk.END, "\n", "content_text")
    
    def _display_events(self, items):
        """Display optional events with relevance"""
        for i, item in enumerate(items, 1):
            # Item title
            self.summary_text.insert(tk.END, f"{i}. {item['subject']}\n", "item_title")
            
            # Metadata
            self.summary_text.insert(tk.END, f"   From: {item['sender']}\n", "item_meta")
            
            # Event details
            self.summary_text.insert(tk.END, "   Date: ", "content_label")
            self.summary_text.insert(tk.END, f"{item['date']}\n", "content_text")
            
            self.summary_text.insert(tk.END, "   Why relevant: ", "content_label")
            self.summary_text.insert(tk.END, f"{item['relevance']}\n", "content_text")
            
            # Links
            if item.get('links'):
                self.summary_text.insert(tk.END, "   Register: ", "content_label")
                for j, link in enumerate(item['links'][:2]):
                    link_text = f"Register {j+1}"
                    link_start = self.summary_text.index(tk.END)
                    self.summary_text.insert(tk.END, link_text, "link")
                    link_end = self.summary_text.index(tk.END)
                    
                    # Create unique tag for this link
                    link_tag = f"link_{hash(link)}"
                    self.summary_text.tag_add(link_tag, link_start, link_end)
                    self.summary_text.tag_configure(link_tag, foreground="#007acc", underline=True)
                    self.summary_text.tag_bind(link_tag, "<Button-1>", lambda e, url=link: self._open_url(url))
                    
                    if j < min(len(item['links']), 2) - 1:
                        self.summary_text.insert(tk.END, " | ", "content_text")
                self.summary_text.insert(tk.END, "\n", "content_text")
            
            self.summary_text.insert(tk.END, "\n", "content_text")
    
    def _display_fyi_notices(self, items):
        """Display FYI notices as bullet points with dismiss functionality"""
        for item in items:
            bullet_text = f"• {item['summary']} ({item['sender']})\n"
            self.summary_text.insert(tk.END, bullet_text, "content_text")
        
        # Add dismiss button if there are FYI items
        if items:
            self.summary_text.insert(tk.END, "   ", "content_text")
            
            dismiss_fyi_button = tk.Button(
                self.summary_text,
                text="🗑️ Clear All FYI Items",
                command=self._dismiss_all_fyi_items,
                bg="#f8d7da",
                fg="#721c24",
                font=("Arial", 8, "bold"),
                relief="raised",
                padx=8,
                pady=2,
                cursor="hand2"
            )
            
            self.summary_text.window_create(tk.END, window=dismiss_fyi_button)
            self.summary_text.insert(tk.END, "\n", "content_text")
        
        self.summary_text.insert(tk.END, "\n", "content_text")
    
    def _display_newsletters(self, items):
        """Display newsletter summaries with dismiss functionality"""
        if len(items) > 1:
            # Combined newsletter highlights
            self.summary_text.insert(tk.END, "Combined Newsletter Highlights:\n", "item_title")
            for i, item in enumerate(items, 1):
                newsletter_text = f"{i}. {item['summary']}\n"
                self.summary_text.insert(tk.END, newsletter_text, "content_text")
        else:
            # Single newsletter
            for item in items:
                self.summary_text.insert(tk.END, f"{item['subject']}\n", "item_title")
                self.summary_text.insert(tk.END, f"From: {item['sender']}, {item['date']}\n", "item_meta")
                self.summary_text.insert(tk.END, f"{item['summary']}\n", "content_text")
        
        # Add dismiss button if there are newsletter items
        if items:
            self.summary_text.insert(tk.END, "   ", "content_text")
            
            dismiss_newsletter_button = tk.Button(
                self.summary_text,
                text="🗑️ Clear All Newsletters",
                command=self._dismiss_all_newsletters,
                bg="#fff3cd",
                fg="#856404",
                font=("Arial", 8, "bold"),
                relief="raised",
                padx=8,
                pady=2,
                cursor="hand2"
            )
            
            self.summary_text.window_create(tk.END, window=dismiss_newsletter_button)
            self.summary_text.insert(tk.END, "\n", "content_text")
        
        self.summary_text.insert(tk.END, "\n", "content_text")
    
    def _dismiss_all_fyi_items(self):
        """Dismiss all FYI items from persistent storage and refresh summary"""
        result = messagebox.askyesno("Clear FYI Items", 
                                   "Clear all FYI items?\n\n"
                                   "This will remove all FYI notices from your summary.")
        if result:
            cleared_count = self.task_persistence.clear_fyi_items()
            if cleared_count > 0:
                messagebox.showinfo("FYI Items Cleared", f"Cleared {cleared_count} FYI items.")
                # Refresh the summary to show the changes - use outstanding tasks only
                self._refresh_summary_after_dismiss()
            else:
                messagebox.showinfo("No Items", "No FYI items to clear.")
    
    def _dismiss_all_newsletters(self):
        """Dismiss all newsletter items from persistent storage and refresh summary"""
        result = messagebox.askyesno("Clear Newsletter Items", 
                                   "Clear all newsletter items?\n\n"
                                   "This will remove all newsletter summaries from your summary.")
        if result:
            cleared_count = self.task_persistence.clear_newsletter_items()
            if cleared_count > 0:
                messagebox.showinfo("Newsletter Items Cleared", f"Cleared {cleared_count} newsletter items.")
                # Refresh the summary to show the changes - use outstanding tasks only
                self._refresh_summary_after_dismiss()
            else:
                messagebox.showinfo("No Items", "No newsletter items to clear.")
    
    def _refresh_summary_after_dismiss(self):
        """Refresh summary display after dismissing items"""
        # Check if we have current email processing data
        if hasattr(self, 'action_items_data') and self.action_items_data:
            # If we have current batch data, regenerate full summary
            self.generate_summary()
        else:
            # If no current batch, just load outstanding tasks
            self.view_outstanding_tasks_only()
    
    def open_summary_in_browser(self):
        if hasattr(self, 'saved_summary_path') and self.saved_summary_path:
            file_path = os.path.abspath(self.saved_summary_path)
            webbrowser.open(f'file://{file_path}')
        else:
            messagebox.showwarning("No Summary", "Please generate a summary first.")
    
    def start_new_session(self):
        result = messagebox.askyesno("New Session", 
                                   "Start a new email processing session?\n\n"
                                   "Note: Outstanding tasks from previous batches will still appear in the summary.")
        if result:
            # Reset all data
            self.email_suggestions = []
            self.action_items_data = {}
            self.summary_sections = {}
            self.processing_cancelled = False
            
            # Reset UI
            self.progress_var.set(0)
            self.progress_text.config(state=tk.NORMAL)
            self.progress_text.delete(1.0, tk.END)
            self.progress_text.config(state=tk.DISABLED)
            
            # Clear email tree
            for item in self.email_tree.get_children():
                self.email_tree.delete(item)
            
            # Clear summary
            self.summary_text.config(state=tk.NORMAL)
            self.summary_text.delete(1.0, tk.END)
            # Keep summary text in NORMAL state to allow button clicks
            self.summary_text.bind("<Key>", lambda e: "break")  # Prevent typing
            
            # Re-enable the start processing button and disable cancel button
            self.start_processing_btn.config(state=tk.NORMAL)
            self.cancel_processing_btn.config(state=tk.DISABLED)
            
            # Disable only the review tab - keep summary tab available for outstanding tasks
            self.notebook.tab(1, state="disabled")
            
            # Switch to processing tab
            self.notebook.select(0)
            
            # Reset status
            self.status_var.set("Ready")
    
    def show_task_statistics(self):
        """Show dialog with task statistics and management options"""
        stats = self.task_persistence.get_task_statistics()
        
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Task Statistics")
        stats_window.geometry("600x500")
        stats_window.transient(self.root)
        
        # Main frame
        main_frame = ttk.Frame(stats_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Statistics display
        stats_text = scrolledtext.ScrolledText(main_frame, width=70, height=20, 
                                              font=('Consolas', 10))
        stats_text.pack(fill=tk.BOTH, expand=True)
        
        # Format statistics
        stats_content = f"""📊 TASK PERSISTENCE STATISTICS
{'='*50}

📈 Overview:
   Outstanding Tasks: {stats['outstanding_total']}
   Completed Tasks: {stats['completed_total']}
   Old Tasks (>7 days): {stats['old_tasks_count']}

📋 Breakdown by Category:
   Required Actions: {stats['sections_breakdown'].get('required_actions', 0)}
   Team Actions: {stats['sections_breakdown'].get('team_actions', 0)}
   Optional Actions: {stats['sections_breakdown'].get('optional_actions', 0)}
   Job Listings: {stats['sections_breakdown'].get('job_listings', 0)}
   Optional Events: {stats['sections_breakdown'].get('optional_events', 0)}

"""
        
        if stats['old_tasks']:
            stats_content += f"⚠️ TASKS NEEDING ATTENTION (oldest first):\n"
            stats_content += "-" * 50 + "\n"
            for task_info in stats['old_tasks']:
                task = task_info['task']
                stats_content += f"• [{task_info['days_old']} days] {task.get('subject', 'No subject')}\n"
                stats_content += f"  From: {task.get('sender', 'Unknown')}\n"
                stats_content += f"  Action: {task.get('action_required', 'Review email')}\n"
                stats_content += f"  Task ID: {task.get('task_id', 'N/A')}\n\n"
        
        stats_content += """
💡 TASK MANAGEMENT TIPS:
• Use 'Mark Tasks Complete' to remove finished tasks
• Old tasks (>7 days) may need attention or removal
• Task IDs can be used to mark specific tasks complete
• Comprehensive summaries show both new and outstanding items
        """
        
        stats_text.insert(tk.END, stats_content)
        stats_text.config(state=tk.DISABLED)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))
        
        ttk.Button(button_frame, text="Mark Tasks Complete", 
                  command=lambda: self.show_task_completion_dialog(stats_window)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Clean Old Completed", 
                  command=self.cleanup_old_tasks).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Close", 
                  command=stats_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def show_task_completion_dialog(self, parent_window=None):
        """Show dialog for marking tasks as complete"""
        outstanding_tasks = self.task_persistence.load_outstanding_tasks()
        
        # Collect all tasks with IDs
        all_tasks = []
        for section_key, tasks in outstanding_tasks.items():
            for task in tasks:
                if task.get('task_id'):
                    try:
                        # Safe task data extraction with better error handling
                        task_entry = {
                            'id': task['task_id'],
                            'subject': task.get('subject', 'No subject'),
                            'sender': task.get('sender', task.get('email_sender', 'Unknown')),
                            'section': section_key.replace('_', ' ').title(),
                            'days_old': self._calculate_task_age(task)
                        }
                        all_tasks.append(task_entry)
                    except Exception as e:
                        print(f"Warning: Error processing task {task.get('task_id', 'unknown')}: {e}")
                        # Continue with next task instead of failing completely
                        continue
        
        if not all_tasks:
            messagebox.showinfo("No Tasks", "No outstanding tasks found.")
            return
        
        # Create completion dialog
        if parent_window:
            completion_window = tk.Toplevel(parent_window)
        else:
            completion_window = tk.Toplevel(self.root)
        
        completion_window.title("Mark Tasks Complete")
        completion_window.geometry("700x400")
        completion_window.transient(self.root)
        
        main_frame = ttk.Frame(completion_window, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Select tasks to mark as complete:", 
                 font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W)
        
        # Task selection frame
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Create listbox with checkboxes (simulate with selection)
        task_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, 
                                 font=('Consolas', 9), height=15)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=task_listbox.yview)
        task_listbox.configure(yscrollcommand=scrollbar.set)
        
        task_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate task list
        task_id_map = {}
        for i, task in enumerate(all_tasks):
            display_text = f"{task['id']} | {task['subject'][:40]}... | {task['section']}"
            if task['days_old'] > 0:
                display_text += f" | {task['days_old']}d old"
            task_listbox.insert(tk.END, display_text)
            task_id_map[i] = task['id']
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(15, 0))
        
        def mark_selected_complete():
            selected_indices = task_listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("No Selection", "Please select tasks to mark complete.")
                return
            
            selected_task_ids = [task_id_map[i] for i in selected_indices]
            
            # Confirm action
            result = messagebox.askyesno("Confirm Completion", 
                                       f"Mark {len(selected_task_ids)} tasks as complete?\n\n"
                                       "This will:\n"
                                       "• Remove them from future summaries\n"
                                       "• Mark tasks as completed with timestamp")
            
            if result:
                try:
                    # Mark tasks as completed
                    self.task_persistence.mark_tasks_completed(selected_task_ids)
                    
                    messagebox.showinfo("Tasks Completed", 
                                      f"✅ Marked {len(selected_task_ids)} tasks as complete!")
                    completion_window.destroy()
                    
                    # Refresh summary using proper method
                    self._refresh_summary_after_dismiss()
                        
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to complete tasks: {e}")
                    print(f"Error completing tasks {selected_task_ids}: {e}")
        
        ttk.Button(button_frame, text="Mark Selected Complete", 
                  command=mark_selected_complete).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Cancel", 
                  command=completion_window.destroy).pack(side=tk.LEFT, padx=5)

    def _mark_single_task_complete(self, task_id):
        """Mark a single task as complete and refresh the summary"""
        result = messagebox.askyesno("Confirm Completion", 
                                   f"Mark task {task_id} as complete?\n\n"
                                   "This will:\n"
                                   "• Remove it from future summaries\n"
                                   "• Mark the task as completed with timestamp")
        
        if result:
            try:
                # Mark the task as completed
                self.task_persistence.mark_tasks_completed([task_id])
                
                messagebox.showinfo("Task Completed", 
                                  f"✅ Task {task_id} marked as complete!")
                
                # Refresh summary immediately using proper method
                self._refresh_summary_after_dismiss()
                    
            except Exception as e:
                error_msg = f"Failed to complete task: {e}"
                print(f"Full error details - Task ID: {task_id}, Error type: {type(e).__name__}, Error: {e}")
                messagebox.showerror("Error", error_msg)
        else:
            pass  # User cancelled
    
    def cleanup_old_tasks(self):
        """Clean up old completed tasks"""
        result = messagebox.askyesno("Clean Up", 
                                   "Remove completed tasks older than 30 days?\n\n"
                                   "This will permanently delete old completed task records.")
        if result:
            self.task_persistence.cleanup_old_completed_tasks(days_to_keep=30)
            messagebox.showinfo("Cleanup Complete", "Old completed tasks have been removed.")
    
    def _calculate_task_age(self, task):
        """Calculate how many days old a task is"""
        try:
            first_seen = datetime.strptime(task.get('first_seen', ''), '%Y-%m-%d %H:%M:%S')
            return (datetime.now() - first_seen).days
        except:
            return 0
    
    def view_outstanding_tasks_only(self):
        """Load and display outstanding tasks without processing new emails"""
        try:
            self.status_var.set("Loading outstanding tasks...")
            
            # Load outstanding tasks from persistent storage
            outstanding_tasks = self.task_persistence.load_outstanding_tasks()
            
            # Check if there are any tasks to display
            total_tasks = sum(len(tasks) for tasks in outstanding_tasks.values())
            
            if total_tasks == 0:
                # Display empty state message
                self.summary_text.config(state=tk.NORMAL)
                self.summary_text.delete(1.0, tk.END)
                
                self.summary_text.insert(tk.END, "📋 Outstanding Tasks\n", "main_title")
                self.summary_text.insert(tk.END, "\n")
                self.summary_text.insert(tk.END, "No outstanding tasks found.\n", "subtitle")
                self.summary_text.insert(tk.END, "\nTo get started:\n", "section_header")
                self.summary_text.insert(tk.END, "• Go to 'Process Emails' tab to analyze new emails\n", "content_text")
                self.summary_text.insert(tk.END, "• Or process a new batch using 'Process New Batch' button\n", "content_text")
                
                self.summary_text.config(state=tk.DISABLED)
                self.status_var.set("No outstanding tasks")
                return
            
            # Set up summary sections with outstanding tasks only
            self.summary_sections = self.task_persistence.get_comprehensive_summary({})
            
            # Display the tasks
            self.display_formatted_summary_in_app(self.summary_sections)
            
            self.status_var.set(f"Loaded {total_tasks} outstanding tasks")
            
        except Exception as e:
            self.status_var.set(f"Error loading tasks: {str(e)}")
            messagebox.showerror("Error", f"Failed to load outstanding tasks:\n{str(e)}")
    
    def run(self):
        self.root.mainloop()


def main():
    app = UnifiedEmailGUI()
    app.run()


if __name__ == "__main__":
    main()
