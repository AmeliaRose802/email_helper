#!/usr/bin/env python3
"""
Unified GUI - Complete workflow within a single GUI application
Implements the full email processing flow: Select → Process → Edit → Generate Summary → View
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
from datetime import datetime
import threading
import os
import webbrowser
import sys

# Add the src directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from outlook_manager import OutlookManager
from ai_processor import AIProcessor
from email_analyzer import EmailAnalyzer
from summary_generator import SummaryGenerator
from email_processor import EmailProcessor


class UnifiedEmailGUI:
    """Complete email management workflow in a single GUI"""
    
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
        self.root.title("🤖 AI Email Management - Complete Workflow")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Configure styles
        self.setup_styles()
        
        # Create GUI components
        self.create_widgets()
        
        # Initialize Outlook connection
        self.init_outlook_connection()
    
    def setup_styles(self):
        """Configure GUI styles for modern look"""
        style = ttk.Style()
        
        # Configure treeview colors for better readability
        style.configure("Treeview", rowheight=60)
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        
        # Configure button styles
        style.configure("Action.TButton", font=('Arial', 9, 'bold'))
        style.configure("Primary.TButton", font=('Arial', 10, 'bold'))
        style.configure("Success.TButton", font=('Arial', 10, 'bold'))
    
    def create_widgets(self):
        """Create all GUI widgets with tabbed interface"""
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
        self.create_status_bar()
        
        # Initially disable tabs 2 and 3
        self.notebook.tab(1, state="disabled")
        self.notebook.tab(2, state="disabled")
    
    def create_processing_tab(self):
        """Create the email processing tab"""
        # Title
        title_label = ttk.Label(self.processing_frame, text="📧 Email Processing Setup", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(20, 30))
        
        # Processing options frame
        options_frame = ttk.LabelFrame(self.processing_frame, text="Processing Options", padding="20")
        options_frame.pack(pady=(0, 20), padx=50, fill=tk.X)
        
        # Email count selection
        ttk.Label(options_frame, text="Number of emails to process:", 
                 font=('Arial', 11)).pack(anchor=tk.W, pady=(0, 5))
        
        self.email_count_var = tk.StringVar(value="50")
        email_count_frame = ttk.Frame(options_frame)
        email_count_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Predefined options
        for count in [25, 50, 100, 200]:
            ttk.Radiobutton(email_count_frame, text=str(count), variable=self.email_count_var, 
                           value=str(count)).pack(side=tk.LEFT, padx=(0, 15))
        
        # Custom option
        custom_frame = ttk.Frame(options_frame)
        custom_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(custom_frame, text="Or custom count:").pack(side=tk.LEFT)
        self.custom_count_entry = ttk.Entry(custom_frame, width=10)
        self.custom_count_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Processing controls
        control_frame = ttk.Frame(self.processing_frame)
        control_frame.pack(pady=20)
        
        self.start_processing_btn = ttk.Button(control_frame, text="🚀 Start Processing Emails", 
                                              command=self.start_email_processing, 
                                              style="Primary.TButton")
        self.start_processing_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_processing_btn = ttk.Button(control_frame, text="⏹️ Cancel", 
                                               command=self.cancel_processing, 
                                               state=tk.DISABLED)
        self.cancel_processing_btn.pack(side=tk.LEFT)
        
        # Progress section
        progress_frame = ttk.LabelFrame(self.processing_frame, text="Processing Progress", padding="15")
        progress_frame.pack(pady=(20, 0), padx=50, fill=tk.BOTH, expand=True)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=400)
        self.progress_bar.pack(pady=(0, 10), fill=tk.X)
        
        # Progress text
        self.progress_text = scrolledtext.ScrolledText(progress_frame, height=15, 
                                                      state=tk.DISABLED, wrap=tk.WORD)
        self.progress_text.pack(fill=tk.BOTH, expand=True)
    
    def create_editing_tab(self):
        """Create the email editing tab (similar to existing EmailSuggestionGUI)"""
        # Main container
        main_frame = ttk.Frame(self.editing_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="✏️ Review & Edit Email Classifications", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))
        
        # Create email list
        self.create_email_treeview(main_frame)
        
        # Create details panel
        self.create_details_panel(main_frame)
        
        # Create editing controls
        self.create_editing_controls(main_frame)
    
    def create_email_treeview(self, parent):
        """Create the email list treeview"""
        # Frame for treeview and scrollbar
        tree_frame = ttk.Frame(parent)
        tree_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Create treeview
        columns = ('Subject', 'From', 'Category', 'Date')
        self.email_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)
        
        # Configure column headings and widths
        self.email_tree.heading('Subject', text='Subject')
        self.email_tree.heading('From', text='From')
        self.email_tree.heading('Category', text='AI Category')
        self.email_tree.heading('Date', text='Date')
        
        self.email_tree.column('Subject', width=300, minwidth=200)
        self.email_tree.column('From', width=200, minwidth=150)
        self.email_tree.column('Category', width=180, minwidth=120)
        self.email_tree.column('Date', width=120, minwidth=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.email_tree.yview)
        self.email_tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid treeview and scrollbar
        self.email_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind selection event
        self.email_tree.bind('<<TreeviewSelect>>', self.on_email_select)
    
    def create_details_panel(self, parent):
        """Create the email details and editing panel"""
        details_frame = ttk.LabelFrame(parent, text="📧 Email Details & Classification", padding="10")
        details_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        details_frame.columnconfigure(1, weight=1)
        details_frame.rowconfigure(4, weight=1)
        
        # Email details labels
        ttk.Label(details_frame, text="Subject:", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.subject_var = tk.StringVar()
        self.subject_label = ttk.Label(details_frame, textvariable=self.subject_var, wraplength=300)
        self.subject_label.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        ttk.Label(details_frame, text="From:", font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.from_var = tk.StringVar()
        self.from_label = ttk.Label(details_frame, textvariable=self.from_var)
        self.from_label.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        ttk.Label(details_frame, text="Date:", font=('Arial', 9, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=2)
        self.date_var = tk.StringVar()
        self.date_label = ttk.Label(details_frame, textvariable=self.date_var)
        self.date_label.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Category selection
        ttk.Label(details_frame, text="Category:", font=('Arial', 9, 'bold')).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(details_frame, textvariable=self.category_var, 
                                          values=self.get_category_display_names(), 
                                          state="readonly", width=25)
        self.category_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        self.category_combo.bind('<<ComboboxSelected>>', self.on_category_change)
        
        # Email preview
        ttk.Label(details_frame, text="Preview:", font=('Arial', 9, 'bold')).grid(row=4, column=0, sticky=(tk.W, tk.N), pady=(5, 0))
        self.preview_text = scrolledtext.ScrolledText(details_frame, height=8, width=40, wrap=tk.WORD, state=tk.DISABLED)
        self.preview_text.grid(row=4, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0), padx=(5, 0))
        
        # Change explanation
        ttk.Label(details_frame, text="Change reason:", font=('Arial', 9, 'bold')).grid(row=5, column=0, sticky=(tk.W, tk.N), pady=(10, 0))
        self.explanation_var = tk.StringVar()
        self.explanation_entry = ttk.Entry(details_frame, textvariable=self.explanation_var, width=40)
        self.explanation_entry.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=(10, 0), padx=(5, 0))
        
        # Apply change button
        self.apply_btn = ttk.Button(details_frame, text="✅ Apply Change", 
                                   command=self.apply_category_change, state=tk.DISABLED,
                                   style="Action.TButton")
        self.apply_btn.grid(row=6, column=1, sticky=tk.E, pady=(10, 0), padx=(5, 0))
        
        # Track current selection
        self.current_email_index = None
        self.original_category = None
    
    def create_editing_controls(self, parent):
        """Create editing control buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, columnspan=3, pady=(15, 0))
        
        ttk.Button(button_frame, text="🔄 Refresh List", 
                  command=self.refresh_email_list).grid(row=0, column=0, padx=5)
        
        ttk.Button(button_frame, text="✅ Apply to Outlook", 
                  command=self.apply_to_outlook).grid(row=0, column=1, padx=5)
        
        ttk.Button(button_frame, text="➡️ Generate Summary", 
                  command=self.proceed_to_summary, 
                  style="Primary.TButton").grid(row=0, column=2, padx=5)
    
    def create_summary_tab(self):
        """Create the summary generation and viewing tab"""
        # Main container
        main_frame = ttk.Frame(self.summary_frame, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="📊 Summary Generation & Results", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Generation controls
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(pady=(0, 20))
        
        self.generate_summary_btn = ttk.Button(control_frame, text="📋 Generate Summary", 
                                              command=self.generate_summary,
                                              style="Success.TButton")
        self.generate_summary_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(control_frame, text="🌐 Open in Browser", 
                  command=self.open_summary_in_browser).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(control_frame, text="🔄 Process New Batch", 
                  command=self.start_new_session).pack(side=tk.LEFT)
        
        # Summary display
        summary_display_frame = ttk.LabelFrame(main_frame, text="Summary Preview", padding="10")
        summary_display_frame.pack(fill=tk.BOTH, expand=True)
        
        self.summary_text = scrolledtext.ScrolledText(summary_display_frame, wrap=tk.WORD, 
                                                     height=20, state=tk.DISABLED)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Connect to Outlook to begin")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 5))
    
    def init_outlook_connection(self):
        """Initialize Outlook connection"""
        try:
            self.outlook_manager.connect_to_outlook()
            self.status_var.set("✅ Connected to Outlook - Ready to process emails")
        except Exception as e:
            self.status_var.set(f"❌ Outlook connection failed: {str(e)}")
            messagebox.showerror("Connection Error", 
                               f"Failed to connect to Outlook:\n\n{str(e)}\n\n"
                               "Please ensure Outlook is running and try again.")
    
    def get_category_display_names(self):
        """Get user-friendly category names"""
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
        """Convert display name back to internal category name"""
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
        """Start email processing - retrieve Outlook data first (main thread), then process in background"""
        try:
            # Get email count
            if self.custom_count_entry.get().strip():
                try:
                    max_emails = int(self.custom_count_entry.get().strip())
                except ValueError:
                    messagebox.showerror("Invalid Input", "Custom count must be a valid number")
                    return
            else:
                max_emails = int(self.email_count_var.get())
            
            if max_emails <= 0 or max_emails > 500:
                messagebox.showerror("Invalid Range", "Email count must be between 1 and 500")
                return
            
            # Reset processing state
            self.processing_cancelled = False
            
            # Update UI state
            self.start_processing_btn.config(state=tk.DISABLED)
            self.cancel_processing_btn.config(state=tk.NORMAL)
            self.progress_var.set(0)
            self.progress_text.config(state=tk.NORMAL)
            self.progress_text.delete(1.0, tk.END)
            self.progress_text.config(state=tk.DISABLED)
            
            self.update_progress(0, f"Starting email processing for {max_emails} emails...")
            self.update_progress(20, "Retrieving conversations using Outlook APIs...")
            
            # CRITICAL FIX: Get Outlook data on main thread (COM apartment thread)
            try:
                conversation_data = self.outlook_manager.get_emails_with_full_conversations(
                    days_back=7, max_emails=max_emails)
                
                # ALSO EXTRACT EMAIL BODIES ON MAIN THREAD
                self.update_progress(25, "Extracting email content...")
                enriched_conversation_data = []
                
                for conversation_id, conv_info in conversation_data:
                    # Extract email bodies for all emails in conversation
                    emails_with_body = []
                    for email in conv_info['emails']:
                        try:
                            # Get body safely on main thread
                            body = self.outlook_manager.get_email_body(email)
                            emails_with_body.append({
                                # Store COM object reference for categorization (will only be used on main thread)
                                'email_object': email,  # Keep this for categorization step
                                'body': body,
                                'subject': email.Subject,
                                'sender_name': email.SenderName,
                                'received_time': email.ReceivedTime,
                                'entry_id': email.EntryID
                            })
                        except Exception as body_error:
                            # Skip emails we can't access
                            self.update_progress_text(f"⚠️  Could not extract body for email: {str(body_error)}")
                            continue
                    
                    if emails_with_body:  # Only include conversations with accessible emails
                        enriched_conv_info = conv_info.copy()
                        enriched_conv_info['emails_with_body'] = emails_with_body
                        # Remove the original COM objects to prevent accidental access
                        enriched_conv_info.pop('emails', None)
                        enriched_conv_info.pop('recent_trigger', None)
                        # Add basic info from COM objects as plain data
                        enriched_conv_info['topic'] = conv_info['topic']
                        enriched_conv_info['latest_date'] = conv_info['latest_date']
                        enriched_conv_info['trigger_subject'] = conv_info['recent_trigger'].Subject
                        enriched_conv_info['trigger_sender'] = conv_info['recent_trigger'].SenderName
                        enriched_conv_info['trigger_date'] = conv_info['recent_trigger'].ReceivedTime
                        
                        enriched_conversation_data.append((conversation_id, enriched_conv_info))
                
                conversation_data = enriched_conversation_data
                
            except Exception as outlook_error:
                self.status_var.set(f"❌ Failed to access Outlook: {str(outlook_error)}")
                messagebox.showerror("Outlook Error", f"Failed to retrieve emails from Outlook:\n\n{str(outlook_error)}")
                self.reset_processing_ui()
                return
            
            if not conversation_data:
                self.update_progress(100, "❌ No emails found to process")
                messagebox.showwarning("No Emails", "No emails found in the specified date range. Try:\n• Increasing the email count\n• Checking if you have emails in your inbox\n• Verifying Outlook connection")
                self.reset_processing_ui()
                return
            
            self.update_progress(30, f"Found {len(conversation_data)} conversations. Starting AI analysis...")
            
            # Now start background thread with the retrieved data
            processing_thread = threading.Thread(target=self.process_emails_background, 
                                                args=(conversation_data,), daemon=True)
            processing_thread.start()
            
        except Exception as e:
            self.status_var.set(f"❌ Failed to start processing: {str(e)}")
            messagebox.showerror("Processing Error", f"Failed to start email processing:\n\n{str(e)}")
            self.reset_processing_ui()
    
    def process_emails_background(self, conversation_data):
        """Process emails in background thread with progress updates - NO OUTLOOK ACCESS HERE"""
        try:
            # Reset email processor data
            self.email_processor._reset_data_storage()
            
            self.update_progress(35, "Loading AI learning data...")
            learning_data = self.ai_processor.load_learning_data()
            
            if self.processing_cancelled:
                return
            
            total_conversations = len(conversation_data)
            self.update_progress(40, f"Analyzing {total_conversations} unique conversations...")
            
            # Initialize accuracy tracking
            self.ai_processor.start_accuracy_session(total_conversations)
            
            # Process each conversation with progress updates
            processed_count = 0
            for i, (conversation_id, conv_info) in enumerate(conversation_data, 1):
                if self.processing_cancelled:
                    self.update_progress(0, "❌ Processing cancelled by user")
                    return
                
                # Calculate progress (40% to 90% for processing)
                # i is 1-based, so subtract 1 to make it 0-based for calculation
                start_progress = 40 + (50 * (i - 1) / total_conversations)
                self.update_progress(start_progress, f"Processing conversation {i}/{total_conversations}...")
                
                # Process single conversation
                try:
                    self.process_single_conversation(conversation_id, conv_info, i, total_conversations, learning_data)
                    processed_count += 1
                    
                    # Update progress after completing this conversation
                    end_progress = 40 + (50 * i / total_conversations)
                    self.update_progress(end_progress, f"Completed conversation {i}/{total_conversations}")
                    
                except Exception as conv_error:
                    self.update_progress_text(f"❌ Error processing conversation: {str(conv_error)}")
                    continue
                
                # Small delay to prevent overwhelming the UI
                self.root.after(50)
            
            if self.processing_cancelled:
                return
            
            self.update_progress(95, "Finalizing processing...")
            
            # Store results
            self.email_suggestions = self.email_processor.get_email_suggestions()
            self.action_items_data = self.email_processor.get_action_items_data()
            
            self.update_progress(100, f"✅ Processing complete! {processed_count} conversations processed.")
            
            # Enable next tab and update UI
            self.root.after(0, self.on_processing_complete)
            
        except Exception as e:
            error_msg = f"❌ Processing failed: {str(e)}"
            self.update_progress(0, error_msg)
            # Capture the error message to avoid closure issues
            error_message = str(e)
            self.root.after(0, lambda msg=error_message: messagebox.showerror("Processing Error", msg))
        finally:
            # Reset UI state
            self.root.after(0, self.reset_processing_ui)
    
    def process_single_conversation(self, conversation_id, conv_info, index, total, learning_data):
        """Process a single conversation with detailed progress updates - NO COM OBJECTS"""
        # Use the enriched data with pre-extracted email bodies (no COM objects)
        emails_with_body = conv_info.get('emails_with_body', [])
        if not emails_with_body:
            # Fallback: if emails_with_body not available, skip this conversation
            self.update_progress_text(f"❌ Skipping conversation {index}/{total} - no accessible email data")
            return
        
        # Use plain data instead of COM objects
        topic = conv_info.get('topic', 'Unknown Topic')
        latest_date = conv_info.get('latest_date', 'Unknown Date')
        trigger_subject = conv_info.get('trigger_subject', 'Unknown Subject')
        trigger_sender = conv_info.get('trigger_sender', 'Unknown Sender')
        trigger_date = conv_info.get('trigger_date', 'Unknown Date')
        
        thread_count = len(emails_with_body)
        thread_info = f" (Thread: {thread_count} emails)" if thread_count > 1 else ""
        
        # Update progress with email details
        date_str = trigger_date.strftime('%Y-%m-%d %H:%M') if hasattr(trigger_date, 'strftime') else str(trigger_date)
        progress_msg = (f"📧 CONVERSATION {index}/{total}{thread_info}\n"
                       f"Topic: {topic}\n"
                       f"From: {trigger_sender}\n"
                       f"Date: {date_str}")
        
        if thread_count > 1:
            participants = list(set(email_data['sender_name'] for email_data in emails_with_body))
            progress_msg += (f"\n🔗 Full Thread: {thread_count} emails\n"
                           f"   Participants: {', '.join(participants[:3])}{'...' if len(participants) > 3 else ''}")
        
        self.update_progress_text(progress_msg)
        
        # Choose representative email from enriched data (most recent)
        representative_email_data = emails_with_body[0]  # Most recent email
        
        # Create email content dict using pre-extracted data
        email_content = {
            'subject': representative_email_data['subject'],
            'sender': representative_email_data['sender_name'],
            'body': representative_email_data['body'],
            'received_time': representative_email_data['received_time']
        }
        
        # Add thread context if needed
        if thread_count > 1:
            thread_context = self._build_thread_context_from_enriched_data(emails_with_body, representative_email_data)
            email_content['body'] += f"\n\n--- CONVERSATION THREAD CONTEXT ---\n{thread_context}"
        
        # Generate AI summary
        ai_summary = self.ai_processor.generate_email_summary(email_content)
        if ai_summary:
            self.update_progress_text(f"📋 AI Summary: {ai_summary}")
        
        # Classify email
        suggestion = self.ai_processor.classify_email(email_content, learning_data)
        self.update_progress_text(f"🤖 AI Classification: {suggestion.replace('_', ' ').title()}")
        
        # Store email suggestion with COM object for categorization (main thread only)
        email_suggestion = {
            'email_data': representative_email_data,  # Enriched data for display
            'email_object': representative_email_data['email_object'],  # COM object for categorization
            'ai_suggestion': suggestion,
            'thread_data': {
                'conversation_id': conversation_id,
                'thread_count': thread_count,
                'all_emails_data': emails_with_body,  # Enriched data for display
                'all_emails': [email_data['email_object'] for email_data in emails_with_body],  # COM objects for categorization
                'participants': list(set(email_data['sender_name'] for email_data in emails_with_body)),
                'latest_date': latest_date,
                'topic': topic
            }
        }
        
        self.email_processor.email_suggestions.append(email_suggestion)
        
        # Process by category using pre-extracted data (no COM access)
        self._process_email_by_category_with_enriched_data(representative_email_data, email_suggestion['thread_data'], suggestion)
        
        self.update_progress_text("✅ Processing complete\n" + "="*50)
    
    def _build_thread_context_from_enriched_data(self, emails_with_body, representative_email_data):
        """Build thread context from pre-extracted email data"""
        thread_context = []
        for email_data in emails_with_body:
            # Skip the representative email to avoid duplication
            if email_data['entry_id'] == representative_email_data['entry_id']:
                continue
                
            context_entry = (f"From: {email_data['sender_name']}\n"
                           f"Date: {email_data['received_time'].strftime('%Y-%m-%d %H:%M')}\n"
                           f"Subject: {email_data['subject']}\n"
                           f"Content: {email_data['body'][:500]}{'...' if len(email_data['body']) > 500 else ''}\n"
                           f"---")
            thread_context.append(context_entry)
        
        return "\n\n".join(thread_context)
    
    def _process_email_by_category_with_enriched_data(self, email_data, thread_data, category):
        """Process email by category using enriched data (no Outlook access)"""
        subject = email_data['subject']
        body = email_data['body']
        sender_name = email_data['sender_name']
        received_time = email_data['received_time']
        
        # Create email content for AI processing
        email_content = {
            'subject': subject,
            'sender': sender_name,
            'body': body,
            'received_time': received_time
        }
        
        # Process based on category without accessing any COM objects
        if category == 'required_personal_action':
            qualification_match = self.email_analyzer.assess_job_qualification(subject, body)
            due_date = self.email_analyzer.extract_due_date_intelligent(f"{subject} {body}")
            links = self.email_analyzer.extract_links_intelligent(body)
            
            # Use correct method for action details
            context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}"
            action_details = self.ai_processor.extract_action_item_details(email_content, context)
            
            # Create a safe email object wrapper that doesn't access COM properties
            safe_email_object = type('SafeEmailObject', (), {
                'Subject': subject,
                'SenderName': sender_name,
                'ReceivedTime': received_time
            })()
            
            action_item = {
                'action': action_details.get('action_required', 'Review email'),
                'qualification_match': qualification_match,
                'due_date': due_date,
                'links': links,
                'thread_data': thread_data,
                'email_subject': subject,
                'email_sender': sender_name,
                'email_date': received_time,
                'action_details': action_details,
                # Use safe wrapper instead of COM object
                'email_object': safe_email_object
            }
            
            # Add to email_processor data directly (avoid method calls that might access COM)
            if not hasattr(self.email_processor, 'action_items_data'):
                self.email_processor.action_items_data = {}
            if 'required_personal_action' not in self.email_processor.action_items_data:
                self.email_processor.action_items_data['required_personal_action'] = []
            self.email_processor.action_items_data['required_personal_action'].append(action_item)
            
        elif category == 'optional_event':
            event_date = self.email_analyzer.extract_due_date_intelligent(f"{subject} {body}")
            relevance = self.ai_processor.assess_event_relevance(subject, body, self.ai_processor.get_job_context())
            links = self.email_analyzer.extract_links_intelligent(body)
            
            # Use correct method for event summary
            context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}"
            action_details = self.ai_processor.extract_action_item_details(email_content, context)
            
            # Create a safe email object wrapper that doesn't access COM properties
            safe_email_object = type('SafeEmailObject', (), {
                'Subject': subject,
                'SenderName': sender_name,
                'ReceivedTime': received_time
            })()
            
            event_item = {
                'event': action_details.get('action_required', f'Event: {subject}'),
                'event_date': event_date,
                'relevance': relevance,
                'links': links,
                'thread_data': thread_data,
                'email_subject': subject,
                'email_sender': sender_name,
                'email_date': received_time,
                # Use safe wrapper instead of COM object
                'email_object': safe_email_object
            }
            
            # Add to email_processor data directly
            if not hasattr(self.email_processor, 'action_items_data'):
                self.email_processor.action_items_data = {}
            if 'optional_event' not in self.email_processor.action_items_data:
                self.email_processor.action_items_data['optional_event'] = []
            self.email_processor.action_items_data['optional_event'].append(event_item)
        
        elif category == 'fyi':
            # Generate FYI summary
            context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}"
            fyi_summary = self.ai_processor.generate_fyi_summary(email_content, context)
            
            # Create a safe email object wrapper that doesn't access COM properties
            safe_email_object = type('SafeEmailObject', (), {
                'Subject': subject,
                'SenderName': sender_name,
                'ReceivedTime': received_time
            })()
            
            fyi_item = {
                'summary': fyi_summary,
                'thread_data': thread_data,
                'email_subject': subject,
                'email_sender': sender_name,
                'email_date': received_time,
                # Use safe wrapper instead of COM object
                'email_object': safe_email_object
            }
            
            if not hasattr(self.email_processor, 'action_items_data'):
                self.email_processor.action_items_data = {}
            if 'fyi' not in self.email_processor.action_items_data:
                self.email_processor.action_items_data['fyi'] = []
            self.email_processor.action_items_data['fyi'].append(fyi_item)
            
        elif category == 'newsletter':
            # Generate newsletter summary
            context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}"
            newsletter_summary = self.ai_processor.generate_newsletter_summary(email_content, context)
            
            # Create a safe email object wrapper that doesn't access COM properties
            safe_email_object = type('SafeEmailObject', (), {
                'Subject': subject,
                'SenderName': sender_name,
                'ReceivedTime': received_time
            })()
            
            newsletter_item = {
                'summary': newsletter_summary,
                'thread_data': thread_data,
                'email_subject': subject,
                'email_sender': sender_name,
                'email_date': received_time,
                # Use safe wrapper instead of COM object
                'email_object': safe_email_object
            }
            
            if not hasattr(self.email_processor, 'action_items_data'):
                self.email_processor.action_items_data = {}
            if 'newsletter' not in self.email_processor.action_items_data:
                self.email_processor.action_items_data['newsletter'] = []
            self.email_processor.action_items_data['newsletter'].append(newsletter_item)
        
        # Add processing for other categories as needed without COM object access
    
    def update_progress(self, value, message):
        """Update progress bar and status"""
        def update_ui():
            self.progress_var.set(value)
            self.status_var.set(message)
        self.root.after(0, update_ui)
    
    def update_progress_text(self, message):
        """Update progress text area"""
        def update_ui():
            self.progress_text.config(state=tk.NORMAL)
            self.progress_text.insert(tk.END, message + "\n")
            self.progress_text.see(tk.END)
            self.progress_text.config(state=tk.DISABLED)
            self.root.update_idletasks()
        self.root.after(0, update_ui)
    
    def cancel_processing(self):
        """Cancel email processing"""
        self.processing_cancelled = True
        self.status_var.set("Cancelling processing...")
    
    def reset_processing_ui(self):
        """Reset processing UI elements"""
        self.start_processing_btn.config(state=tk.NORMAL)
        self.cancel_processing_btn.config(state=tk.DISABLED)
    
    def on_processing_complete(self):
        """Handle completion of email processing"""
        # Enable editing tab
        self.notebook.tab(1, state="normal")
        
        # Load emails into editing interface
        self.load_processed_emails()
        
        # Switch to editing tab
        self.notebook.select(1)
        
        # Update status
        self.status_var.set(f"✅ Processing complete - {len(self.email_suggestions)} conversations ready for review")
    
    def load_processed_emails(self):
        """Load processed emails into the editing interface"""
        # Clear existing items
        for item in self.email_tree.get_children():
            self.email_tree.delete(item)
        
        # Load email suggestions
        for suggestion_data in self.email_suggestions:
            # Use enriched email data instead of COM object
            email_data = suggestion_data.get('email_data', {})
            suggestion = suggestion_data['ai_suggestion']
            thread_data = suggestion_data.get('thread_data', {})
            thread_count = thread_data.get('thread_count', 1)
            
            # Format display data
            if thread_count > 1:
                participants = thread_data.get('participants', [email_data.get('sender_name', 'Unknown')])
                subject = f"🧵 {thread_data.get('topic', email_data.get('subject', 'Unknown'))} ({thread_count} emails)"
                sender = f"{len(participants)} participants"
                date = email_data.get('received_time', 'Unknown')
                if hasattr(date, 'strftime'):
                    date = date.strftime('%Y-%m-%d %H:%M')
                else:
                    date = str(date)
            else:
                subject = email_data.get('subject', 'Unknown Subject')
                sender = email_data.get('sender_name', 'Unknown Sender')
                date = email_data.get('received_time', 'Unknown Date')
                if hasattr(date, 'strftime'):
                    date = date.strftime('%Y-%m-%d %H:%M')
                else:
                    date = str(date)
            
            category = suggestion.replace('_', ' ').title()
            
            # Insert into treeview
            self.email_tree.insert('', tk.END, values=(subject, sender, category, date))
        
        self.status_var.set(f"Loaded {len(self.email_suggestions)} conversations for review")
    
    def on_email_select(self, event):
        """Handle email selection in treeview"""
        selection = self.email_tree.selection()
        if not selection:
            return
        
        # Get selected item index
        item = selection[0]
        index = None
        for i, child in enumerate(self.email_tree.get_children()):
            if child == item:
                index = i
                break
        
        if index is not None and index < len(self.email_suggestions):
            self.display_email_details(index)
    
    def display_email_details(self, index):
        """Display email details in the details panel"""
        self.current_email_index = index
        suggestion_data = self.email_suggestions[index]
        email_data = suggestion_data.get('email_data', {})
        suggestion = suggestion_data['ai_suggestion']
        thread_data = suggestion_data.get('thread_data', {})
        thread_count = thread_data.get('thread_count', 1)
        
        # Update email details using enriched data
        if thread_count > 1:
            topic = thread_data.get('topic', email_data.get('subject', 'Unknown'))
            participants = thread_data.get('participants', [email_data.get('sender_name', 'Unknown')])
            latest_date = thread_data.get('latest_date', email_data.get('received_time', 'Unknown'))
            
            self.subject_var.set(f"Conversation: {topic}")
            self.from_var.set(f"{len(participants)} participants: {', '.join(participants[:2])}{'...' if len(participants) > 2 else ''}")
            
            if hasattr(latest_date, 'strftime'):
                self.date_var.set(f"Latest: {latest_date.strftime('%Y-%m-%d %H:%M')}")
            else:
                self.date_var.set(f"Latest: {str(latest_date)}")
            
            # Create preview showing thread summary
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)
            
            preview_content = f"🧵 CONVERSATION THREAD ({thread_count} emails)\n\n"
            preview_content += f"Topic: {topic}\n"
            preview_content += f"Participants: {', '.join(participants)}\n\n"
            
            # Show latest email content as preview using pre-extracted data
            body = email_data.get('body', 'No content available')
            preview_content += f"Latest email preview:\n{body[:300]}"
            if len(body) > 300:
                preview_content += "\n\n[... truncated ...]"
            
            # Add thread summary using enriched data
            all_emails_data = thread_data.get('all_emails_data', [email_data])
            if len(all_emails_data) > 1:
                preview_content += f"\n\n--- THREAD EMAILS ---\n"
                for i, thread_email_data in enumerate(all_emails_data[-3:], 1):
                    received_time = thread_email_data.get('received_time', 'Unknown')
                    if hasattr(received_time, 'strftime'):
                        date_str = received_time.strftime('%m/%d %H:%M')
                    else:
                        date_str = str(received_time)
                    
                    sender = thread_email_data.get('sender_name', 'Unknown')
                    subject = thread_email_data.get('subject', 'No subject')[:50]
                    preview_content += f"{i}. {date_str} - {sender}: {subject}\n"
            
            self.preview_text.insert(tk.END, preview_content)
        else:
            # Show single email details using enriched data
            self.subject_var.set(email_data.get('subject', 'Unknown Subject'))
            self.from_var.set(email_data.get('sender_name', 'Unknown Sender'))
            
            received_time = email_data.get('received_time', 'Unknown Date')
            if hasattr(received_time, 'strftime'):
                self.date_var.set(received_time.strftime('%Y-%m-%d %H:%M'))
            else:
                self.date_var.set(str(received_time))
            
            # Update preview using pre-extracted data
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)
            
            body = email_data.get('body', 'No content available')
            self.preview_text.insert(tk.END, body[:500])
            if len(body) > 500:
                self.preview_text.insert(tk.END, "\n\n[... truncated ...]")
        
        self.preview_text.config(state=tk.DISABLED)
        
        
        # Update category dropdown
        self.category_var.set(suggestion.replace('_', ' ').title())
        self.original_category = suggestion
        
        # Clear explanation and disable apply button
        self.explanation_var.set("")
        self.apply_btn.config(state=tk.DISABLED)
        
        # Update status with thread info
        subject = email_data.get('subject', 'Unknown Subject')
        thread_info = f" ({thread_count} emails)" if thread_count > 1 else ""
        self.status_var.set(f"Selected: {subject[:40]}{'...' if len(subject) > 40 else ''}{thread_info}")
    
    def on_category_change(self, event):
        """Handle category change in combobox"""
        if self.current_email_index is not None:
            current_category = self.get_category_internal_name(self.category_var.get())
            if current_category != self.original_category:
                self.apply_btn.config(state=tk.NORMAL)
            else:
                self.apply_btn.config(state=tk.DISABLED)
    
    def apply_category_change(self):
        """Apply the category change"""
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
        self.refresh_email_list()
        
        # Re-select the current email
        if self.current_email_index < len(self.email_tree.get_children()):
            item_id = list(self.email_tree.get_children())[self.current_email_index]
            self.email_tree.selection_set(item_id)
        
        self.status_var.set("✅ Category change applied successfully")
    
    def edit_suggestion(self, email_index, new_category, user_explanation):
        """Edit a specific email suggestion"""
        if email_index >= len(self.email_suggestions):
            return
        
        suggestion_data = self.email_suggestions[email_index]
        old_category = suggestion_data['ai_suggestion']
        email = suggestion_data['email_object']
        
        # Update the suggestion
        suggestion_data['ai_suggestion'] = new_category
        
        # Record the change for accuracy tracking
        email_data = suggestion_data.get('email_data', {})
        email_info = {
            'subject': email_data.get('subject', 'Unknown'),
            'sender': email_data.get('sender_name', 'Unknown'),
            'body': email_data.get('body', '')[:500]  # Truncate for storage
        }
        self.ai_processor.record_suggestion_modification(email_info, old_category, new_category, user_explanation)
        
        # Remove from old action data category
        self._remove_from_action_data(email, old_category)
        
        # Add to new action data category
        self._add_to_action_data(email, new_category)
        
        print(f"✅ Updated: {email.Subject}")
        print(f"   Changed from: {old_category.replace('_', ' ').title()}")
        print(f"   Changed to: {new_category.replace('_', ' ').title()}")
        print(f"   Reason: {user_explanation}")
    
    def _remove_from_action_data(self, email, category):
        """Remove email from action_items_data category"""
        if category in self.action_items_data:
            # Find and remove the email from this category
            self.action_items_data[category] = [
                item for item in self.action_items_data[category]
                if item['email_object'].EntryID != email.EntryID
            ]
    
    def _add_to_action_data(self, email, new_category):
        """Add email to action_items_data in new category"""
        if new_category not in self.action_items_data:
            self.action_items_data[new_category] = []
        
        # Create appropriate data structure based on category
        if new_category in ['required_personal_action', 'team_action', 'optional_action']:
            # For action categories, we'd need to re-process to get action details
            # For now, add with minimal details
            email_content = self.email_processor._create_email_content_dict(email)
            context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}"
            action_details = self.ai_processor.extract_action_item_details(email_content, context)
            
            self.action_items_data[new_category].append({
                'email_object': email,
                'action_details': action_details,
                'thread_data': {}
            })
        elif new_category == 'job_listing':
            qualification_match = self.email_analyzer.assess_job_qualification(email.Subject, self.outlook_manager.get_email_body(email))
            due_date = self.email_analyzer.extract_due_date_intelligent(f"{email.Subject} {self.outlook_manager.get_email_body(email)}")
            links = self.email_analyzer.extract_links_intelligent(self.outlook_manager.get_email_body(email))
            
            self.action_items_data[new_category].append({
                'email_object': email,
                'qualification_match': qualification_match,
                'due_date': due_date,
                'links': links,
                'thread_data': {}
            })
        elif new_category == 'optional_event':
            event_date = self.email_analyzer.extract_due_date_intelligent(f"{email.Subject} {self.outlook_manager.get_email_body(email)}")
            relevance = self.ai_processor.assess_event_relevance(email.Subject, self.outlook_manager.get_email_body(email), self.ai_processor.get_job_context())
            links = self.email_analyzer.extract_links_intelligent(self.outlook_manager.get_email_body(email))
            
            self.action_items_data[new_category].append({
                'email_object': email,
                'date': event_date,
                'relevance': relevance,
                'links': links,
                'thread_data': {}
            })
        elif new_category == 'fyi':
            email_content = self.email_processor._create_email_content_dict(email)
            context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}"
            fyi_summary = self.ai_processor.generate_fyi_summary(email_content, context)
            
            self.action_items_data[new_category].append({
                'email_object': email,
                'summary': fyi_summary,
                'thread_data': {}
            })
        elif new_category == 'newsletter':
            email_content = self.email_processor._create_email_content_dict(email)
            context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}"
            newsletter_summary = self.ai_processor.generate_newsletter_summary(email_content, context)
            
            self.action_items_data[new_category].append({
                'email_object': email,
                'summary': newsletter_summary,
                'thread_data': {}
            })
    
    def refresh_email_list(self):
        """Refresh the email list in the treeview"""
        # Clear existing items
        for item in self.email_tree.get_children():
            self.email_tree.delete(item)
        
        # Reload with current data
        self.load_processed_emails()
    
    def apply_to_outlook(self):
        """Apply categorization to Outlook"""
        if not self.email_suggestions:
            messagebox.showwarning("No Data", "No email suggestions to apply.")
            return
        
        try:
            # Disable buttons during processing
            for widget in self.editing_frame.winfo_children():
                if isinstance(widget, ttk.Button):
                    widget.config(state=tk.DISABLED)
            
            self.status_var.set("Applying categorization to Outlook...")
            self.root.update()
            
            # Apply categorization using existing logic
            def confirmation_callback(email_count):
                return messagebox.askyesno("Confirm Application", 
                                         f"Apply categorization to {email_count} emails in Outlook?")
            
            success_count, error_count = self.outlook_manager.apply_categorization_batch(
                self.email_suggestions, 
                confirmation_callback
            )
            
            # Record the batch processing
            categories_used = len(set(s['ai_suggestion'] for s in self.email_suggestions))
            self.ai_processor.record_batch_processing(success_count, error_count, categories_used)
            
            messagebox.showinfo("Complete", 
                              f"Categorization applied!\n\n"
                              f"✅ Successfully processed: {success_count}\n"
                              f"❌ Errors: {error_count}\n\n"
                              f"Check your Outlook categories to see the results.")
            
            self.status_var.set(f"✅ Categorization applied - {success_count} successful, {error_count} errors")
            
        except Exception as e:
            messagebox.showerror("Application Error", f"Failed to apply categorization:\n\n{str(e)}")
            self.status_var.set(f"❌ Failed to apply categorization: {str(e)}")
        finally:
            # Re-enable buttons
            for widget in self.editing_frame.winfo_children():
                if isinstance(widget, ttk.Button):
                    widget.config(state=tk.NORMAL)
    
    def proceed_to_summary(self):
        """Proceed to summary tab"""
        # Enable summary tab
        self.notebook.tab(2, state="normal")
        
        # Switch to summary tab
        self.notebook.select(2)
        
        self.status_var.set("Ready to generate summary")
    
    def generate_summary(self):
        """Generate and display summary"""
        try:
            self.generate_summary_btn.config(state=tk.DISABLED)
            self.status_var.set("Generating summary...")
            
            # Generate summary sections
            self.summary_sections = self.summary_generator.build_summary_sections(self.action_items_data)
            
            # Create text summary for display
            summary_text = self.create_summary_text(self.summary_sections)
            
            # Update summary display
            self.summary_text.config(state=tk.NORMAL)
            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(tk.END, summary_text)
            self.summary_text.config(state=tk.DISABLED)
            
            # Save HTML summary
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.saved_summary_path = self.summary_generator.save_focused_summary(self.summary_sections, timestamp)
            
            self.status_var.set("✅ Summary generated successfully")
            
        except Exception as e:
            messagebox.showerror("Summary Error", f"Failed to generate summary:\n\n{str(e)}")
            self.status_var.set(f"❌ Summary generation failed: {str(e)}")
        finally:
            self.generate_summary_btn.config(state=tk.NORMAL)
    
    def create_summary_text(self, summary_sections):
        """Create text representation of summary for display"""
        text_parts = []
        
        # Overview
        total_items = sum(len(items) for items in summary_sections.values())
        high_priority = len(summary_sections.get('required_actions', []))
        
        text_parts.append("📊 SUMMARY OVERVIEW")
        text_parts.append("=" * 50)
        text_parts.append(f"Total actionable items: {total_items}")
        text_parts.append(f"High priority (required actions): {high_priority}")
        text_parts.append("")
        
        # Sections
        sections = [
            ('🔴 REQUIRED ACTION ITEMS (ME)', 'required_actions'),
            ('👥 TEAM ACTION ITEMS', 'team_actions'),
            ('📝 OPTIONAL ACTION ITEMS', 'optional_actions'),
            ('💼 JOB LISTINGS', 'job_listings'),
            ('🎪 OPTIONAL EVENTS', 'optional_events'),
            ('📋 FYI NOTICES', 'fyi_notices'),
            ('📰 NEWSLETTERS SUMMARY', 'newsletters')
        ]
        
        for title, section_key in sections:
            items = summary_sections.get(section_key, [])
            if not items:
                continue
            
            count = len(items)
            title_with_count = f"{title} ({count})"
            text_parts.append(title_with_count)
            text_parts.append("-" * len(title_with_count))
            
            for i, item in enumerate(items, 1):
                if section_key == 'fyi_notices':
                    text_parts.append(f"• {item['summary']} ({item['sender']})")
                elif section_key == 'newsletters':
                    if len(items) > 1:
                        text_parts.append(f"{i}. {item['summary']}")
                    else:
                        text_parts.append(f"**{item['subject']}** ({item['sender']}, {item['date']})")
                        text_parts.append(f"{item['summary']}")
                else:
                    text_parts.append(f"{i}. **{item['subject']}**")
                    text_parts.append(f"   From: {item['sender']}")
                    
                    if section_key in ['required_actions', 'team_actions']:
                        text_parts.append(f"   Due: {item['due_date']}")
                        text_parts.append(f"   Action: {item.get('action_required', 'Review email')}")
                        text_parts.append(f"   Why: {item['explanation']}")
                    elif section_key == 'optional_actions':
                        text_parts.append(f"   What: {item.get('action_required', 'Provide feedback')}")
                        text_parts.append(f"   Why relevant: {item['why_relevant']}")
                        text_parts.append(f"   Context: {item['explanation']}")
                    elif section_key == 'job_listings':
                        text_parts.append(f"   Match: {item['qualification_match']}")
                        text_parts.append(f"   Due: {item['due_date']}")
                    elif section_key == 'optional_events':
                        text_parts.append(f"   Date: {item['date']}")
                        text_parts.append(f"   Why relevant: {item['relevance']}")
                    
                    if item.get('links'):
                        link_type = 'Apply' if section_key == 'job_listings' else 'Register' if section_key == 'optional_events' else 'Link'
                        for link in item['links'][:2]:
                            text_parts.append(f"   {link_type}: {link}")
                
                text_parts.append("")
            
            text_parts.append("")
        
        return "\n".join(text_parts)
    
    def open_summary_in_browser(self):
        """Open summary in browser"""
        if hasattr(self, 'saved_summary_path') and self.saved_summary_path:
            try:
                file_path = os.path.abspath(self.saved_summary_path)
                webbrowser.open(f'file://{file_path}')
                self.status_var.set("✅ Summary opened in browser")
            except Exception as e:
                messagebox.showerror("Browser Error", f"Failed to open summary in browser:\n\n{str(e)}")
        else:
            messagebox.showwarning("No Summary", "Please generate a summary first.")
    
    def start_new_session(self):
        """Start a new processing session"""
        result = messagebox.askyesno("New Session", 
                                   "Start a new email processing session?\n\n"
                                   "This will reset all current data and return to the processing tab.")
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
            
            # Disable tabs 2 and 3
            self.notebook.tab(1, state="disabled")
            self.notebook.tab(2, state="disabled")
            
            # Switch to processing tab
            self.notebook.select(0)
            
            self.status_var.set("Ready for new processing session")
    
    def run(self):
        """Start the GUI main loop"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n🛑 GUI closed by user")


def main():
    """Main function"""
    print("🤖 AI-POWERED EMAIL MANAGEMENT SYSTEM - UNIFIED GUI")
    print("=" * 60)
    
    try:
        app = UnifiedEmailGUI()
        app.run()
    except Exception as e:
        print(f"❌ Failed to start GUI: {e}")
        messagebox.showerror("Startup Error", f"Failed to start the application:\n\n{str(e)}")


if __name__ == "__main__":
    main()
