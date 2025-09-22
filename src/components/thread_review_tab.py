#!/usr/bin/env python3
"""
Thread Review Tab Component - Accordion-style thread grouping for email review
"""

# Standard library imports
import re
import webbrowser
from datetime import datetime

# Third-party imports
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox


class ThreadReviewTab:
    def __init__(self, parent_frame, controller):
        self.parent_frame = parent_frame
        self.controller = controller
        self.current_thread_index = None
        self.current_email_index = None
        self.expanded_threads = set()
        self.thread_frames = {}
        self.setup_ui()

    def setup_ui(self):
        """Create the thread-based review tab UI"""
        main_frame = ttk.Frame(self.parent_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Header
        self.create_header(main_frame)
        
        # Thread list with accordion view
        self.create_thread_accordion(main_frame)
        
        # Thread analysis panel
        self.create_thread_analysis_panel(main_frame)
        
        # Control buttons
        self.create_control_buttons(main_frame)

    def create_header(self, main_frame):
        """Create header with thread statistics"""
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.stats_label = ttk.Label(
            header_frame, 
            text="📧 Thread View - Loading...", 
            font=('Segoe UI', 11, 'bold')
        )
        self.stats_label.pack(side=tk.LEFT)
        
        # View toggle button
        self.toggle_all_btn = ttk.Button(
            header_frame,
            text="🔽 Expand All",
            command=self.toggle_all_threads
        )
        self.toggle_all_btn.pack(side=tk.RIGHT)

    def create_thread_accordion(self, main_frame):
        """Create scrollable accordion view for threads"""
        # Frame for thread list
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Scrollable canvas for threads
        self.canvas = tk.Canvas(list_frame, bg='white')
        self.scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Configure scrollable frame to expand
        self.scrollable_frame.columnconfigure(0, weight=1)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Bind canvas resize to adjust window width
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind mousewheel to canvas
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

    def create_thread_analysis_panel(self, main_frame):
        """Create thread analysis and reclassification panel"""
        analysis_frame = ttk.LabelFrame(main_frame, text="Thread Analysis & Actions", padding="10")
        analysis_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        analysis_frame.columnconfigure(0, weight=1)
        analysis_frame.rowconfigure(2, weight=1)
        
        # Thread category selection
        ttk.Label(analysis_frame, text="Thread Category:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.thread_category_var = tk.StringVar()
        self.thread_category_combo = ttk.Combobox(
            analysis_frame,
            textvariable=self.thread_category_var,
            values=self.get_category_names(),
            state="readonly"
        )
        self.thread_category_combo.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2, padx=(0, 0))
        self.thread_category_combo.bind('<<ComboboxSelected>>', self.on_thread_category_change)
        
        # Thread actions
        actions_frame = ttk.Frame(analysis_frame)
        actions_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.reclassify_thread_btn = ttk.Button(
            actions_frame,
            text="🔄 Reclassify Entire Thread",
            command=self.reclassify_entire_thread,
            state=tk.DISABLED
        )
        self.reclassify_thread_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.thread_summary_btn = ttk.Button(
            actions_frame,
            text="📋 Generate Thread Summary",
            command=self.generate_thread_summary,
            state=tk.DISABLED
        )
        self.thread_summary_btn.pack(side=tk.LEFT)
        
        # Thread analysis display
        self.analysis_text = scrolledtext.ScrolledText(
            analysis_frame,
            height=12,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg='#f8f9fa'
        )
        self.analysis_text.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
        self.configure_analysis_text_tags()

    def create_control_buttons(self, main_frame):
        """Create control buttons"""
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(15, 0))
        
        ttk.Button(
            button_frame,
            text="Apply to Outlook",
            command=self.controller.apply_to_outlook
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Generate Summary",
            command=self.controller.proceed_to_summary
        ).pack(side=tk.LEFT, padx=5)

    def populate_threads(self, email_suggestions):
        """Populate the accordion view with thread data"""
        # Clear existing threads
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.thread_frames = {}
        self.expanded_threads = set()
        
        # Group suggestions by thread
        thread_groups = self.group_suggestions_by_thread(email_suggestions)
        
        # Update statistics
        total_threads = len(thread_groups)
        total_emails = len(email_suggestions)
        multi_email_threads = len([g for g in thread_groups.values() if len(g['emails']) > 1])
        
        self.stats_label.config(
            text=f"🧵 {total_threads} threads ({multi_email_threads} multi-email) • {total_emails} total emails"
        )
        
        # Create thread accordion items
        for i, (thread_id, thread_data) in enumerate(thread_groups.items()):
            self.create_thread_accordion_item(i, thread_id, thread_data)
        
        # Auto-select and expand the first thread if any threads exist
        if thread_groups:
            first_thread_id = list(thread_groups.keys())[0]
            self.toggle_thread(first_thread_id)  # This will expand and select the first thread

    def group_suggestions_by_thread(self, email_suggestions):
        """Group email suggestions by thread"""
        thread_groups = {}
        
        for suggestion in email_suggestions:
            thread_data = suggestion.get('thread_data', {})
            thread_id = thread_data.get('conversation_id', f"single_{suggestion.get('entry_id', 'unknown')}")
            
            if thread_id not in thread_groups:
                thread_groups[thread_id] = {
                    'emails': [],
                    'topic': thread_data.get('topic', 'Unknown Thread'),
                    'participants': thread_data.get('participants', []),
                    'thread_count': thread_data.get('thread_count', 1),
                    'has_complete_thread': thread_data.get('has_complete_thread', False),
                    'latest_date': thread_data.get('latest_date'),
                    'ai_category': suggestion.get('ai_suggestion', 'unknown')
                }
            
            thread_groups[thread_id]['emails'].append(suggestion)
        
        # Sort by latest date
        sorted_threads = dict(sorted(
            thread_groups.items(),
            key=lambda x: x[1]['latest_date'] if x[1]['latest_date'] else datetime.min,
            reverse=True
        ))
        
        return sorted_threads

    def create_thread_accordion_item(self, index, thread_id, thread_data):
        """Create a single thread accordion item"""
        # Main thread frame
        thread_frame = ttk.Frame(self.scrollable_frame, relief='solid', borderwidth=1, padding=5)
        thread_frame.grid(row=index, column=0, sticky=(tk.W, tk.E), pady=2, padx=5)
        thread_frame.columnconfigure(0, weight=1)  # Allow the frame to expand horizontally
        thread_frame.columnconfigure(1, weight=1)  # Both columns can expand
        
        # Configure the scrollable frame to expand this item
        self.scrollable_frame.rowconfigure(index, weight=0)  # Don't expand vertically
        
        self.thread_frames[thread_id] = {
            'main_frame': thread_frame,
            'index': index,
            'data': thread_data,
            'expanded': False
        }
        
        # Thread header (always visible)
        self.create_thread_header(thread_frame, thread_id, thread_data)

    def create_thread_header(self, parent_frame, thread_id, thread_data):
        """Create clickable thread header"""
        header_frame = ttk.Frame(parent_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        header_frame.columnconfigure(1, weight=1)
        
        # Expand/collapse button
        expand_btn = ttk.Button(
            header_frame,
            text="▶",
            width=3,
            command=lambda: self.toggle_thread(thread_id)
        )
        expand_btn.grid(row=0, column=0, padx=(0, 5))
        self.thread_frames[thread_id]['expand_btn'] = expand_btn
        
        # Thread info
        thread_count = thread_data['thread_count']
        participants = thread_data.get('participants', [])
        topic = thread_data['topic']
        
        if thread_count > 1:
            icon = "🧵"
            count_text = f"({thread_count} emails, {len(participants)} participants)"
        else:
            icon = "📧"
            count_text = f"(Single email)"
        
        info_text = f"{icon} {topic[:60]}" + ("..." if len(topic) > 60 else "")
        category = thread_data['ai_category'].replace('_', ' ').title()
        
        info_label = ttk.Label(
            header_frame,
            text=f"{info_text}\n{count_text} • Category: {category}",
            font=('Segoe UI', 9)
        )
        info_label.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Make header clickable
        header_frame.bind("<Button-1>", lambda e: self.toggle_thread(thread_id))
        info_label.bind("<Button-1>", lambda e: self.toggle_thread(thread_id))

    def toggle_thread(self, thread_id):
        """Toggle thread expansion"""
        thread_info = self.thread_frames[thread_id]
        
        if thread_info['expanded']:
            # Collapse
            thread_info['content_frame'].grid_remove()
            thread_info['expand_btn'].config(text="▶")
            thread_info['expanded'] = False
            self.expanded_threads.discard(thread_id)
        else:
            # Expand - always create fresh content when expanding
            self.create_thread_content(thread_id)
            
            thread_info['content_frame'].grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
            thread_info['expand_btn'].config(text="▼")
            thread_info['expanded'] = True
            self.expanded_threads.add(thread_id)
            
            # Select this thread for analysis
            self.select_thread_for_analysis(thread_id)
        
        # Update scroll region
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def create_thread_content(self, thread_id):
        """Create expanded content for a thread"""
        thread_info = self.thread_frames[thread_id]
        thread_data = thread_info['data']
        
        if 'content_frame' in thread_info and thread_info['content_frame'].winfo_exists():
            thread_info['content_frame'].destroy()
        
        content_frame = ttk.Frame(thread_info['main_frame'])
        content_frame.columnconfigure(0, weight=1)  # Allow content to expand horizontally
        thread_info['content_frame'] = content_frame
        
        # Create individual email items
        emails = thread_data['emails']
        for i, email_suggestion in enumerate(emails):
            self.create_email_item(content_frame, i, email_suggestion, thread_id)

    def create_email_item(self, parent_frame, email_index, email_suggestion, thread_id):
        """Create individual email item within thread"""
        email_frame = ttk.LabelFrame(parent_frame, text=f"Email {email_index + 1}", padding=5)
        email_frame.grid(row=email_index, column=0, sticky=(tk.W, tk.E), pady=2)
        email_frame.columnconfigure(1, weight=1)
        
        email_data = email_suggestion.get('email_data', {})
        ai_summary = email_suggestion.get('ai_summary', 'No summary')
        
        # Email header
        subject = email_data.get('subject', 'Unknown Subject')
        sender = email_data.get('sender_name', 'Unknown Sender')
        date = email_data.get('received_time', 'Unknown Date')
        
        if hasattr(date, 'strftime'):
            date_str = date.strftime('%m/%d/%Y %H:%M')
        else:
            date_str = str(date)
        
        header_text = f"From: {sender}\nSubject: {subject}\nDate: {date_str}"
        
        header_label = ttk.Label(email_frame, text=header_text, font=('Segoe UI', 8))
        header_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # AI Summary
        summary_label = ttk.Label(email_frame, text="AI Summary:", font=('Segoe UI', 8, 'bold'))
        summary_label.grid(row=1, column=0, sticky=tk.W)
        
        summary_text = ai_summary[:200] + "..." if len(ai_summary) > 200 else ai_summary
        summary_content_label = ttk.Label(email_frame, text=summary_text, wraplength=400, font=('Segoe UI', 8))
        summary_content_label.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0))

    def select_thread_for_analysis(self, thread_id):
        """Select thread for analysis panel"""
        self.current_thread_index = thread_id
        thread_data = self.thread_frames[thread_id]['data']
        
        # Enable thread action buttons
        self.reclassify_thread_btn.config(state=tk.NORMAL)
        self.thread_summary_btn.config(state=tk.NORMAL)
        
        # Update category selection
        current_category = thread_data['ai_category']
        display_mapping = self.get_display_name_mapping()
        display_category = display_mapping.get(current_category, current_category.replace('_', ' ').title())
        self.thread_category_var.set(display_category)
        
        # Generate and display thread analysis
        self.display_thread_analysis(thread_id, thread_data)

    def display_thread_analysis(self, thread_id, thread_data):
        """Display comprehensive thread analysis"""
        self.analysis_text.config(state=tk.NORMAL)
        self.analysis_text.delete(1.0, tk.END)
        
        emails = thread_data['emails']
        thread_count = thread_data['thread_count']
        participants = thread_data.get('participants', [])
        topic = thread_data['topic']
        
        # Thread overview
        self.analysis_text.insert(tk.END, "🧵 THREAD ANALYSIS\n\n", "header")
        
        self.analysis_text.insert(tk.END, f"Topic: {topic}\n", "bold")
        self.analysis_text.insert(tk.END, f"Emails in thread: {thread_count}\n")
        self.analysis_text.insert(tk.END, f"Participants: {', '.join(participants)}\n")
        self.analysis_text.insert(tk.END, f"Current category: {thread_data['ai_category'].replace('_', ' ').title()}\n\n")
        
        # Thread timeline
        self.analysis_text.insert(tk.END, "📅 THREAD TIMELINE:\n", "header")
        
        for i, email_suggestion in enumerate(emails):
            email_data = email_suggestion.get('email_data', {})
            date = email_data.get('received_time', 'Unknown')
            sender = email_data.get('sender_name', 'Unknown')
            subject = email_data.get('subject', 'Unknown')
            
            if hasattr(date, 'strftime'):
                date_str = date.strftime('%m/%d %H:%M')
            else:
                date_str = str(date)[:16]
            
            self.analysis_text.insert(tk.END, f"{i+1}. {date_str} - {sender}\n")
            self.analysis_text.insert(tk.END, f"   {subject}\n\n")
        
        # AI recommendations
        self.analysis_text.insert(tk.END, "🤖 AI ANALYSIS:\n", "header")
        
        # Use the first email's summary as thread summary
        if emails:
            thread_summary = emails[0].get('ai_summary', 'No analysis available')
            self.analysis_text.insert(tk.END, f"{thread_summary}\n\n")
        
        # Thread classification reasoning
        self.analysis_text.insert(tk.END, "🎯 CLASSIFICATION REASONING:\n", "header")
        if thread_count > 1:
            self.analysis_text.insert(tk.END, 
                "This classification applies to the entire conversation thread. "
                "All emails in the thread will be categorized together for consistency.\n"
            )
        else:
            self.analysis_text.insert(tk.END, 
                "This is a single-email thread. Classification applies to this email only.\n"
            )
        
        self.analysis_text.config(state=tk.DISABLED)

    def toggle_all_threads(self):
        """Toggle all threads expanded/collapsed"""
        if len(self.expanded_threads) > 0:
            # Collapse all
            for thread_id in list(self.expanded_threads):
                self.toggle_thread(thread_id)
            self.toggle_all_btn.config(text="🔽 Expand All")
        else:
            # Expand all
            for thread_id in self.thread_frames:
                if not self.thread_frames[thread_id]['expanded']:
                    self.toggle_thread(thread_id)
            self.toggle_all_btn.config(text="🔼 Collapse All")

    def on_thread_category_change(self, event=None):
        """Handle thread category change"""
        if self.current_thread_index:
            self.controller.on_thread_category_change(self.current_thread_index)

    def reclassify_entire_thread(self):
        """Reclassify entire thread with new category"""
        if self.current_thread_index:
            new_category = self.get_category_mapping().get(self.thread_category_var.get())
            if new_category:
                self.controller.reclassify_entire_thread(self.current_thread_index, new_category)

    def generate_thread_summary(self):
        """Generate comprehensive thread summary"""
        if self.current_thread_index:
            try:
                summary = self.controller.generate_thread_summary(self.current_thread_index)
                if summary:
                    messagebox.showinfo("Thread Summary", f"Thread summary generated successfully:\n\n{summary[:500]}...")
                else:
                    messagebox.showerror("Error", "Failed to generate thread summary - no summary returned")
            except Exception as e:
                messagebox.showerror("Error", f"Thread context failed error when generating thread summary:\n{str(e)}")
        else:
            messagebox.showwarning("Warning", "Please select a thread first")

    def get_category_names(self):
        """Get display names for categories"""
        return [
            "Required Personal Action",
            "Team Action", 
            "Optional Action", 
            "Job Listing",
            "Optional Event",
            "FYI Notice",
            "Newsletter",
            "Work Relevant",
            "General Information",
            "Spam To Delete"
        ]
    
    def get_category_mapping(self):
        """Map display names to internal category names"""
        return {
            "Required Personal Action": "required_personal_action",
            "Team Action": "team_action",
            "Optional Action": "optional_action", 
            "Job Listing": "job_listing",
            "Optional Event": "optional_event",
            "FYI Notice": "fyi",
            "Newsletter": "newsletter",
            "Work Relevant": "work_relevant",
            "General Information": "general_information",
            "Spam To Delete": "spam_to_delete"
        }
    
    def get_display_name_mapping(self):
        """Map internal category names to display names"""
        return {
            "required_personal_action": "Required Personal Action",
            "team_action": "Team Action",
            "optional_action": "Optional Action",
            "job_listing": "Job Listing", 
            "optional_event": "Optional Event",
            "fyi": "FYI Notice",
            "newsletter": "Newsletter",
            "work_relevant": "Work Relevant",
            "general_information": "General Information",
            "spam_to_delete": "Spam To Delete"
        }

    def configure_analysis_text_tags(self):
        """Configure text formatting tags"""
        self.analysis_text.tag_configure("header", 
                                        font=("Arial", 10, "bold"), 
                                        foreground="#2c3e50")
        
        self.analysis_text.tag_configure("bold", 
                                        font=("Arial", 9, "bold"))

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_canvas_configure(self, event):
        """Handle canvas resize to adjust scrollable frame width"""
        # Update the scrollable frame width to match canvas width
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def clear_selection(self):
        """Clear thread selection"""
        self.current_thread_index = None
        self.current_email_index = None
        self.reclassify_thread_btn.config(state=tk.DISABLED)
        self.thread_summary_btn.config(state=tk.DISABLED)
        self.thread_category_var.set("")
        
        if hasattr(self, 'analysis_text'):
            self.analysis_text.delete('1.0', tk.END)
