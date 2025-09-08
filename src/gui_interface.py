#!/usr/bin/env python3
"""
GUI Interface - Desktop GUI for viewing and modifying AI email suggestions
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
import threading


class EmailSuggestionGUI:
    """Desktop GUI for viewing and modifying AI email suggestions"""
    
    def __init__(self, ai_processor, outlook_manager, summary_generator):
        self.ai_processor = ai_processor
        self.outlook_manager = outlook_manager
        self.summary_generator = summary_generator
        self.email_suggestions = []
        self.action_items_data = {}
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("AI Email Management - Suggestion Editor")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Configure styles
        self.setup_styles()
        
        # Create GUI components
        self.create_widgets()
        
        # Track if changes were made
        self.changes_made = False
        
    def setup_styles(self):
        """Configure GUI styles"""
        style = ttk.Style()
        
        # Configure treeview colors for better readability
        style.configure("Treeview", rowheight=60)
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        
        # Configure button styles
        style.configure("Action.TButton", font=('Arial', 9, 'bold'))
        
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🤖 AI Email Suggestions Editor", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Create treeview for email list
        self.create_email_treeview(main_frame)
        
        # Create details panel
        self.create_details_panel(main_frame)
        
        # Create control buttons
        self.create_control_buttons(main_frame)
        
        # Create status bar
        self.create_status_bar(main_frame)
        
    def create_email_treeview(self, parent):
        """Create the email list treeview"""
        # Frame for treeview and scrollbar
        tree_frame = ttk.Frame(parent)
        tree_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Create treeview
        columns = ('Subject', 'From', 'Category', 'Date')
        self.email_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
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
        
    def create_control_buttons(self, parent):
        """Create control buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, columnspan=3, pady=(10, 0))
        
        # Summary and actions
        ttk.Button(button_frame, text="📊 Regenerate Summary", 
                  command=self.regenerate_summary).grid(row=0, column=0, padx=5)
        
        ttk.Button(button_frame, text="📈 Show Accuracy Report", 
                  command=self.show_accuracy_report).grid(row=0, column=1, padx=5)
        
        ttk.Button(button_frame, text="✅ Apply to Outlook", 
                  command=self.apply_to_outlook).grid(row=0, column=2, padx=5)
        
        ttk.Button(button_frame, text="🔄 Refresh List", 
                  command=self.refresh_email_list).grid(row=0, column=3, padx=5)
        
        ttk.Button(button_frame, text="✅ Done", 
                  command=self.close_gui).grid(row=0, column=4, padx=5)
        
    def create_status_bar(self, parent):
        """Create status bar"""
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Select an email to edit its classification")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def get_category_display_names(self):
        """Get user-friendly category names"""
        category_map = {
            'required_personal_action': 'Required Personal Action',
            'team_action': 'Team Action',
            'optional_action': 'Optional Action',
            'job_listing': 'Job Listing',
            'optional_event': 'Optional Event',
            'spam_to_delete': 'Spam/Delete',
            'general_information': 'General Information'
        }
        return [category_map.get(cat, cat.replace('_', ' ').title()) 
                for cat in self.ai_processor.get_available_categories()]
    
    def get_category_internal_name(self, display_name):
        """Convert display name back to internal category name"""
        category_map = {
            'Required Personal Action': 'required_personal_action',
            'Team Action': 'team_action',
            'Optional Action': 'optional_action',
            'Job Listing': 'job_listing',
            'Optional Event': 'optional_event',
            'Spam/Delete': 'spam_to_delete',
            'General Information': 'general_information'
        }
        return category_map.get(display_name, display_name.lower().replace(' ', '_'))
    
    def load_email_suggestions(self, email_suggestions, action_items_data):
        """Load email suggestions into the GUI"""
        self.email_suggestions = email_suggestions
        self.action_items_data = action_items_data
        self.refresh_email_list()
        
    def refresh_email_list(self):
        """Refresh the email list in the treeview"""
        # Clear existing items
        for item in self.email_tree.get_children():
            self.email_tree.delete(item)
            
        # Add email suggestions with thread grouping
        for i, suggestion_data in enumerate(self.email_suggestions):
            email = suggestion_data['email_object']
            suggestion = suggestion_data['ai_suggestion']
            thread_data = suggestion_data.get('thread_data', {})
            thread_count = thread_data.get('thread_count', 1)
            
            # Format data for display
            if thread_count > 1:
                # Thread with multiple emails - show as conversation
                topic = thread_data.get('topic', email.Subject)
                participants = thread_data.get('participants', [email.SenderName])
                latest_date = thread_data.get('latest_date', email.ReceivedTime)
                
                # Create subject showing it's a conversation
                subject = f"🧵 {topic}" if len(topic) <= 45 else f"🧵 {topic[:42]}..."
                sender = f"{len(participants)} participants" if len(participants) > 1 else participants[0]
                if len(sender) > 30:
                    sender = sender[:27] + "..."
                category = suggestion.replace('_', ' ').title()
                date = latest_date.strftime('%Y-%m-%d %H:%M')
                
                # Insert thread parent
                thread_item = self.email_tree.insert('', tk.END, values=(subject, sender, category, date))
                
                # Add individual emails as children (for reference, but collapsed by default)
                for j, thread_email in enumerate(thread_data.get('all_emails', [email])):
                    child_subject = thread_email.Subject if len(thread_email.Subject) <= 45 else thread_email.Subject[:42] + "..."
                    child_sender = thread_email.SenderName if len(thread_email.SenderName) <= 30 else thread_email.SenderName[:27] + "..."
                    child_date = thread_email.ReceivedTime.strftime('%Y-%m-%d %H:%M')
                    child_item = self.email_tree.insert(thread_item, tk.END, 
                                                      values=(f"  └ {child_subject}", child_sender, "", child_date))
                
            else:
                # Single email
                subject = email.Subject if len(email.Subject) <= 50 else email.Subject[:47] + "..."
                sender = email.SenderName if len(email.SenderName) <= 30 else email.SenderName[:27] + "..."
                category = suggestion.replace('_', ' ').title()
                date = email.ReceivedTime.strftime('%Y-%m-%d %H:%M')
                
                # Insert single email
                self.email_tree.insert('', tk.END, values=(subject, sender, category, date))
            
        self.status_var.set(f"Loaded {len(self.email_suggestions)} conversations ({sum(s.get('thread_data', {}).get('thread_count', 1) for s in self.email_suggestions)} total emails)")
        
    def on_email_select(self, event):
        """Handle email selection in treeview"""
        selection = self.email_tree.selection()
        if not selection:
            return
            
        # Get selected item
        item = selection[0]
        
        # Check if this is a child item (individual email in thread)
        parent = self.email_tree.parent(item)
        if parent:
            # This is a child item, get the parent index instead
            parent_children = self.email_tree.get_children('')
            index = None
            for i, parent_item in enumerate(parent_children):
                if parent_item == parent:
                    index = i
                    break
        else:
            # This is a top-level item, get its index
            index = None
            top_level_items = self.email_tree.get_children('')
            for i, top_item in enumerate(top_level_items):
                if top_item == item:
                    index = i
                    break
        
        if index is not None and index < len(self.email_suggestions):
            self.display_email_details(index)
            
    def display_email_details(self, index):
        """Display email details in the details panel"""
        self.current_email_index = index
        suggestion_data = self.email_suggestions[index]
        email = suggestion_data['email_object']
        suggestion = suggestion_data['ai_suggestion']
        thread_data = suggestion_data.get('thread_data', {})
        thread_count = thread_data.get('thread_count', 1)
        
        # Update email details
        if thread_count > 1:
            # Show conversation details
            topic = thread_data.get('topic', email.Subject)
            participants = thread_data.get('participants', [email.SenderName])
            latest_date = thread_data.get('latest_date', email.ReceivedTime)
            
            self.subject_var.set(f"Conversation: {topic}")
            self.from_var.set(f"{len(participants)} participants: {', '.join(participants[:2])}{'...' if len(participants) > 2 else ''}")
            self.date_var.set(f"Latest: {latest_date.strftime('%Y-%m-%d %H:%M')}")
            
            # Create preview showing thread summary
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)
            
            preview_content = f"🧵 CONVERSATION THREAD ({thread_count} emails)\n\n"
            preview_content += f"Topic: {topic}\n"
            preview_content += f"Participants: {', '.join(participants)}\n\n"
            
            # Show latest email content as preview
            try:
                body = self.outlook_manager.get_email_body(email)
                preview_content += f"Latest email preview:\n{body[:300]}"
                if len(body) > 300:
                    preview_content += "\n\n[... truncated ...]"
            except Exception as e:
                preview_content += f"Error loading preview: {e}"
                
            # Add thread summary
            all_emails = thread_data.get('all_emails', [email])
            if len(all_emails) > 1:
                preview_content += f"\n\n--- THREAD EMAILS ---\n"
                for i, thread_email in enumerate(all_emails[-3:], 1):  # Show last 3 emails
                    preview_content += f"{i}. {thread_email.ReceivedTime.strftime('%m/%d %H:%M')} - {thread_email.SenderName}: {thread_email.Subject[:50]}\n"
            
            self.preview_text.insert(tk.END, preview_content)
        else:
            # Show single email details
            self.subject_var.set(email.Subject)
            self.from_var.set(email.SenderName)
            self.date_var.set(email.ReceivedTime.strftime('%Y-%m-%d %H:%M'))
            
            # Update preview
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)
            
            try:
                body = self.outlook_manager.get_email_body(email)
                preview = body[:500] if body else "No preview available"
                if len(body) > 500:
                    preview += "\n\n[... truncated ...]"
                self.preview_text.insert(tk.END, preview)
            except Exception as e:
                self.preview_text.insert(tk.END, f"Error loading preview: {e}")
        
        self.preview_text.config(state=tk.DISABLED)
        
        # Set category
        display_name = suggestion.replace('_', ' ').title()
        self.category_var.set(display_name)
        self.original_category = suggestion
        
        # Clear explanation and disable apply button
        self.explanation_var.set("")
        self.apply_btn.config(state=tk.DISABLED)
        
        thread_info = f" ({thread_count} emails)" if thread_count > 1 else ""
        self.status_var.set(f"Selected: {email.Subject[:40]}{'...' if len(email.Subject) > 40 else ''}{thread_info}")
        
    def on_category_change(self, event):
        """Handle category change in combobox"""
        if self.current_email_index is None:
            return
            
        new_display_name = self.category_var.get()
        new_category = self.get_category_internal_name(new_display_name)
        
        # Enable apply button if category changed
        if new_category != self.original_category:
            self.apply_btn.config(state=tk.NORMAL)
            self.status_var.set(f"Category changed to '{new_display_name}' - Add reason and apply")
        else:
            self.apply_btn.config(state=tk.DISABLED)
            self.status_var.set("Category unchanged")
            
    def apply_category_change(self):
        """Apply the category change"""
        if self.current_email_index is None:
            return
            
        new_display_name = self.category_var.get()
        new_category = self.get_category_internal_name(new_display_name)
        explanation = self.explanation_var.get().strip()
        
        if not explanation:
            messagebox.showwarning("Missing Information", 
                                 "Please provide a reason for changing the classification.")
            return
            
        if new_category == self.original_category:
            messagebox.showinfo("No Change", "The category is the same as the original.")
            return
            
        try:
            # Apply the change using existing logic
            success = self.edit_suggestion(self.current_email_index + 1, new_category, explanation)
            
            if success:
                self.changes_made = True
                
                # Update the treeview - need to handle thread structure
                top_level_items = self.email_tree.get_children('')
                if self.current_email_index < len(top_level_items):
                    item = top_level_items[self.current_email_index]
                    values = list(self.email_tree.item(item, 'values'))
                    values[2] = new_display_name  # Update category column
                    self.email_tree.item(item, values=values)
                
                # Update original category
                self.original_category = new_category
                
                # Clear explanation and disable apply button
                self.explanation_var.set("")
                self.apply_btn.config(state=tk.DISABLED)
                
                self.status_var.set("✅ Category updated successfully!")
                
                # Show success message
                messagebox.showinfo("Success", f"Email classification changed to '{new_display_name}'")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update classification:\n{str(e)}")
            self.status_var.set(f"❌ Error: {str(e)}")
            
    def edit_suggestion(self, email_index, new_category, user_explanation):
        """Edit a specific email suggestion (reuse existing logic)"""
        if not self.email_suggestions:
            messagebox.showerror("Error", "No email suggestions available.")
            return False
            
        if email_index < 1 or email_index > len(self.email_suggestions):
            messagebox.showerror("Error", "Invalid email number.")
            return False
            
        # Get the email suggestion
        suggestion_data = self.email_suggestions[email_index - 1]
        email = suggestion_data['email_object']
        old_category = suggestion_data['ai_suggestion']
        
        if new_category not in self.ai_processor.get_available_categories():
            messagebox.showerror("Error", f"Invalid category. Available: {', '.join(self.ai_processor.get_available_categories())}")
            return False
            
        # Update the suggestion
        suggestion_data['ai_suggestion'] = new_category
        
        # Remove from old category in action_items_data
        self._remove_from_action_data(email, old_category)
        
        # Add to new category in action_items_data  
        self._add_to_action_data(email, new_category)
        
        # Record the modification
        email_data = {
            'subject': email.Subject,
            'sender': email.SenderName,
            'date': email.ReceivedTime.strftime('%Y-%m-%d %H:%M'),
            'body': self.outlook_manager.get_email_body(email)
        }
        self.ai_processor.record_suggestion_modification(email_data, old_category, new_category, user_explanation)
        
        return True
        
    def _remove_from_action_data(self, email, category):
        """Remove email from action_items_data category"""
        if category in self.action_items_data:
            # Remove entries that match this email
            self.action_items_data[category] = [
                item for item in self.action_items_data[category]
                if item['email_object'].Subject != email.Subject or 
                   item['email_object'].SenderName != email.SenderName
            ]
    
    def _add_to_action_data(self, email, new_category):
        """Add email to action_items_data in new category"""
        if new_category not in self.action_items_data:
            self.action_items_data[new_category] = []
            
        # Process the email for the new category (simplified version)
        if new_category in ['required_personal_action', 'team_action', 'optional_action']:
            email_content = {
                'subject': email.Subject,
                'sender': email.SenderName,
                'date': email.ReceivedTime.strftime('%Y-%m-%d %H:%M'),
                'body': self.outlook_manager.get_email_body(email)
            }
            
            context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}"
            action_details = self.ai_processor.extract_action_item_details(email_content, context)
            
            self.action_items_data[new_category].append({
                'email_object': email,
                'action_details': action_details
            })
            
        # For other categories, just add basic entry
        else:
            self.action_items_data[new_category].append({
                'email_object': email,
                'thread_data': {}
            })
            
    def regenerate_summary(self):
        """Regenerate summary after changes"""
        if not self.action_items_data:
            messagebox.showwarning("No Data", "No action items data available.")
            return
            
        try:
            # Generate focused summary using updated data
            summary_sections = self.summary_generator.build_summary_sections(self.action_items_data)
            
            # Save updated summary
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.summary_generator.save_focused_summary(summary_sections, timestamp)
            
            messagebox.showinfo("Success", "Summary regenerated and saved successfully!")
            self.status_var.set("✅ Summary regenerated successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to regenerate summary:\n{str(e)}")
            self.status_var.set(f"❌ Summary regeneration failed: {str(e)}")
            
    def show_accuracy_report(self):
        """Show accuracy report in a new window"""
        try:
            # Create new window
            report_window = tk.Toplevel(self.root)
            report_window.title("📊 Accuracy Report")
            report_window.geometry("600x400")
            
            # Create text widget with scrollbar
            text_frame = ttk.Frame(report_window, padding="10")
            text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            report_window.columnconfigure(0, weight=1)
            report_window.rowconfigure(0, weight=1)
            text_frame.columnconfigure(0, weight=1)
            text_frame.rowconfigure(0, weight=1)
            
            report_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, width=70, height=20)
            report_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Get report data (capture print output)
            import io
            import sys
            
            # Capture the report output
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            try:
                self.ai_processor.show_accuracy_report(days_back=14)
                report_content = captured_output.getvalue()
            finally:
                sys.stdout = old_stdout
                
            if report_content:
                report_text.insert(tk.END, report_content)
            else:
                report_text.insert(tk.END, "No accuracy data available yet.\nThis might be the first run or there's insufficient data.")
                
            report_text.config(state=tk.DISABLED)
            
            # Close button
            ttk.Button(text_frame, text="Close", 
                      command=report_window.destroy).grid(row=1, column=0, pady=(10, 0))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate accuracy report:\n{str(e)}")
            
    def apply_to_outlook(self):
        """Apply categorization to Outlook"""
        if not self.email_suggestions:
            messagebox.showwarning("No Data", "No email suggestions available.")
            return
            
        # Confirm with user
        result = messagebox.askyesno("Apply to Outlook",
                                    f"This will organize {len(self.email_suggestions)} emails based on AI suggestions.\n\n"
                                    "Actions will include:\n"
                                    "• Moving emails to category folders under Inbox\n"  
                                    "• Adding color categories as backup\n"
                                    "• Moving spam/irrelevant emails to 'ai_deleted' folder\n\n"
                                    "Do you want to proceed?")
        
        if not result:
            return
            
        try:
            # Disable the button during processing
            for child in self.root.winfo_children():
                if isinstance(child, ttk.Frame):
                    for widget in child.winfo_children():
                        if isinstance(widget, ttk.Button) and "Apply to Outlook" in str(widget.cget('text')):
                            widget.config(state=tk.DISABLED)
            
            self.status_var.set("Applying categorization to Outlook...")
            self.root.update()
            
            # Apply categorization using existing logic
            def confirmation_callback(email_count):
                return True  # Already confirmed above
                
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
                              f"❌ Errors: {error_count}")
            
            self.status_var.set(f"✅ Applied to Outlook: {success_count} success, {error_count} errors")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply categorization:\n{str(e)}")
            self.status_var.set(f"❌ Error applying to Outlook: {str(e)}")
            
        finally:
            # Re-enable the button
            for child in self.root.winfo_children():
                if isinstance(child, ttk.Frame):
                    for widget in child.winfo_children():
                        if isinstance(widget, ttk.Button) and "Apply to Outlook" in str(widget.cget('text')):
                            widget.config(state=tk.NORMAL)
            
    def close_gui(self):
        """Close the GUI"""
        if self.changes_made:
            result = messagebox.askyesno("Unsaved Changes",
                                       "You have made changes to email classifications.\n"
                                       "Are you sure you want to close?")
            if not result:
                return
                
        self.root.destroy()
        
    def run(self):
        """Run the GUI main loop"""
        self.root.mainloop()


