#!/usr/bin/env python3
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


class UnifiedEmailGUI:
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
        
        # Create status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 5))
        
        # Initially disable tabs 2 and 3
        self.notebook.tab(1, state="disabled")
        self.notebook.tab(2, state="disabled")
    
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
        
        for col in columns:
            self.email_tree.heading(col, text=col)
            
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
        details_frame.rowconfigure(3, weight=1)
        
        ttk.Label(details_frame, text="Category:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(details_frame, textvariable=self.category_var, 
                                          values=self.get_category_display_names(), 
                                          state="readonly")
        self.category_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        self.category_combo.bind('<<ComboboxSelected>>', self.on_category_change)
        
        ttk.Label(details_frame, text="Reason:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.explanation_var = tk.StringVar()
        self.explanation_entry = ttk.Entry(details_frame, textvariable=self.explanation_var)
        self.explanation_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        self.apply_btn = ttk.Button(details_frame, text="Apply Change", 
                                   command=self.apply_category_change, state=tk.DISABLED)
        self.apply_btn.grid(row=2, column=1, sticky=tk.E, pady=5, padx=(5, 0))
        
        self.preview_text = scrolledtext.ScrolledText(details_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        self.preview_text.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
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
        
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(pady=(0, 20))
        
        self.generate_summary_btn = ttk.Button(control_frame, text="Generate Summary", 
                                              command=self.generate_summary)
        self.generate_summary_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Open in Browser", 
                  command=self.open_summary_in_browser).pack(side=tk.LEFT, padx=5)
        
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
        
        # Configure link click behavior
        self.summary_text.tag_bind("link", "<Button-1>", self._on_summary_link_click)
        self.summary_text.tag_bind("link", "<Enter>", lambda e: self.summary_text.config(cursor="hand2"))
        self.summary_text.tag_bind("link", "<Leave>", lambda e: self.summary_text.config(cursor=""))
    
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
        self.action_items_data = self.email_processor.get_action_items_data()
        
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
        suggestion = self.ai_processor.classify_email(email_content, learning_data)
        
        # Store email suggestion with COM object for categorization
        email_suggestion = {
            'email_data': representative_email_data,
            'email_object': representative_email_data['email_object'],
            'ai_suggestion': suggestion,
            'ai_summary': ai_summary,  # Include AI summary for display
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
        self._process_email_by_category_with_enriched_data(representative_email_data, email_suggestion['thread_data'], suggestion)
    
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
        # Clear existing items
        for item in self.email_tree.get_children():
            self.email_tree.delete(item)
        
        # Load email suggestions with AI summaries
        for suggestion_data in self.email_suggestions:
            email_data = suggestion_data.get('email_data', {})
            suggestion = suggestion_data['ai_suggestion']
            ai_summary = suggestion_data.get('ai_summary', 'No summary')
            thread_data = suggestion_data.get('thread_data', {})
            thread_count = thread_data.get('thread_count', 1)
            
            if thread_count > 1:
                participants = thread_data.get('participants', [email_data.get('sender_name', 'Unknown')])
                subject = f"🧵 {thread_data.get('topic', email_data.get('subject', 'Unknown'))} ({thread_count} emails)"
                sender = f"{len(participants)} participants"
            else:
                subject = email_data.get('subject', 'Unknown Subject')
                sender = email_data.get('sender_name', 'Unknown Sender')
            
            date = email_data.get('received_time', 'Unknown Date')
            if hasattr(date, 'strftime'):
                date = date.strftime('%m-%d %H:%M')
            else:
                date = str(date)
            
            category = suggestion.replace('_', ' ').title()
            
            # Insert into treeview with AI summary
            self.email_tree.insert('', tk.END, values=(subject, sender, category, ai_summary, date))
    
    def on_email_select(self, event):
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
    
    def display_email_details(self, index):
        self.current_email_index = index
        suggestion_data = self.email_suggestions[index]
        email_data = suggestion_data.get('email_data', {})
        suggestion = suggestion_data['ai_suggestion']
        ai_summary = suggestion_data.get('ai_summary', 'No summary available')
        
        # Update preview with AI summary first, then email body
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        
        # Configure text tags for better formatting
        self._configure_text_tags()
        
        # Add AI Summary section at the top for faster review
        self.preview_text.insert(tk.END, "🤖 AI SUMMARY:\n", "header")
        self.preview_text.insert(tk.END, f"{ai_summary}\n\n", "summary")
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
                self.apply_btn.config(state=tk.NORMAL)
            else:
                self.apply_btn.config(state=tk.DISABLED)
    
    def apply_category_change(self):
        if self.current_email_index is None:
            return
        
        new_display_category = self.category_var.get()
        new_category = self.get_category_internal_name(new_display_category)
        explanation = self.explanation_var.get().strip()
        
        if not explanation:
            messagebox.showwarning("Missing Information", "Please provide a reason for the change.")
            return
        
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
        """Update action_items_data when an email is reclassified"""
        email_data = suggestion_data.get('email_data', {})
        thread_data = suggestion_data.get('thread_data', {})
        
        # Remove from old category if it exists in action_items_data
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
        
        # Add to new category
        if new_category not in self.action_items_data:
            self.action_items_data[new_category] = []
        
        # Create appropriate data structure based on new category
        if new_category == 'fyi':
            # Generate FYI summary for reclassified item
            email_content = {
                'subject': email_data.get('subject', 'Unknown'),
                'sender': email_data.get('sender_name', 'Unknown'),
                'body': email_data.get('body', ''),
                'received_time': email_data.get('received_time')
            }
            context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}"
            fyi_summary = self.ai_processor.generate_fyi_summary(email_content, context)
            
            fyi_item = {
                'summary': fyi_summary,
                'thread_data': thread_data,
                'email_subject': email_data.get('subject'),
                'email_sender': email_data.get('sender_name'),
                'email_date': email_data.get('received_time')
            }
            self.action_items_data[new_category].append(fyi_item)
            
        elif new_category == 'newsletter':
            # Generate newsletter summary for reclassified item
            email_content = {
                'subject': email_data.get('subject', 'Unknown'),
                'sender': email_data.get('sender_name', 'Unknown'),
                'body': email_data.get('body', ''),
                'received_time': email_data.get('received_time')
            }
            context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}"
            newsletter_summary = self.ai_processor.generate_newsletter_summary(email_content, context)
            
            newsletter_item = {
                'summary': newsletter_summary,
                'thread_data': thread_data,
                'email_subject': email_data.get('subject'),
                'email_sender': email_data.get('sender_name'),
                'email_date': email_data.get('received_time')
            }
            self.action_items_data[new_category].append(newsletter_item)
            
        elif new_category in ['required_personal_action', 'optional_action', 'team_action']:
            # Generate action item details for reclassified item
            email_content = {
                'subject': email_data.get('subject', 'Unknown'),
                'sender': email_data.get('sender_name', 'Unknown'),
                'body': email_data.get('body', ''),
                'received_time': email_data.get('received_time')
            }
            context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}"
            action_details = self.ai_processor.extract_action_item_details(email_content, context)
            
            action_item = {
                'action': action_details.get('action_required', 'Review email'),
                'thread_data': thread_data,
                'email_subject': email_data.get('subject'),
                'email_sender': email_data.get('sender_name'),
                'email_date': email_data.get('received_time'),
                'action_details': action_details
            }
            self.action_items_data[new_category].append(action_item)
            
        elif new_category == 'optional_event':
            # Generate event relevance for reclassified item
            relevance = self.ai_processor.assess_event_relevance(
                email_data.get('subject', ''), email_data.get('body', ''), 
                self.ai_processor.get_job_context())
            
            event_item = {
                'relevance': relevance,
                'thread_data': thread_data,
                'email_subject': email_data.get('subject'),
                'email_sender': email_data.get('sender_name'),
                'email_date': email_data.get('received_time')
            }
            self.action_items_data[new_category].append(event_item)
    
    def apply_to_outlook(self):
        if not self.email_suggestions:
            messagebox.showwarning("No Data", "No email suggestions to apply.")
            return
        
        # Calculate folder distribution for user preview
        inbox_categories = {'required_personal_action', 'optional_action', 'job_listing', 'work_relevant', 'spam_to_delete'}
        non_inbox_categories = {'team_action', 'optional_event', 'fyi', 'newsletter', 'general_information'}
        
        inbox_count = sum(1 for s in self.email_suggestions if s['ai_suggestion'] in inbox_categories)
        non_inbox_count = sum(1 for s in self.email_suggestions if s['ai_suggestion'] in non_inbox_categories)
        
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
    
    def generate_summary(self):
        self.generate_summary_btn.config(state=tk.DISABLED)
        
        # Generate summary sections
        self.summary_sections = self.summary_generator.build_summary_sections(self.action_items_data)
        
        # Display beautifully formatted summary in the app
        self.display_formatted_summary_in_app(self.summary_sections)
        
        # Also save HTML summary for browser viewing (keep existing functionality)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.saved_summary_path = self.summary_generator.save_focused_summary(self.summary_sections, timestamp)
        
        self.generate_summary_btn.config(state=tk.NORMAL)
    
    def display_formatted_summary_in_app(self, summary_sections):
        """Display beautifully formatted summary directly in the application"""
        # Clear existing content
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        
        # Calculate totals
        total_items = sum(len(items) for items in summary_sections.values())
        high_priority = len(summary_sections.get('required_actions', []))
        
        # Header
        self.summary_text.insert(tk.END, "📊 Email Summary\n", "main_title")
        self.summary_text.insert(tk.END, "Focused & Actionable\n\n", "subtitle")
        
        # Overview section
        self.summary_text.insert(tk.END, "📊 Summary Overview\n", "overview_title")
        self.summary_text.insert(tk.END, "═" * 50 + "\n", "separator")
        overview_text = f"Total Items: {total_items}    |    High Priority: {high_priority}\n"
        overview_text += "Stay focused - relevant items only!\n\n"
        self.summary_text.insert(tk.END, overview_text, "overview_stats")
        
        # Define sections with their styling
        sections_config = [
            ('required_actions', '🔴 REQUIRED ACTION ITEMS (ME)', 'section_required', self._display_action_items),
            ('team_actions', '👥 TEAM ACTION ITEMS', 'section_team', self._display_action_items),
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
        
        self.summary_text.config(state=tk.DISABLED)
        # Scroll to top for better user experience
        self.summary_text.see("1.0")
    
    def _display_action_items(self, items):
        """Display required or team action items with full details"""
        for i, item in enumerate(items, 1):
            # Item title
            self.summary_text.insert(tk.END, f"{i}. {item['subject']}\n", "item_title")
            
            # Metadata
            self.summary_text.insert(tk.END, f"   From: {item['sender']}\n", "item_meta")
            
            # Action details
            self.summary_text.insert(tk.END, "   Due: ", "content_label")
            self.summary_text.insert(tk.END, f"{item['due_date']}\n", "content_text")
            
            self.summary_text.insert(tk.END, "   Action: ", "content_label")
            self.summary_text.insert(tk.END, f"{item.get('action_required', 'Review email')}\n", "content_text")
            
            self.summary_text.insert(tk.END, "   Why: ", "content_label")
            self.summary_text.insert(tk.END, f"{item['explanation']}\n", "content_text")
            
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
    
    def _display_optional_actions(self, items):
        """Display optional action items with relevance context"""
        for i, item in enumerate(items, 1):
            # Item title
            self.summary_text.insert(tk.END, f"{i}. {item['subject']}\n", "item_title")
            
            # Metadata
            self.summary_text.insert(tk.END, f"   From: {item['sender']}\n", "item_meta")
            
            # Optional action details
            self.summary_text.insert(tk.END, "   What: ", "content_label")
            self.summary_text.insert(tk.END, f"{item.get('action_required', 'Provide feedback')}\n", "content_text")
            
            self.summary_text.insert(tk.END, "   Why relevant: ", "content_label")
            self.summary_text.insert(tk.END, f"{item['why_relevant']}\n", "content_text")
            
            self.summary_text.insert(tk.END, "   Context: ", "content_label")
            self.summary_text.insert(tk.END, f"{item['explanation']}\n", "content_text")
            
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
            # Item title
            self.summary_text.insert(tk.END, f"{i}. {item['subject']}\n", "item_title")
            
            # Metadata
            self.summary_text.insert(tk.END, f"   From: {item['sender']}\n", "item_meta")
            
            # Job details
            self.summary_text.insert(tk.END, "   Match: ", "content_label")
            self.summary_text.insert(tk.END, f"{item['qualification_match']}\n", "content_text")
            
            self.summary_text.insert(tk.END, "   Due: ", "content_label")
            self.summary_text.insert(tk.END, f"{item['due_date']}\n", "content_text")
            
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
        """Display FYI notices as bullet points"""
        for item in items:
            bullet_text = f"• {item['summary']} ({item['sender']})\n"
            self.summary_text.insert(tk.END, bullet_text, "content_text")
        self.summary_text.insert(tk.END, "\n", "content_text")
    
    def _display_newsletters(self, items):
        """Display newsletter summaries"""
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
        
        self.summary_text.insert(tk.END, "\n", "content_text")
    
    def open_summary_in_browser(self):
        if hasattr(self, 'saved_summary_path') and self.saved_summary_path:
            file_path = os.path.abspath(self.saved_summary_path)
            webbrowser.open(f'file://{file_path}')
        else:
            messagebox.showwarning("No Summary", "Please generate a summary first.")
    
    def start_new_session(self):
        result = messagebox.askyesno("New Session", 
                                   "Start a new email processing session?")
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
            self.summary_text.config(state=tk.DISABLED)
            
            # Re-enable the start processing button and disable cancel button
            self.start_processing_btn.config(state=tk.NORMAL)
            self.cancel_processing_btn.config(state=tk.DISABLED)
            
            # Disable tabs 2 and 3
            self.notebook.tab(1, state="disabled")
            self.notebook.tab(2, state="disabled")
            
            # Switch to processing tab
            self.notebook.select(0)
            
            # Reset status
            self.status_var.set("Ready")
    
    def run(self):
        self.root.mainloop()


def main():
    app = UnifiedEmailGUI()
    app.run()


if __name__ == "__main__":
    main()
