#!/usr/bin/env python3
"""
Summary Generator - Handles summary creation, display, and file output
"""

from datetime import datetime
import os
from jinja2 import Environment, FileSystemLoader


class SummaryGenerator:
    def __init__(self):
        pass
    
    def _create_content_hash(self, subject, sender, due_date=None, action_required=None):
        """Create a hash for content-based deduplication"""
        import hashlib
        import re
        
        # Normalize subject by removing common variations
        normalized_subject = subject.lower().strip()
        
        # Remove common subject prefixes and suffixes
        prefixes_to_remove = ['re:', 'fw:', 'fwd:', 'forward:', '[external]', '[reminder]', '[action required]']
        for prefix in prefixes_to_remove:
            if normalized_subject.startswith(prefix):
                normalized_subject = normalized_subject[len(prefix):].strip()
        
        # Remove task IDs, ticket numbers, and similar variations
        normalized_subject = re.sub(r'\b\w*\d{4,}\w*\b', '', normalized_subject)  # Remove alphanumeric IDs
        normalized_subject = re.sub(r'#\d+', '', normalized_subject)  # Remove ticket numbers
        normalized_subject = re.sub(r'task\s+id:?\s*\w+', '', normalized_subject)  # Remove task ID references
        
        # Remove extra whitespace and standardize
        normalized_subject = ' '.join(normalized_subject.split())
        
        # Normalize sender
        normalized_sender = sender.lower().strip()
        
        # Create content signature with core elements only
        content_parts = [
            normalized_subject,
            normalized_sender,
        ]
        
        # Add due date if provided and meaningful
        if due_date and due_date != 'No specific deadline':
            # Normalize date format
            normalized_date = due_date.lower().strip()
            content_parts.append(normalized_date)
        
        # For action_required, extract the core action verb/concept
        if action_required and action_required not in ['Review email', 'Details in email']:
            # Normalize action to focus on key concepts
            normalized_action = action_required.lower().strip()
            
            # Extract key action concepts (remove minor variations)
            key_concepts = []
            if 'certificate' in normalized_action or 'cert' in normalized_action:
                key_concepts.append('certificate')
            if 'yubikey' in normalized_action or 'yubi' in normalized_action:
                key_concepts.append('yubikey')
            if 'request' in normalized_action:
                key_concepts.append('request')
            if 'renew' in normalized_action or 'new' in normalized_action:
                key_concepts.append('renew')
            if 'expire' in normalized_action or 'expir' in normalized_action:
                key_concepts.append('expire')
                
            # Only add action concepts if we found meaningful ones
            if key_concepts:
                content_parts.extend(sorted(key_concepts))  # Sort for consistency
        
        # Create hash from combined content
        content_string = '|'.join(content_parts)
        return hashlib.md5(content_string.encode('utf-8')).hexdigest()
    
    def _is_duplicate_content(self, subject, sender, due_date, action_required, processed_hashes):
        """Check if this content is a duplicate of something already processed"""
        content_hash = self._create_content_hash(subject, sender, due_date, action_required)
        
        if content_hash in processed_hashes:
            return True, content_hash
        else:
            processed_hashes.add(content_hash)
            return False, content_hash
    
    def build_summary_sections(self, action_items_data):
        """Build summary sections using collected AI analysis data"""
        summary_sections = {
            'required_actions': [],
            'team_actions': [],
            'optional_actions': [],
            'job_listings': [],
            'optional_events': [],
            'fyi_notices': [],
            'newsletters': []
        }
        
        # Track processed emails and content to prevent duplicates
        processed_entry_ids = set()
        processed_content_hashes = set()  # For content-based deduplication
        
        # Required personal actions - use collected action details
        if 'required_personal_action' in action_items_data:
            for item_data in action_items_data['required_personal_action']:
                email_obj = item_data.get('email_object')
                if email_obj and hasattr(email_obj, 'EntryID') and email_obj.EntryID not in processed_entry_ids:
                    
                    action_details = item_data['action_details']
                    
                    # Use enriched email data instead of COM object properties
                    subject = item_data.get('email_subject', getattr(email_obj, 'Subject', 'Unknown Subject'))
                    sender = item_data.get('email_sender', getattr(email_obj, 'SenderName', 'Unknown Sender'))
                    due_date = action_details.get('due_date', 'No specific deadline')
                    action_required = action_details.get('action_required', 'Review email')
                    
                    # Check for content-based duplicates
                    is_duplicate, content_hash = self._is_duplicate_content(
                        subject, sender, due_date, action_required, processed_content_hashes
                    )
                    
                    if not is_duplicate:
                        processed_entry_ids.add(email_obj.EntryID)
                        
                        summary_sections['required_actions'].append({
                            'subject': subject,
                            'sender': sender,
                            'due_date': due_date,
                            'explanation': action_details.get('explanation', 'Details in email'),
                            'action_required': action_required,
                            'links': action_details.get('links', []),
                            'priority': 1,
                            '_entry_id': email_obj.EntryID,  # Track for future deduplication
                            '_content_hash': content_hash  # Track content hash
                        })
                    else:
                        print(f"📋 Filtered duplicate content: '{subject[:50]}...' from {sender}")
        
        # Team actions - use collected action details
        if 'team_action' in action_items_data:
            for item_data in action_items_data['team_action']:
                email_obj = item_data.get('email_object')
                if email_obj and hasattr(email_obj, 'EntryID') and email_obj.EntryID not in processed_entry_ids:
                    
                    action_details = item_data['action_details']
                    
                    # Use enriched email data instead of COM object properties
                    subject = item_data.get('email_subject', getattr(email_obj, 'Subject', 'Unknown Subject'))
                    sender = item_data.get('email_sender', getattr(email_obj, 'SenderName', 'Unknown Sender'))
                    due_date = action_details.get('due_date', 'No specific deadline')
                    action_required = action_details.get('action_required', 'Review email')
                    
                    # Check for content-based duplicates
                    is_duplicate, content_hash = self._is_duplicate_content(
                        subject, sender, due_date, action_required, processed_content_hashes
                    )
                    
                    if not is_duplicate:
                        processed_entry_ids.add(email_obj.EntryID)
                        
                        summary_sections['team_actions'].append({
                            'subject': subject,
                            'sender': sender,
                            'due_date': due_date,
                            'explanation': action_details.get('explanation', 'Details in email'),
                            'action_required': action_required,
                            'links': action_details.get('links', []),
                            'priority': 2,
                            '_entry_id': email_obj.EntryID,  # Track for future deduplication
                            '_content_hash': content_hash  # Track content hash
                        })
                    else:
                        print(f"📋 Filtered duplicate content: '{subject[:50]}...' from {sender}")
        
        # Optional actions - use collected action details
        if 'optional_action' in action_items_data:
            for item_data in action_items_data['optional_action']:
                email_obj = item_data.get('email_object')
                if email_obj and hasattr(email_obj, 'EntryID') and email_obj.EntryID not in processed_entry_ids:
                    
                    action_details = item_data['action_details']
                    
                    # Use enriched email data instead of COM object properties
                    subject = item_data.get('email_subject', getattr(email_obj, 'Subject', 'Unknown Subject'))
                    sender = item_data.get('email_sender', getattr(email_obj, 'SenderName', 'Unknown Sender'))
                    action_required = action_details.get('action_required', 'Review email')
                    
                    # Check for content-based duplicates (no due_date for optional actions)
                    is_duplicate, content_hash = self._is_duplicate_content(
                        subject, sender, None, action_required, processed_content_hashes
                    )
                    
                    if not is_duplicate:
                        processed_entry_ids.add(email_obj.EntryID)
                        
                        summary_sections['optional_actions'].append({
                            'subject': subject,
                            'sender': sender,
                            'explanation': action_details.get('explanation', 'Details in email'),
                            'action_required': action_required,
                            'links': action_details.get('links', []),
                            'why_relevant': action_details.get('relevance', 'General professional interest'),
                            '_entry_id': email_obj.EntryID,  # Track for future deduplication
                            '_content_hash': content_hash  # Track content hash
                        })
                    else:
                        print(f"📋 Filtered duplicate content: '{subject[:50]}...' from {sender}")
        
        # Job listings - use collected job data
        if 'job_listing' in action_items_data:
            for job_data in action_items_data['job_listing']:
                email_obj = job_data.get('email_object')
                if email_obj and hasattr(email_obj, 'EntryID') and email_obj.EntryID not in processed_entry_ids:
                    processed_entry_ids.add(email_obj.EntryID)
                    
                    # Use enriched email data instead of COM object properties
                    subject = job_data.get('email_subject', getattr(email_obj, 'Subject', 'Unknown Subject'))
                    sender = job_data.get('email_sender', getattr(email_obj, 'SenderName', 'Unknown Sender'))
                    
                    summary_sections['job_listings'].append({
                        'subject': subject,
                        'sender': sender,
                        'qualification_match': job_data.get('qualification_match', 'No qualification analysis available'),
                        'links': job_data.get('links', []),
                        'due_date': job_data.get('due_date', 'No deadline specified'),
                        '_entry_id': email_obj.EntryID  # Track for future deduplication
                    })
        
        # Optional events - use collected event data
        if 'optional_event' in action_items_data:
            for event_data in action_items_data['optional_event']:
                email_obj = event_data.get('email_object')
                if email_obj and hasattr(email_obj, 'EntryID') and email_obj.EntryID not in processed_entry_ids:
                    processed_entry_ids.add(email_obj.EntryID)
                    
                    # Use enriched email data instead of COM object properties
                    subject = event_data.get('email_subject', getattr(email_obj, 'Subject', 'Unknown Subject'))
                    sender = event_data.get('email_sender', getattr(email_obj, 'SenderName', 'Unknown Sender'))
                    
                    summary_sections['optional_events'].append({
                        'subject': subject,
                        'sender': sender,
                        'date': event_data.get('date', event_data.get('event_date', 'Unknown')),
                        'relevance': event_data.get('relevance', 'Professional development opportunity'),
                        'links': event_data.get('links', []),
                        '_entry_id': email_obj.EntryID  # Track for future deduplication
                    })
        
        # FYI notices - use collected FYI data
        if 'fyi' in action_items_data:
            for fyi_data in action_items_data['fyi']:
                email_obj = fyi_data.get('email_object')
                if email_obj and hasattr(email_obj, 'EntryID') and email_obj.EntryID not in processed_entry_ids:
                    processed_entry_ids.add(email_obj.EntryID)
                    
                    date_str = 'Unknown'
                    if 'email_date' in fyi_data and fyi_data['email_date']:
                        date = fyi_data['email_date']
                        if hasattr(date, 'strftime'):
                            date_str = date.strftime('%Y-%m-%d')
                        else:
                            date_str = str(date)[:10]
                    elif hasattr(email_obj, 'ReceivedTime'):
                        date_str = email_obj.ReceivedTime.strftime('%Y-%m-%d')
                    
                    summary_sections['fyi_notices'].append({
                        'subject': fyi_data.get('email_subject', getattr(email_obj, 'Subject', 'Unknown Subject')),
                        'sender': fyi_data.get('email_sender', getattr(email_obj, 'SenderName', 'Unknown Sender')),
                        'date': date_str,
                        'summary': fyi_data.get('summary', 'No summary available'),
                        '_entry_id': email_obj.EntryID  # Track for future deduplication
                    })
        
        # Newsletters - use collected newsletter data
        if 'newsletter' in action_items_data:
            for newsletter_data in action_items_data['newsletter']:
                email_obj = newsletter_data.get('email_object')
                if email_obj and hasattr(email_obj, 'EntryID') and email_obj.EntryID not in processed_entry_ids:
                    processed_entry_ids.add(email_obj.EntryID)
                    
                    date_str = 'Unknown'
                    if 'email_date' in newsletter_data and newsletter_data['email_date']:
                        date = newsletter_data['email_date']
                        if hasattr(date, 'strftime'):
                            date_str = date.strftime('%Y-%m-%d')
                        else:
                            date_str = str(date)[:10]
                    elif hasattr(email_obj, 'ReceivedTime'):
                        date_str = email_obj.ReceivedTime.strftime('%Y-%m-%d')
                    
                    summary_sections['newsletters'].append({
                        'subject': newsletter_data.get('email_subject', getattr(email_obj, 'Subject', 'Unknown Subject')),
                        'sender': newsletter_data.get('email_sender', getattr(email_obj, 'SenderName', 'Unknown Sender')),
                        'date': date_str,
                        'summary': newsletter_data.get('summary', 'No summary available'),
                        '_entry_id': email_obj.EntryID  # Track for future deduplication
                    })
        
        # Log deduplication results
        total_processed = len(processed_entry_ids)
        total_content_hashes = len(processed_content_hashes)
        if total_processed > 0:
            print(f"📋 Summary built from {total_processed} unique emails")
            if total_content_hashes < total_processed:
                duplicates_filtered = total_processed - total_content_hashes
                print(f"   📋 Content duplicates filtered: {duplicates_filtered} similar items removed")
        
        return summary_sections
    
    def display_focused_summary(self, summary_sections):
        """Display AI-enhanced ADHD-friendly focused summary"""
        
        # Calculate total counts for overview
        total_items = sum(len(items) for items in summary_sections.values())
        high_priority = len(summary_sections.get('required_actions', []))
        
        print(f"📊 SUMMARY OVERVIEW")
        print(f"Total actionable items: {total_items}")
        print(f"High priority (required actions): {high_priority}")
        print("=" * 50)
        print()
        
        sections = [
            ('🔴 REQUIRED ACTION ITEMS (ME)', 'required_actions', lambda x: x['due_date'] == "No specific deadline"),
            ('👥 TEAM ACTION ITEMS', 'team_actions', None),
            ('📝 OPTIONAL ACTION ITEMS', 'optional_actions', None),
            ('💼 JOB LISTINGS', 'job_listings', None),
            ('🎪 OPTIONAL EVENTS', 'optional_events', None),
            ('📋 FYI NOTICES', 'fyi_notices', None),
            ('📰 NEWSLETTERS SUMMARY', 'newsletters', None)
        ]
        
        for title, section_key, sort_key in sections:
            items = summary_sections.get(section_key, [])
            if not items:
                continue
                
            # Include count in the title
            count = len(items)
            title_with_count = f"{title} ({count})"
            print(f"{title_with_count}\n{'-' * len(title_with_count)}")
            
            if sort_key:
                items = sorted(items, key=sort_key)
            
            # Special handling for FYI and Newsletter sections
            if section_key == 'fyi_notices':
                # FYI notices display as simple bullet points
                for item in items:
                    self._display_item(None, item, section_key)
            elif section_key == 'newsletters':
                # Newsletter section displays as paragraph summaries
                if len(items) > 1:
                    # Combine multiple newsletters into a comprehensive summary
                    print("Combined newsletter highlights:")
                    for i, item in enumerate(items, 1):
                        print(f"{i}. {item['summary']}")
                else:
                    # Single newsletter
                    for item in items:
                        self._display_item(None, item, section_key)
            else:
                # Regular sections with numbered items
                for i, item in enumerate(items, 1):
                    self._display_item(i, item, section_key)
                    print()
    
    def _display_item(self, index, item, section_type):
        """Display individual item based on section type"""
        if section_type == 'fyi_notices':
            # FYI notices show as bullet points only
            print(f"{item['summary']} ({item['sender']})")
        elif section_type == 'newsletters':
            # Newsletters show as paragraph summaries
            print(f"**{item['subject']}** ({item['sender']}, {item['date']})")
            print(f"{item['summary']}")
        else:
            # Regular items display as before
            print(f"{index}. **{item['subject']}**")
            print(f"   From: {item['sender']}")
            
            if section_type in ['required_actions', 'team_actions']:
                print(f"   Due: {item['due_date']}")
                print(f"   Action: {item.get('action_required', 'Review email')}")
                print(f"   Why: {item['explanation']}")
            elif section_type == 'optional_actions':
                print(f"   What: {item.get('action_required', 'Provide feedback')}")
                print(f"   Why relevant: {item['why_relevant']}")
                print(f"   Context: {item['explanation']}")
            elif section_type == 'job_listings':
                print(f"   Match: {item['qualification_match']}")
                print(f"   Due: {item['due_date']}")
            elif section_type == 'optional_events':
                print(f"   Date: {item['date']}")
                print(f"   Why relevant: {item['relevance']}")
            
            # Display links
            if item.get('links'):
                link_type = 'Apply' if section_type == 'job_listings' else 'Register' if section_type == 'optional_events' else 'Link'
                for link in item['links'][:2]:
                    print(f"   {link_type}: {link}")
    
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
