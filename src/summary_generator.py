#!/usr/bin/env python3
"""
Summary Generator - Handles summary creation, display, and file output
"""

import os
from jinja2 import Environment, FileSystemLoader


class SummaryGenerator:
    def __init__(self):
        # Constants for section configuration
        self.SECTION_KEYS = {
            'required_personal_action': 'required_actions',
            'team_action': 'team_actions', 
            'optional_action': 'optional_actions',
            'job_listing': 'job_listings',
            'optional_event': 'optional_events',
            'fyi': 'fyi_notices',
            'newsletter': 'newsletters'
        }
        
        # Initialize empty sections structure
        self.EMPTY_SECTIONS = {
            'required_actions': [],
            'team_actions': [],
            'optional_actions': [],
            'job_listings': [],
            'optional_events': [],
            'fyi_notices': [],
            'newsletters': []
        }
    
    def _extract_entry_id_and_check_duplicates(self, item_data, processed_entry_ids):
        """Extract entry ID from item data and check for duplicates"""
        email_obj = item_data.get('email_object')
        entry_id = None
        
        # Handle both email object and dictionary-only data
        if email_obj and hasattr(email_obj, 'EntryID'):
            entry_id = email_obj.EntryID
        elif not email_obj and item_data.get('thread_data', {}).get('entry_id'):
            entry_id = item_data['thread_data']['entry_id']
        
        # Check for duplicates
        if entry_id and entry_id in processed_entry_ids:
            return None, True  # None entry_id, is_duplicate=True
        
        if entry_id:
            processed_entry_ids.add(entry_id)
        
        return entry_id, False  # Return entry_id, is_duplicate=False
    
    def _extract_email_basic_data(self, item_data):
        """Extract subject, sender, and email object from item data with fallbacks"""
        email_obj = item_data.get('email_object')
        
        # Extract subject with fallbacks
        subject = item_data.get('email_subject')
        if not subject and email_obj:
            subject = getattr(email_obj, 'Subject', 'Unknown Subject')
        elif not subject:
            subject = 'Unknown Subject'
            
        # Extract sender with fallbacks
        sender = item_data.get('email_sender')
        if not sender and email_obj:
            sender = getattr(email_obj, 'SenderName', 'Unknown Sender')
        elif not sender:
            sender = 'Unknown Sender'
        
        return subject, sender, email_obj
    
    def _extract_date_string(self, item_data, email_obj=None):
        """Extract and format date string from item data or email object"""
        # Try item data first
        if 'email_date' in item_data and item_data['email_date']:
            date = item_data['email_date']
            if hasattr(date, 'strftime'):
                return date.strftime('%Y-%m-%d')
            else:
                return str(date)[:10]
        
        # Fallback to email object
        if email_obj and hasattr(email_obj, 'ReceivedTime'):
            return email_obj.ReceivedTime.strftime('%Y-%m-%d')
        
        return 'Unknown'
    
    def _build_action_item(self, item_data, action_details, entry_id, priority=1):
        """Build a standardized action item dictionary"""
        subject, sender, _ = self._extract_email_basic_data(item_data)
        
        return {
            'subject': subject,
            'sender': sender,
            'due_date': action_details.get('due_date', 'No specific deadline'),
            'action_required': action_details.get('action_required', 'Review email'),
            'explanation': action_details.get('explanation', 'Details in email'),
            'links': action_details.get('links', []),
            'priority': priority,
            '_entry_id': entry_id
        }
    
    def _process_section_items(self, action_items_data, section_name, processed_entry_ids, ai_processor=None):
        """Generic method to process items for any section type"""
        if section_name not in action_items_data:
            return []
        
        items = []
        for item_data in action_items_data[section_name]:
            # Check for duplicates
            entry_id, is_duplicate = self._extract_entry_id_and_check_duplicates(item_data, processed_entry_ids)
            if is_duplicate:
                continue
            
            # Build item based on section type
            item = self._build_section_item(section_name, item_data, entry_id, ai_processor)
            if item:
                items.append(item)
        
        return items
    
    def _build_section_item(self, section_name, item_data, entry_id, ai_processor=None):
        """Build item dictionary based on section type"""
        subject, sender, email_obj = self._extract_email_basic_data(item_data)
        
        if section_name == 'required_personal_action':
            action_details = item_data.get('action_details', {})
            return self._build_action_item(item_data, action_details, entry_id, priority=1)
        
        elif section_name == 'team_action':
            action_details = item_data.get('action_details', {})
            item = self._build_action_item(item_data, action_details, entry_id, priority=2)
            
            # Add team action specific fields
            if ai_processor:
                completion_status, completion_note = self._check_team_action_completion(item_data, ai_processor)
                item['completion_status'] = completion_status
                if completion_note:
                    item['completion_note'] = completion_note
            
            return item
        
        elif section_name == 'optional_action':
            action_details = item_data.get('action_details', {})
            return self._build_action_item(item_data, action_details, entry_id, priority=3)
        
        elif section_name == 'job_listing':
            # Job listings only process if email_obj exists (legacy constraint)
            if not email_obj or not hasattr(email_obj, 'EntryID'):
                return None
            
            return {
                'subject': subject,
                'sender': sender,
                'qualification_match': item_data.get('qualification_match', 'No qualification analysis available'),
                'links': item_data.get('links', []),
                'due_date': item_data.get('due_date', 'No deadline specified'),
                '_entry_id': entry_id
            }
        
        elif section_name == 'optional_event':
            # Optional events only process if email_obj exists (legacy constraint)
            if not email_obj or not hasattr(email_obj, 'EntryID'):
                return None
            
            return {
                'subject': subject,
                'sender': sender,
                'date': item_data.get('date', item_data.get('event_date', 'Unknown')),
                'relevance': item_data.get('relevance', 'Professional development opportunity'),
                'links': item_data.get('links', []),
                '_entry_id': entry_id
            }
        
        elif section_name == 'fyi':
            date_str = self._extract_date_string(item_data, email_obj)
            
            return {
                'subject': subject,
                'sender': sender,
                'date': date_str,
                'summary': item_data.get('summary', 'No summary available'),
                '_entry_id': entry_id
            }
        
        elif section_name == 'newsletter':
            date_str = self._extract_date_string(item_data, email_obj)
            
            return {
                'subject': subject,
                'sender': sender,
                'date': date_str,
                'summary': item_data.get('summary', 'No summary available'),
                '_entry_id': entry_id
            }
        
        return None
    
    def _ai_detect_duplicate_intent(self, new_item, existing_items, ai_processor=None):
        """Use AI to detect if new item is a duplicate of existing items"""
        if not ai_processor or not existing_items:
            return False, None
        
        try:
            # Load the duplicate detection prompt using ai_processor's method
            import os
            prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompts')
            prompt_file = os.path.join(prompts_dir, 'email_duplicate_detection.prompty')
            
            # Use ai_processor's parse_prompty_file method
            if os.path.exists(prompt_file):
                system_prompt = ai_processor.parse_prompty_file(prompt_file)
            else:
                raise FileNotFoundError(f"Required prompt file not found: {prompt_file}")
            
            # Create comparison content for AI
            new_summary = f"Subject: {new_item.get('subject', new_item.get('summary', 'Unknown'))}\nSender: {new_item.get('sender', 'Unknown')}\nAction: {new_item.get('action_required', new_item.get('summary', 'N/A'))}\nDue: {new_item.get('due_date', 'N/A')}"
            
            existing_summaries = []
            for i, item in enumerate(existing_items):
                existing_summary = f"Item {i+1} - Subject: {item.get('subject', item.get('summary', 'Unknown'))}\nSender: {item.get('sender', 'Unknown')}\nAction: {item.get('action_required', item.get('summary', 'N/A'))}\nDue: {item.get('due_date', 'N/A')}"
                existing_summaries.append(existing_summary)
            
            # Build the complete prompt
            full_prompt = f"""{system_prompt}

NEW ITEM:
{new_summary}

EXISTING ITEMS:
{chr(10).join(existing_summaries)}

Your response:"""

            # Use AI to analyze duplication
            response = ai_processor.query_ai(full_prompt, max_tokens=50)
            
            if response and response.strip().upper().startswith('DUPLICATE:'):
                try:
                    duplicate_index = int(response.strip().upper().replace('DUPLICATE:', '')) - 1
                    if 0 <= duplicate_index < len(existing_items):
                        return True, existing_items[duplicate_index]
                except ValueError:
                    pass
            
            return False, None
            
        except Exception as e:
            print(f"⚠️  AI duplicate detection failed: {e}")
            return False, None
    
    def _check_team_action_completion(self, item_data, ai_processor):
        """Check if a team action has been completed by analyzing thread context"""
        try:
            # Get email content and thread context
            email_obj = item_data.get('email_object')
            if not email_obj:
                return 'active', None
            
            # Extract email content
            email_content = {
                'subject': item_data.get('email_subject', getattr(email_obj, 'Subject', '')),
                'sender': item_data.get('email_sender', getattr(email_obj, 'SenderName', '')),
                'body': getattr(email_obj, 'Body', '') if hasattr(email_obj, 'Body') else ''
            }
            
            # Get thread context from conversation thread
            thread_context = self._extract_thread_context(email_obj)
            
            if not thread_context:
                return 'active', None
            
            # Use AI to detect if team action has been resolved
            is_resolved, resolution_details = ai_processor.detect_resolved_team_action(
                email_content, thread_context
            )
            
            if is_resolved:
                print(f"✅ Team action completed: '{email_content['subject'][:50]}...'")
                print(f"   → {resolution_details}")
                return 'completed', resolution_details
            else:
                return 'active', None
                
        except Exception as e:
            print(f"⚠️  Team action completion check failed: {e}")
            return 'active', None
    
    def _extract_thread_context(self, email_obj):
        """Extract conversation thread context for team action analysis"""
        try:
            # Try to get conversation thread if available
            if hasattr(email_obj, 'GetConversation'):
                conversation = email_obj.GetConversation()
                if conversation:
                    # Get conversation items
                    conv_items = conversation.GetChildren()
                    thread_parts = []
                    
                    for item in conv_items:
                        try:
                            if hasattr(item, 'Subject') and hasattr(item, 'SenderName') and hasattr(item, 'Body'):
                                # Add email to thread context
                                thread_parts.append(f"From: {item.SenderName}")
                                thread_parts.append(f"Subject: {item.Subject}")
                                thread_parts.append(f"Body: {item.Body[:500]}...")
                                thread_parts.append("---")
                        except Exception:
                            continue
                    
                    if thread_parts:
                        return "\n".join(thread_parts[-10:])  # Last 10 parts to avoid token limits
            
            # Fallback: try to analyze subject line for reply indicators
            subject = getattr(email_obj, 'Subject', '')
            if subject.startswith(('RE:', 'Re:', 'FW:', 'Fw:')):
                return f"This appears to be part of an email thread: {subject}"
                
            return None
            
        except Exception as e:
            print(f"⚠️  Thread context extraction failed: {e}")
            return None
    
    def _remove_duplicate_items(self, summary_sections, ai_processor):
        """Remove duplicate action items, FYIs, etc. from final summary sections using AI"""
        duplicates_removed = 0
        
        # Process action-oriented sections that benefit from duplicate detection
        action_sections = ['required_actions', 'team_actions', 'optional_actions', 'fyi_notices']
        
        for section_name in action_sections:
            if section_name not in summary_sections or len(summary_sections[section_name]) <= 1:
                continue
                
            items = summary_sections[section_name]
            unique_items = []
            
            for item in items:
                # Check if this item is a duplicate of any item already in unique_items
                is_duplicate, duplicate_of = self._ai_detect_duplicate_intent(
                    item, unique_items, ai_processor
                )
                
                if not is_duplicate:
                    unique_items.append(item)
                else:
                    duplicates_removed += 1
                    duplicate_subject = (duplicate_of.get('subject', duplicate_of.get('summary', 'unknown')))[:40] if duplicate_of else 'unknown item'
                    item_subject = (item.get('subject', item.get('summary', 'unknown')))[:40]
                    print(f"🤖 Removed duplicate {section_name[:-1]}: '{item_subject}...' → similar to '{duplicate_subject}...'")
            
            # Update the section with deduplicated items
            summary_sections[section_name] = unique_items
        
        if duplicates_removed > 0:
            print(f"📋 Final summary: {duplicates_removed} duplicate items removed")
        
        return summary_sections
    
    def _separate_completed_team_actions(self, summary_sections):
        """Separate completed team actions into their own section"""
        if 'team_actions' not in summary_sections:
            return summary_sections
        
        active_team_actions = []
        completed_team_actions = []
        
        for item in summary_sections['team_actions']:
            if item.get('completion_status') == 'completed':
                completed_team_actions.append(item)
            else:
                active_team_actions.append(item)
        
        # Update sections
        summary_sections['team_actions'] = active_team_actions
        summary_sections['completed_team_actions'] = completed_team_actions
        
        if completed_team_actions:
            print(f"✅ Found {len(completed_team_actions)} completed team action(s)")
        
        return summary_sections
    
    def build_summary_sections(self, action_items_data, ai_processor=None):
        """Build summary sections using collected AI analysis data"""
        summary_sections = self.EMPTY_SECTIONS.copy()
        processed_entry_ids = set()
        
        # Process all sections using the generic handler
        for source_key, target_key in self.SECTION_KEYS.items():
            items = self._process_section_items(action_items_data, source_key, processed_entry_ids, ai_processor)
            summary_sections[target_key] = items
        
        # Log processing results
        total_processed = len(processed_entry_ids)
        if total_processed > 0:
            print(f"📋 Built initial summary from {total_processed} unique emails")
        
        # Apply AI-powered duplicate detection to final summary sections
        if ai_processor:
            summary_sections = self._remove_duplicate_items(summary_sections, ai_processor)
        
        # Separate completed team actions from active ones
        summary_sections = self._separate_completed_team_actions(summary_sections)
        
        return summary_sections
    
    def display_focused_summary(self, summary_sections):
        """Display AI-enhanced ADHD-friendly focused summary"""
        # Calculate total counts for overview
        total_items = sum(len(items) for items in summary_sections.values())
        high_priority = len(summary_sections.get('required_actions', []))
        
        self._print_summary_header(total_items, high_priority)
        
        # Section configuration with display properties
        section_configs = [
            ('🔴 REQUIRED ACTION ITEMS (ME)', 'required_actions', lambda x: x['due_date'] == "No specific deadline"),
            ('👥 TEAM ACTION ITEMS', 'team_actions', None),
            ('✅ COMPLETED TEAM ACTIONS', 'completed_team_actions', None),
            ('📝 OPTIONAL ACTION ITEMS', 'optional_actions', None),
            ('💼 JOB LISTINGS', 'job_listings', None),
            ('🎪 OPTIONAL EVENTS', 'optional_events', None),
            ('📋 FYI NOTICES', 'fyi_notices', None),
            ('📰 NEWSLETTERS SUMMARY', 'newsletters', None)
        ]
        
        for title, section_key, sort_key in section_configs:
            self._display_section(summary_sections, title, section_key, sort_key)
    
    def _print_summary_header(self, total_items, high_priority):
        """Print summary overview header"""
        print(f"📊 SUMMARY OVERVIEW")
        print(f"Total actionable items: {total_items}")
        print(f"High priority (required actions): {high_priority}")
        print("=" * 50)
        print()
    
    def _display_section(self, summary_sections, title, section_key, sort_key):
        """Display a single summary section"""
        items = summary_sections.get(section_key, [])
        if not items:
            return
            
        # Print section header
        count = len(items)
        title_with_count = f"{title} ({count})"
        print(f"{title_with_count}\n{'-' * len(title_with_count)}")
        
        if sort_key:
            items = sorted(items, key=sort_key)
        
        # Handle special section types
        if section_key == 'fyi_notices':
            self._display_fyi_items(items)
        elif section_key == 'newsletters':
            self._display_newsletter_items(items)
        else:
            self._display_regular_items(items, section_key)
        
        print()  # Add spacing after each section
    
    def _display_fyi_items(self, items):
        """Display FYI items as bullet points"""
        for item in items:
            self._display_item(None, item, 'fyi_notices')
    
    def _display_newsletter_items(self, items):
        """Display newsletter items with special formatting"""
        if len(items) > 1:
            # Combine multiple newsletters
            print("Combined newsletter highlights:")
            for i, item in enumerate(items, 1):
                print(f"{i}. {item['summary']}")
        else:
            # Single newsletter
            for item in items:
                self._display_item(None, item, 'newsletters')
    
    def _display_regular_items(self, items, section_key):
        """Display regular numbered items"""
        for i, item in enumerate(items, 1):
            self._display_item(i, item, section_key)
    
    def _display_item(self, index, item, section_type):
        """Display individual item based on section type"""
        if section_type == 'fyi_notices':
            print(f"{item['summary']} ({item['sender']})")
        elif section_type == 'newsletters':
            print(f"**{item['subject']}** ({item['sender']}, {item['date']})")
            print(f"{item['summary']}")
        else:
            self._display_regular_item(index, item, section_type)
    
    def _display_regular_item(self, index, item, section_type):
        """Display a regular numbered item with details"""
        print(f"{index}. **{item['subject']}**")
        print(f"   From: {item['sender']}")
        
        # Display section-specific information
        if section_type in ['required_actions', 'team_actions', 'completed_team_actions']:
            self._display_action_details(item, section_type)
        elif section_type == 'optional_actions':
            self._display_optional_action_details(item)
        elif section_type == 'job_listings':
            self._display_job_details(item)
        elif section_type == 'optional_events':
            self._display_event_details(item)
        
        # Display links if available
        self._display_links(item, section_type)
    
    def _display_action_details(self, item, section_type):
        """Display details for action items"""
        print(f"   Due: {item.get('due_date', 'No specific deadline')}")
        print(f"   Action: {item.get('action_required', 'Review email')}")
        print(f"   Why: {item['explanation']}")
        
        # Show completion status for team actions
        if section_type in ['team_actions', 'completed_team_actions']:
            completion_status = item.get('completion_status', 'active')
            if completion_status == 'completed':
                print(f"   ✅ Status: COMPLETED")
                completion_note = item.get('completion_note', '')
                if completion_note:
                    print(f"   📝 Note: {completion_note}")
            else:
                print(f"   ⏳ Status: Active")
    
    def _display_optional_action_details(self, item):
        """Display details for optional actions"""
        print(f"   What: {item.get('action_required', 'Provide feedback')}")
        print(f"   Why relevant: {item.get('why_relevant', 'No specific reason provided')}")
        print(f"   Context: {item.get('explanation', 'No context available')}")
    
    def _display_job_details(self, item):
        """Display details for job listings"""
        print(f"   Match: {item['qualification_match']}")
        print(f"   Due: {item.get('due_date', 'No specific deadline')}")
    
    def _display_event_details(self, item):
        """Display details for optional events"""
        print(f"   Date: {item['date']}")
        print(f"   Why relevant: {item['relevance']}")
    
    def _display_links(self, item, section_type):
        """Display relevant links for items"""
        if not item.get('links'):
            return
            
        link_type = self._get_link_type(section_type)
        for link in item['links'][:2]:  # Limit to first 2 links
            print(f"   {link_type}: {link}")
    
    def _get_link_type(self, section_type):
        """Get appropriate link type label based on section"""
        link_types = {
            'job_listings': 'Apply',
            'optional_events': 'Register'
        }
        return link_types.get(section_type, 'Link')
    
    def save_focused_summary(self, summary_sections, timestamp):
        """Save focused summary to HTML file and open in browser"""
        # Create runtime_data/ai_summaries directory if it doesn't exist
        # Get the project root directory (parent of scripts directory)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        runtime_dir = os.path.join(project_root, 'runtime_data', 'ai_summaries')
        os.makedirs(runtime_dir, exist_ok=True)
        
        filename = f'focused_summary_{timestamp.replace(":", "").replace("-", "").replace(" ", "_")}.html'
        filepath = os.path.join(runtime_dir, filename)
        
        # Set up Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('summary_base.html')
        
        # Calculate total counts
        total_items = sum(len(items) for items in summary_sections.values())
        high_priority = len(summary_sections.get('required_actions', []))
        
        # Render HTML with template
        html_content = template.render(
            timestamp=timestamp,
            total_items=total_items,
            high_priority=high_priority,
            required_actions=summary_sections.get('required_actions', []),
            team_actions=summary_sections.get('team_actions', []),
            completed_team_actions=summary_sections.get('completed_team_actions', []),
            optional_actions=summary_sections.get('optional_actions', []),
            job_listings=summary_sections.get('job_listings', []),
            optional_events=summary_sections.get('optional_events', []),
            fyi_notices=summary_sections.get('fyi_notices', []),
            newsletters=summary_sections.get('newsletters', [])
        )
        
        # Write HTML file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # File saved - no longer opening in browser since we display in-app
        file_path = os.path.abspath(filepath)
        
        print(f"💾 HTML summary saved to: {filepath}")
        print(f"📱 Summary displayed in application - browser opening disabled")
        return filepath
    
    def display_suggestions_for_editing(self, email_suggestions):
        """Display all AI suggestions with numbers for editing"""
        if not email_suggestions:
            print("❌ No email suggestions available. Please generate summary first.")
            return False
            
        print("\n📝 EMAIL SUGGESTIONS")
        print("=" * 60)
        
        for i, suggestion_data in enumerate(email_suggestions, 1):
            email = suggestion_data['email_object']
            suggestion = suggestion_data['ai_suggestion']
            
            print(f"{i:2d}. {email.Subject}")
            print(f"    From: {email.SenderName}")
            print(f"    Current: {suggestion.replace('_', ' ').title()}")
            
            # Safe date handling for both COM objects and safe wrappers
            try:
                if hasattr(email.ReceivedTime, 'strftime'):
                    date_str = email.ReceivedTime.strftime('%Y-%m-%d %H:%M')
                else:
                    date_str = str(email.ReceivedTime) if str(email.ReceivedTime) != 'Unknown' else 'Unknown'
            except AttributeError:
                date_str = 'Unknown'
            
            print(f"    Date: {date_str}")
            print()
        
        return True
    
    def show_categorization_preview(self, categories):
        """Show preview of email categorization counts"""
        print(f"\n✅ Email categorization preview:")
        for category, emails in categories.items():
            if category != 'spam_to_delete':
                print(f"  • {category.replace('_', ' ').title()}: {len(emails)} conversations")
        
        # Show spam/deleted count separately if any
        if 'spam_to_delete' in categories:
            spam_count = len(categories['spam_to_delete'])
            print(f"  • 🗑️ Spam/Delete: {spam_count} conversations")
