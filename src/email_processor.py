#!/usr/bin/env python3
"""Email Processing Engine for Email Helper - Main Processing Logic and Orchestration.

This module provides the core email processing pipeline that orchestrates
all components of the email helper system. It manages the complete workflow
from email retrieval through AI analysis to summary generation and storage.

The EmailProcessor class coordinates:
- Email loading and preprocessing from Outlook
- AI-powered email classification and analysis
- Content analysis and metadata extraction
- Action item organization and categorization
- Summary generation and formatting
- User interaction and feedback collection
- Result storage and persistence

Key Features:
- Complete email processing pipeline orchestration
- Multi-stage AI analysis with error handling
- Action item extraction and organization
- User feedback integration for accuracy improvement
- Batch processing capabilities for efficiency
- Comprehensive error handling and recovery
- Integration with all core system components

This module serves as the central processing hub that coordinates
all other components to provide the complete email management workflow.
"""

from datetime import datetime
from collections import defaultdict

class EmailProcessor:
    """Email processing pipeline orchestrator and workflow manager.
    
    This class provides the central processing engine for the email helper
    system, coordinating all components to deliver the complete email
    management workflow from raw email retrieval to organized summaries.
    
    The processor manages:
    - Email loading and filtering from Outlook
    - AI-powered classification and analysis
    - Content extraction and metadata processing
    - Action item organization and categorization
    - Summary generation and formatting
    - User feedback collection and integration
    - Result persistence and storage
    
    Attributes:
        outlook_manager (OutlookManager): Handles Outlook email operations
        ai_processor (AIProcessor): Manages AI classification and analysis
        email_analyzer (EmailAnalyzer): Analyzes email content and metadata
        summary_generator (SummaryGenerator): Creates formatted summaries
        action_items_data (dict): Organized action items by category
        email_suggestions (list): Email categorization suggestions
        
    Example:
        >>> processor = EmailProcessor(outlook_mgr, ai_proc, analyzer, generator)
        >>> results = processor.process_emails(max_emails=50)
        >>> print(f"Processed {len(results)} emails")
    """
    
    def __init__(self, outlook_manager, ai_processor, email_analyzer, summary_generator):
        self.outlook_manager = outlook_manager
        self.ai_processor = ai_processor
        self.email_analyzer = email_analyzer
        self.summary_generator = summary_generator
        
        # Data storage
        self.action_items_data = {
            'required_personal_action': [],
            'team_action': [],
            'optional_action': [],
            'job_listing': [],
            'optional_event': [],
            'fyi': [],
            'newsletter': []
        }
        self.email_suggestions = []
    
    def process_emails(self, max_emails=50):
        """Main email processing pipeline"""
        print("🔍 AI SUGGESTIONS PREVIEW")
        print("=" * 60)
        
        # Load learning data
        learning_data = self.ai_processor.load_learning_data()
        
        # Get conversations with full thread context using Outlook APIs
        print("🔗 Retrieving conversations using Outlook conversation APIs...")
        conversation_data = self.outlook_manager.get_emails_with_full_conversations(days_back=7, max_emails=max_emails)
        
        print(f"📊 Analyzing {len(conversation_data)} unique conversations...")
        
        # Initialize accuracy tracking for this session
        self.ai_processor.start_accuracy_session(len(conversation_data))
        
        # Reset data storage
        self._reset_data_storage()
        
        # Process each conversation
        categories = defaultdict(list)
        
        for i, (conversation_id, conv_info) in enumerate(conversation_data, 1):
            emails = conv_info['emails']
            topic = conv_info['topic']
            latest_date = conv_info['latest_date']
            trigger_email = conv_info['recent_trigger']
            
            thread_count = len(emails)
            thread_info = f" (Thread: {thread_count} emails)" if thread_count > 1 else ""
            
            print(f"\n📧 CONVERSATION {i}/{len(conversation_data)}{thread_info}")
            print("=" * 50)
            print(f"Topic: {topic}")
            print(f"Representative Email: {trigger_email.Subject}")
            print(f"From: {trigger_email.SenderName}")
            print(f"Date: {trigger_email.ReceivedTime.strftime('%Y-%m-%d %H:%M')}")
            
            if thread_count > 1:
                participants = list(set(email.SenderName for email in emails))
                print(f"🔗 Full Conversation Thread: {thread_count} emails")
                print(f"   Participants: {', '.join(participants[:3])}{'...' if len(participants) > 3 else ''}")
                print(f"   Date Range: {min(e.ReceivedTime for e in emails).strftime('%Y-%m-%d')} to {latest_date.strftime('%Y-%m-%d %H:%M')}")
            
            # Use the most recent/relevant email for AI processing
            representative_email = self.email_analyzer.choose_best_representative_email(emails, "general")
            
            # Generate AI summary using representative email but with full thread context
            email_content = self._create_email_content_dict(representative_email)
            
            # Add thread context to the email content for better AI analysis
            if thread_count > 1:
                thread_context = self._build_thread_context(emails, representative_email)
                email_content['body'] += f"\n\n--- CONVERSATION THREAD CONTEXT ---\n{thread_context}"
            
            ai_summary = self.ai_processor.generate_email_summary(email_content)
            if ai_summary:
                print(f"📋 AI Summary: {ai_summary}")
            
            # Classify the email with explanation
            classification_result = self.ai_processor.classify_email_with_explanation(email_content, learning_data)
            suggestion = classification_result['category']
            explanation = classification_result['explanation']
            
            # Apply confidence thresholds for auto-approval decisions
            confidence_result = self.ai_processor.apply_confidence_thresholds(classification_result)
            auto_approve = confidence_result['auto_approve']
            confidence_score = confidence_result['confidence']
            review_reason = confidence_result.get('review_reason', '')
            
            # CRASH HARD if AI classification failed
            if suggestion in ["AI processing unavailable", "AI processing failed", "general_information"]:
                print("\n" + "="*80)
                print("🚨 AI CLASSIFICATION FAILURE - CRASHING WITH DEBUG INFO")
                print("="*80)
                print(f"Subject: {email_content['subject']}")
                print(f"Sender: {email_content['sender']}")
                print(f"Date: {email_content['date']}")
                print(f"Body Length: {len(email_content['body'])} chars")
                print(f"Learning Data Rows: {len(learning_data)}")
                print("\n--- EMAIL BODY ---")
                print(email_content['body'][:1000])
                if len(email_content['body']) > 1000:
                    print(f"... (truncated, full length: {len(email_content['body'])} chars)")
                print(f"\n--- AI CLASSIFICATION RESULT ---")
                print(f"Suggestion: '{suggestion}'")
                print(f"Explanation: '{explanation}'")
                print("="*80)
                raise RuntimeError(f"AI classification failed for email: {email_content['subject']}")
            
            print(f"🤖 AI Classification: {suggestion.replace('_', ' ').title()}")
            print(f"   📝 Reasoning: {explanation}")
            print(f"   🎯 Confidence: {confidence_score:.1%} ({'Auto-approve' if auto_approve else f'Manual review: {review_reason}'})")
            print(f"   ⏳ Detailed processing deferred until after review")
            
            # Store email suggestion with full conversation context and explanation
            email_suggestion = {
                'email_object': representative_email,
                'ai_suggestion': suggestion,
                'explanation': explanation,  # Store the AI explanation
                'confidence_score': confidence_score,
                'auto_approve': auto_approve,
                'review_reason': review_reason,
                'thread_data': {
                    'conversation_id': conversation_id,
                    'thread_count': thread_count,
                    'all_emails': emails,  # Include all emails in thread
                    'participants': participants if thread_count > 1 else [representative_email.SenderName],
                    'latest_date': latest_date,
                    'topic': topic
                }
            }
            
            self.email_suggestions.append(email_suggestion)
            
            # Store in categories but skip expensive processing for now
            categories[suggestion].append(representative_email)
        
        # Show categorization summary
        self.summary_generator.show_categorization_preview(categories)
        
        print(f"\n💡 Initial classification complete! Review and reclassify as needed.")
        print(f"   Detailed AI analysis will be performed when you apply changes to Outlook.")
        print(f"   This saves processing time and avoids wasted work on reclassified emails.")
        
        return self.email_suggestions
    
    def process_detailed_analysis(self, finalized_suggestions):
        """
        Perform detailed AI analysis only after user has completed reclassification.
        This includes enhanced thread grouping and duplicate detection.
        """
        print("\n🔍 Processing detailed analysis for finalized classifications...")
        
        # Reset action items data for fresh processing
        self._reset_data_storage()
        
        # Step 1: Apply enhanced thread grouping to improve organization
        print("🔗 Applying enhanced thread grouping...")
        enhanced_thread_groups = self.group_similar_threads(finalized_suggestions)
        print(f"✅ Enhanced grouping: {len(enhanced_thread_groups)} thread groups created")
        
        # Step 2: Process by category but with enhanced grouping awareness
        by_category = {}
        for suggestion in finalized_suggestions:
            category = suggestion.get('ai_suggestion', 'fyi')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(suggestion)
        
        # Process each category with appropriate detail level
        for category, suggestions in by_category.items():
            print(f"📋 Processing {len(suggestions)} {category.replace('_', ' ')} items...")
            
            for suggestion in suggestions:
                email_object = suggestion.get('email_object')
                thread_data = suggestion.get('thread_data', {})
                explanation = suggestion.get('explanation', f"Classified as {category}")
                
                if email_object:
                    # Process with enhanced thread context
                    self._process_email_by_category(email_object, thread_data, category, explanation)
        
        # Step 3: Apply content-based duplicate detection to processed results
        print("🤖 Applying content-based duplicate detection...")
        self.action_items_data = self.detect_duplicate_tasks(self.action_items_data)
        
        print("✅ Detailed analysis completed with enhanced grouping and deduplication")
        return self.action_items_data
    
    def _build_thread_context(self, emails, representative_email):
        """Build context summary from conversation thread"""
        try:
            if len(emails) <= 1:
                return ""
                
            # Sort emails chronologically
            sorted_emails = sorted(emails, key=lambda x: x.ReceivedTime)
            
            context_parts = []
            context_parts.append(f"This is part of a {len(emails)}-email conversation thread.")
            
            # Add participant summary
            participants = list(set(email.SenderName for email in emails))
            context_parts.append(f"Participants: {', '.join(participants)}")
            
            # Add key emails summary (excluding the representative)
            other_emails = [e for e in sorted_emails if e.EntryID != representative_email.EntryID][:3]
            if other_emails:
                context_parts.append("Related messages in thread:")
                for email in other_emails:
                    date_str = email.ReceivedTime.strftime('%m/%d %H:%M')
                    subject = email.Subject[:50] + "..." if len(email.Subject) > 50 else email.Subject
                    context_parts.append(f"- {date_str} from {email.SenderName}: {subject}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            return f"Thread context unavailable: {str(e)}"
    
    def _reset_data_storage(self):
        """Reset data storage for new processing run"""
        self.action_items_data = {
            'required_personal_action': [],
            'team_action': [],
            'optional_action': [],
            'job_listing': [],
            'optional_event': [],
            'fyi': [],
            'newsletter': []
        }
        self.email_suggestions = []
    
    def _create_email_content_dict(self, email):
        """Create standardized email content dictionary"""
        return {
            'subject': email.Subject,
            'sender': email.SenderName,
            'date': email.ReceivedTime.strftime('%Y-%m-%d %H:%M'),
            'body': self.outlook_manager.get_email_body(email)
        }
    
    def _process_email_by_category(self, email, email_data, suggestion, explanation=None):
        """Process email based on its AI-suggested category"""
        # Check for duplicates using EntryID
        entry_id = getattr(email, 'EntryID', None)
        if not entry_id:
            print(f"⚠️  Warning: Email has no EntryID, skipping: {getattr(email, 'Subject', 'Unknown')}")
            return
        
        # Check if we've already processed this exact email
        for category_data in self.action_items_data.values():
            for existing_item in category_data:
                existing_email = existing_item.get('email_object')
                if existing_email and getattr(existing_email, 'EntryID', None) == entry_id:
                    print(f"⚠️  Duplicate email detected and skipped: {email.Subject[:50]}...")
                    return
        
        # Process action items with detailed output
        if suggestion in ['required_personal_action', 'team_action', 'optional_action']:
            print("🔍 Extracting action item details...")
            
            # For thread processing, analyze the most relevant email in the thread
            analysis_email = self.email_analyzer.choose_best_representative_email(
                email_data.get('all_emails', [email]), "actionable"
            )
            
            email_content = self._create_email_content_dict(analysis_email)
            
            # Add thread context if available
            thread_count = email_data.get('thread_count', 1)
            if thread_count > 1:
                thread_context = f"\nThread context: {thread_count} emails in conversation with {', '.join(email_data['participants'])}"
                email_content['body'] += thread_context
            
            context = self.ai_processor.get_standard_context()
            action_details = self.ai_processor.extract_action_item_details(email_content, context)
            
            # CRASH HARD if AI parsing failed - dump debug info
            if action_details.get('explanation') in ['AI could not analyze this email', 'AI parsing failed']:
                print("\n" + "="*80)
                print("🚨 AI PARSING FAILURE - CRASHING WITH DEBUG INFO")
                print("="*80)
                print(f"Subject: {email_content['subject']}")
                print(f"Sender: {email_content['sender']}")
                print(f"Date: {email_content['date']}")
                print(f"Body Length: {len(email_content['body'])} chars")
                print(f"Context Length: {len(context)} chars")
                print("\n--- EMAIL BODY ---")
                print(email_content['body'][:1000])
                if len(email_content['body']) > 1000:
                    print(f"... (truncated, full length: {len(email_content['body'])} chars)")
                print("\n--- CONTEXT ---")
                print(context[:500])
                if len(context) > 500:
                    print(f"... (truncated, full length: {len(context)} chars)")
                print("\n--- AI RESPONSE ---")
                print(f"Action Details Returned: {action_details}")
                print("="*80)
                raise RuntimeError(f"AI parsing failed for action item: {email_content['subject']}")
            
            print(f"   • Due Date: {action_details.get('due_date', 'No specific deadline')}")
            print(f"   • Action: {action_details.get('action_required', 'Review email')}")
            if action_details.get('links'):
                print(f"   • Links: {len(action_details['links'])} found")
            
            self.action_items_data[suggestion].append({
                'email_object': email,
                'email_subject': email.Subject,
                'email_sender': email.SenderName,
                'email_date': email.ReceivedTime,
                'action_details': action_details,
                'explanation': explanation or f"Classified as {suggestion.replace('_', ' ')} based on email content.",
                'thread_data': email_data
            })
        
        # Process job listings with detailed output
        elif suggestion == 'job_listing':
            print("🔍 Analyzing job qualification match...")
            qualification_match = self.email_analyzer.assess_job_qualification(email.Subject, self.outlook_manager.get_email_body(email))
            metadata = self.email_analyzer.extract_email_metadata(email.Subject, self.outlook_manager.get_email_body(email))
            
            print(f"   • Match Assessment: {qualification_match}")
            print(f"   • Application Due: {metadata['due_date']}")
            if metadata['links']:
                print(f"   • Application Links: {len(metadata['links'])} found")
            
            job_data = {
                'email_object': email,
                'email_subject': email.Subject,
                'email_sender': email.SenderName,
                'email_date': email.ReceivedTime,
                'qualification_match': qualification_match,
                'due_date': metadata['due_date'],
                'links': metadata['links'],
                'explanation': explanation or f"Classified as job listing based on email content.",
                'thread_data': email_data
            }
            self.action_items_data['job_listing'].append(job_data)
        
        # Process optional events with detailed output
        elif suggestion == 'optional_event':
            print("🔍 Analyzing event details and relevance...")
            metadata = self.email_analyzer.extract_email_metadata(email.Subject, self.outlook_manager.get_email_body(email))
            relevance = self.ai_processor.assess_event_relevance(email.Subject, self.outlook_manager.get_email_body(email), self.ai_processor.get_job_context())
            
            print(f"   • Event Date: {metadata['due_date']}")
            print(f"   • Relevance: {relevance[:100]}..." if len(relevance) > 100 else f"   • Relevance: {relevance}")
            if metadata['links']:
                print(f"   • Registration Links: {len(metadata['links'])} found")
            
            event_data = {
                'email_object': email,
                'email_subject': email.Subject,
                'email_sender': email.SenderName,
                'email_date': email.ReceivedTime,
                'date': metadata['due_date'],
                'relevance': relevance,
                'links': metadata['links'],
                'explanation': explanation or f"Classified as optional event based on email content.",
                'thread_data': email_data
            }
            self.action_items_data['optional_event'].append(event_data)
        
        # For other categories, just show basic info
        else:
            if suggestion == 'spam_to_delete':
                print("🗑️  Marked for deletion")
                thread_count = email_data.get('thread_count', 1)
                if thread_count > 1:
                    print(f"   Note: Will handle entire thread ({thread_count} emails)")
            elif suggestion == 'work_relevant':
                print("ℹ️  Work-relevant informational content")
                thread_count = email_data.get('thread_count', 1)
                if thread_count > 1:
                    print(f"   Note: Thread summary ({thread_count} emails)")
            elif suggestion == 'fyi':
                print("📋 Processing FYI notice...")
                # Generate FYI summary
                email_content = self._create_email_content_dict(email)
                context = self.ai_processor.get_standard_context()
                fyi_summary = self.ai_processor.generate_fyi_summary(email_content, context)
                
                print(f"   • Summary: {fyi_summary}")
                
                fyi_data = {
                    'email_object': email,
                    'email_subject': email.Subject,
                    'email_sender': email.SenderName,
                    'email_date': email.ReceivedTime,
                    'summary': fyi_summary,
                    'explanation': explanation or f"Classified as FYI based on email content.",
                    'thread_data': email_data
                }
                self.action_items_data['fyi'].append(fyi_data)
                
            elif suggestion == 'newsletter':
                print("📰 Processing newsletter...")
                # Generate newsletter summary
                email_content = self._create_email_content_dict(email)
                context = self.ai_processor.get_standard_context()
                newsletter_summary = self.ai_processor.generate_newsletter_summary(email_content, context)
                
                print(f"   • Newsletter: {email.Subject}")
                print(f"   • Key highlights captured for summary")
                
                newsletter_data = {
                    'email_object': email,
                    'email_subject': email.Subject,
                    'email_sender': email.SenderName,
                    'email_date': email.ReceivedTime,
                    'summary': newsletter_summary,
                    'explanation': explanation or f"Classified as newsletter based on email content.",
                    'thread_data': email_data
                }
                self.action_items_data['newsletter'].append(newsletter_data)
    
    def detect_duplicate_tasks(self, action_items_data):
        """Detect and merge duplicate tasks using content similarity analysis
        
        Args:
            action_items_data: Dictionary of categorized action items
            
        Returns:
            dict: De-duplicated action items with merged information
        """
        print("🔍 Detecting duplicate tasks using content similarity...")
        
        merged_data = {}
        duplicates_removed = 0
        
        # Process action-oriented categories that benefit from duplicate detection
        action_categories = ['required_personal_action', 'team_action', 'optional_action']
        
        for category in action_categories:
            if category not in action_items_data:
                merged_data[category] = []
                continue
                
            items = action_items_data[category]
            unique_items = []
            
            print(f"   Analyzing {len(items)} {category.replace('_', ' ')} items...")
            
            for item in items:
                # Check if this item is similar to any already processed unique items
                is_duplicate = False
                
                for unique_item in unique_items:
                    is_similar, similarity_score = self.email_analyzer.calculate_content_similarity(
                        item, unique_item, threshold=0.75
                    )
                    
                    if is_similar:
                        # Merge the duplicate into the existing unique item
                        self._merge_duplicate_tasks(unique_item, item, similarity_score)
                        is_duplicate = True
                        duplicates_removed += 1
                        
                        item_subject = item.get('email_subject', 'Unknown')[:40]
                        unique_subject = unique_item.get('email_subject', 'Unknown')[:40]
                        print(f"   🤖 Merged duplicate: '{item_subject}...' → '{unique_subject}...' (similarity: {similarity_score:.2f})")
                        break
                
                if not is_duplicate:
                    unique_items.append(item)
            
            merged_data[category] = unique_items
        
        # Copy other categories unchanged
        for category, items in action_items_data.items():
            if category not in action_categories:
                merged_data[category] = items
        
        if duplicates_removed > 0:
            print(f"✅ Duplicate detection complete: {duplicates_removed} tasks merged")
        else:
            print("✅ No duplicate tasks detected")
        
        return merged_data
    
    def _merge_duplicate_tasks(self, target_item, duplicate_item, similarity_score):
        """Merge duplicate task information into target item"""
        try:
            # Add contributing email information
            if 'contributing_emails' not in target_item:
                target_item['contributing_emails'] = []
            
            # Add the duplicate's email information
            duplicate_email_info = {
                'email_object': duplicate_item.get('email_object'),
                'subject': duplicate_item.get('email_subject', ''),
                'sender': duplicate_item.get('email_sender', ''),
                'received_time': getattr(duplicate_item.get('email_object'), 'ReceivedTime', ''),
                'similarity_score': similarity_score
            }
            target_item['contributing_emails'].append(duplicate_email_info)
            
            # Merge action details if they provide additional information
            target_action = target_item.get('action_details', {})
            duplicate_action = duplicate_item.get('action_details', {})
            
            # Keep the more specific action description if available
            if len(duplicate_action.get('action_required', '')) > len(target_action.get('action_required', '')):
                target_action['action_required'] = duplicate_action['action_required']
            
            # Combine explanations if different
            target_explanation = target_action.get('explanation', '')
            duplicate_explanation = duplicate_action.get('explanation', '')
            if duplicate_explanation and duplicate_explanation not in target_explanation:
                if target_explanation:
                    target_action['explanation'] = f"{target_explanation}; {duplicate_explanation}"
                else:
                    target_action['explanation'] = duplicate_explanation
            
            # Use earlier due date if both are available
            target_due = target_action.get('due_date')
            duplicate_due = duplicate_action.get('due_date')
            if duplicate_due and duplicate_due != "No specific deadline":
                if target_due == "No specific deadline" or not target_due:
                    target_action['due_date'] = duplicate_due
                elif target_due != duplicate_due:
                    # Keep both dates for reference
                    target_action['alternative_due_dates'] = target_action.get('alternative_due_dates', [])
                    if duplicate_due not in target_action['alternative_due_dates']:
                        target_action['alternative_due_dates'].append(duplicate_due)
            
            # Merge links
            target_links = target_action.get('links', [])
            duplicate_links = duplicate_action.get('links', [])
            for link in duplicate_links:
                if link not in target_links:
                    target_links.append(link)
            if target_links:
                target_action['links'] = target_links
            
            target_item['action_details'] = target_action
            
        except Exception as e:
            print(f"⚠️  Task merge failed: {e}")

    def group_similar_threads(self, email_suggestions):
        """Group email suggestions by thread with enhanced similarity detection"""
        print("🔗 Grouping similar email threads...")
        
        # Use existing thread grouping from email_analyzer
        thread_groups = self.email_analyzer.group_emails_by_thread(
            [suggestion.get('email_object') for suggestion in email_suggestions 
             if suggestion.get('email_object')]
        )
        
        # Enhanced grouping: merge groups with similar subjects/content
        enhanced_groups = {}
        group_id = 0
        
        for thread_key, emails in thread_groups.items():
            # Find if this thread should merge with an existing enhanced group
            merged = False
            
            for existing_key, existing_group in enhanced_groups.items():
                # Check if threads should be merged based on content similarity
                sample_email_new = emails[0] if emails else None
                sample_email_existing = existing_group['emails'][0] if existing_group['emails'] else None
                
                if sample_email_new and sample_email_existing:
                    is_similar, _ = self.email_analyzer.calculate_content_similarity(
                        sample_email_new, sample_email_existing, threshold=0.6
                    )
                    
                    if is_similar:
                        # Merge threads
                        existing_group['emails'].extend(emails)
                        existing_group['thread_keys'].append(thread_key)
                        merged = True
                        break
            
            if not merged:
                # Create new enhanced group
                group_id += 1
                enhanced_groups[f"group_{group_id}"] = {
                    'emails': emails,
                    'thread_keys': [thread_key],
                    'primary_subject': emails[0].Subject if emails else 'Unknown'
                }
        
        print(f"✅ Thread grouping complete: {len(thread_groups)} original threads → {len(enhanced_groups)} enhanced groups")
        
        return enhanced_groups

    def generate_summary(self):
        """Generate and display the focused summary"""
        summary_sections = self.summary_generator.build_summary_sections(self.action_items_data)
        
        print("\n" + "=" * 60)
        print("📊 INITIAL SUMMARY")
        print("=" * 60)
        self.summary_generator.display_focused_summary(summary_sections)
        
        # Save summary
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.summary_generator.save_focused_summary(summary_sections, timestamp)
        
        return summary_sections
    
    def get_email_suggestions(self):
        """Get the processed email suggestions"""
        return self.email_suggestions
    
    def get_action_items_data(self):
        """Get the action items data"""
        return self.action_items_data
