#!/usr/bin/env python3
"""Summary Generator for Email Helper - Summary Creation and Display Management.

This module handles the generation, formatting, and output of email summaries
across multiple formats including GUI display, HTML files, and structured
text output. It provides comprehensive summary management capabilities.

The SummaryGenerator class manages:
- Summary section organization and formatting
- Multi-format output generation (GUI, HTML, text)
- Template-based summary rendering using Jinja2
- Section persistence and state management
- Cross-session summary continuity
- User-friendly formatting and presentation

Key Features:
- Configurable summary sections with standardized structure
- Template-based HTML generation with consistent styling
- Persistent summary state across application sessions
- Multiple output formats for different use cases
- Section-specific formatting and organization
- Integration with task persistence for outstanding items

This module integrates with the GUI components and task management
system to provide a unified summary experience.
"""

from datetime import datetime
import os
from jinja2 import Environment, FileSystemLoader


class SummaryGenerator:
    """Summary generation and formatting engine for email processing results.
    
    This class handles the creation, organization, and formatting of email
    summaries across multiple output formats. It manages summary sections,
    applies templates, and ensures consistent presentation of results.
    
    The generator provides:
    - Structured summary section management
    - Template-based HTML output generation
    - Cross-session summary persistence
    - Multiple output format support
    - Section-specific formatting and styling
    - Integration with task management systems
    
    Attributes:
        SECTION_KEYS (dict): Mapping of category names to section identifiers
        EMPTY_SECTIONS (dict): Default empty structure for summary sections
        
    Example:
        >>> generator = SummaryGenerator()
        >>> sections = generator.organize_summary_sections(action_items)
        >>> html_output = generator.generate_html_summary(sections)
        >>> print(len(html_output))  # Size of generated HTML
    """
    
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
            # Create comparison content for AI
            new_summary = f"Subject: {new_item.get('subject', new_item.get('summary', 'Unknown'))}\nSender: {new_item.get('sender', 'Unknown')}\nAction: {new_item.get('action_required', new_item.get('summary', 'N/A'))}\nDue: {new_item.get('due_date', 'N/A')}"
            
            existing_summaries = []
            for i, item in enumerate(existing_items):
                existing_summary = f"Item {i+1} - Subject: {item.get('subject', item.get('summary', 'Unknown'))}\nSender: {item.get('sender', 'Unknown')}\nAction: {item.get('action_required', item.get('summary', 'N/A'))}\nDue: {item.get('due_date', 'N/A')}"
                existing_summaries.append(existing_summary)
            
            # Create inputs for the duplicate detection prompty
            inputs = {
                'new_item': new_summary,
                'existing_items': '\n'.join(existing_summaries),
                'item_count': len(existing_items)
            }
            
            # Use AI to analyze duplication using the prompty file
            response = ai_processor.execute_prompty('email_duplicate_detection.prompty', inputs)
            
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
        """Remove duplicate action items, FYIs, etc. from final summary sections using content similarity"""
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
                is_duplicate = False
                
                # First try content-based similarity if email_analyzer is available
                if hasattr(ai_processor, 'email_analyzer') and ai_processor.email_analyzer:
                    for unique_item in unique_items:
                        is_similar, similarity_score = ai_processor.email_analyzer.calculate_content_similarity(
                            item, unique_item, threshold=0.75
                        )
                        
                        if is_similar:
                            # Merge information from duplicate into unique item
                            self._merge_summary_items(unique_item, item, similarity_score)
                            is_duplicate = True
                            duplicates_removed += 1
                            
                            item_subject = (item.get('subject', item.get('summary', 'unknown')))[:40]
                            unique_subject = (unique_item.get('subject', unique_item.get('summary', 'unknown')))[:40]
                            print(f"🤖 Merged duplicate {section_name[:-1]}: '{item_subject}...' → '{unique_subject}...' (similarity: {similarity_score:.2f})")
                            break
                
                # Fallback to AI-powered detection if content similarity didn't catch it
                if not is_duplicate and ai_processor:
                    is_ai_duplicate, duplicate_of = self._ai_detect_duplicate_intent(
                        item, unique_items, ai_processor
                    )
                    
                    if is_ai_duplicate:
                        is_duplicate = True
                        duplicates_removed += 1
                        
                        item_subject = (item.get('subject', item.get('summary', 'unknown')))[:40]
                        duplicate_subject = (duplicate_of.get('subject', duplicate_of.get('summary', 'unknown')))[:40] if duplicate_of else 'unknown item'
                        print(f"🤖 AI detected duplicate {section_name[:-1]}: '{item_subject}...' → similar to '{duplicate_subject}...'")
                
                if not is_duplicate:
                    unique_items.append(item)
            
            # Update the section with deduplicated items
            summary_sections[section_name] = unique_items
        
        if duplicates_removed > 0:
            print(f"📋 Final summary: {duplicates_removed} duplicate items removed")
        
        return summary_sections
    
    def _merge_summary_items(self, target_item, duplicate_item, similarity_score):
        """Merge information from duplicate summary item into target item"""
        try:
            # Add contributing email information if not already present
            if 'contributing_emails' not in target_item:
                target_item['contributing_emails'] = []
            
            # Add the duplicate's email information
            duplicate_email_info = {
                'subject': duplicate_item.get('subject', ''),
                'sender': duplicate_item.get('sender', ''),
                'date': duplicate_item.get('date', ''),
                'entry_id': duplicate_item.get('_entry_id', ''),
                'similarity_score': similarity_score
            }
            target_item['contributing_emails'].append(duplicate_email_info)
            
            # Merge action details for action items
            if 'action_required' in duplicate_item:
                # Keep the more detailed action description
                if len(duplicate_item.get('action_required', '')) > len(target_item.get('action_required', '')):
                    target_item['action_required'] = duplicate_item['action_required']
                
                # Combine explanations if different
                target_explanation = target_item.get('explanation', '')
                duplicate_explanation = duplicate_item.get('explanation', '')
                if duplicate_explanation and duplicate_explanation not in target_explanation:
                    if target_explanation:
                        target_item['explanation'] = f"{target_explanation}; {duplicate_explanation}"
                    else:
                        target_item['explanation'] = duplicate_explanation
                
                # Keep earlier due date
                target_due = target_item.get('due_date')
                duplicate_due = duplicate_item.get('due_date')
                if duplicate_due and duplicate_due != "No specific deadline":
                    if target_due == "No specific deadline" or not target_due:
                        target_item['due_date'] = duplicate_due
            
            # Merge links
            target_links = target_item.get('links', [])
            duplicate_links = duplicate_item.get('links', [])
            for link in duplicate_links:
                if link not in target_links:
                    target_links.append(link)
            if target_links:
                target_item['links'] = target_links
                
        except Exception as e:
            print(f"⚠️  Summary item merge failed: {e}")
    
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
        """Build summary sections using collected AI analysis data with holistic duplicate removal"""
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
        
        # Apply holistic cross-section duplicate removal
        summary_sections = self._remove_cross_section_duplicates(summary_sections, ai_processor)
        
        # Separate completed team actions from active ones
        summary_sections = self._separate_completed_team_actions(summary_sections)
        
        return summary_sections
    
    def _remove_cross_section_duplicates(self, summary_sections, ai_processor):
        """Remove FYIs/newsletters already covered by tasks - holistic duplicate removal"""
        print("🔄 Applying holistic cross-section duplicate removal...")
        
        # Collect all action items (high priority sections)
        action_items = []
        action_sections = ['required_actions', 'team_actions', 'optional_actions']
        
        for section_name in action_sections:
            if section_name in summary_sections:
                action_items.extend(summary_sections[section_name])
        
        if not action_items:
            print("   No action items found, skipping cross-section deduplication")
            return summary_sections
        
        cross_duplicates_removed = 0
        
        # Check FYI notices against action items
        if 'fyi_notices' in summary_sections:
            unique_fyis = []
            
            for fyi_item in summary_sections['fyi_notices']:
                is_covered_by_action = False
                
                # Check if this FYI is already covered by an action item
                if hasattr(ai_processor, 'email_analyzer') and ai_processor.email_analyzer:
                    for action_item in action_items:
                        is_similar, similarity_score = ai_processor.email_analyzer.calculate_content_similarity(
                            fyi_item, action_item, threshold=0.15  # Lower threshold for cross-section
                        )
                        
                        if is_similar:
                            is_covered_by_action = True
                            cross_duplicates_removed += 1
                            
                            fyi_subject = fyi_item.get('subject', fyi_item.get('summary', 'unknown'))[:40]
                            action_subject = action_item.get('subject', 'unknown')[:40]
                            print(f"   🔗 Removed FYI covered by task: '{fyi_subject}...' → covered by '{action_subject}...' (similarity: {similarity_score:.2f})")
                            break
                
                if not is_covered_by_action:
                    unique_fyis.append(fyi_item)
            
            summary_sections['fyi_notices'] = unique_fyis
        
        # Check newsletters against action items and FYIs
        if 'newsletters' in summary_sections:
            unique_newsletters = []
            
            # Combine action items and remaining FYIs for comparison
            comparison_items = action_items + summary_sections.get('fyi_notices', [])
            
            for newsletter_item in summary_sections['newsletters']:
                is_covered = False
                
                if hasattr(ai_processor, 'email_analyzer') and ai_processor.email_analyzer:
                    for comparison_item in comparison_items:
                        is_similar, similarity_score = ai_processor.email_analyzer.calculate_content_similarity(
                            newsletter_item, comparison_item, threshold=0.12  # Even lower threshold for newsletters
                        )
                        
                        if is_similar:
                            is_covered = True
                            cross_duplicates_removed += 1
                            
                            newsletter_subject = newsletter_item.get('subject', newsletter_item.get('summary', 'unknown'))[:40]
                            comparison_subject = comparison_item.get('subject', comparison_item.get('summary', 'unknown'))[:40]
                            print(f"   🔗 Removed newsletter covered by other content: '{newsletter_subject}...' → covered by '{comparison_subject}...' (similarity: {similarity_score:.2f})")
                            break
                
                if not is_covered:
                    unique_newsletters.append(newsletter_item)
            
            summary_sections['newsletters'] = unique_newsletters
        
        if cross_duplicates_removed > 0:
            print(f"✅ Holistic deduplication: {cross_duplicates_removed} cross-section duplicates removed")
        else:
            print("✅ No cross-section duplicates found")
        
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