class GuiInterface:
    """GUI-based interface that can replace the console UserInterface"""
    
    def __init__(self, ai_processor, outlook_manager, summary_generator):
        self.ai_processor = ai_processor
        self.outlook_manager = outlook_manager  
        self.summary_generator = summary_generator
        self.email_suggestions = []
        self.action_items_data = {}
        
    def get_max_emails_from_user(self, default=50, max_limit=200):
        """Get max emails using a simple dialog (or use default)"""
        # For now, just return default to keep it simple
        # Could add a dialog later if needed
        return default
        
    def offer_editing_options(self):
        """Launch GUI for editing options"""
        try:
            gui = EmailSuggestionGUI(self.ai_processor, self.outlook_manager, self.summary_generator)
            gui.load_email_suggestions(self.email_suggestions, self.action_items_data)
            
            print("\n🖥️  Launching GUI for email suggestion editing...")
            print("   Close the GUI window when you're finished editing.")
            
            gui.run()
            
            # Update our data from the GUI
            self.email_suggestions = gui.email_suggestions
            self.action_items_data = gui.action_items_data
            
            print("✅ GUI session completed!")
            
        except Exception as e:
            print(f"❌ GUI launch failed: {e}")
            print("Falling back to console interface...")
            # Could fall back to console interface here
            
    def set_email_suggestions(self, email_suggestions):
        """Set the email suggestions"""
        self.email_suggestions = email_suggestions
        
    def set_action_items_data(self, action_items_data):
        """Set the action items data"""
        self.action_items_data = action_items_data
