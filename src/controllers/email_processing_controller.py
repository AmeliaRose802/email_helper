"""Email Processing Controller - Handles all email processing business logic.

This controller manages the complete email processing workflow including:
- Email retrieval and conversation enrichment
- AI-powered classification and analysis
- Action item extraction
- Holistic inbox intelligence
- Progress tracking and reporting
"""

import threading
from datetime import datetime
from typing import Callable, Dict, List, Tuple, Any, Optional


class EmailProcessingController:
    """Controller for email processing operations - pure business logic."""
    
    def __init__(self, outlook_manager, ai_processor, email_analyzer, 
                 email_processor, task_persistence):
        """Initialize controller with required services.
        
        Args:
            outlook_manager: Service for Outlook integration
            ai_processor: Service for AI processing
            email_analyzer: Service for email analysis
            email_processor: Service for email workflow processing
            task_persistence: Service for task storage
        """
        self.outlook_manager = outlook_manager
        self.ai_processor = ai_processor
        self.email_analyzer = email_analyzer
        self.email_processor = email_processor
        self.task_persistence = task_persistence
        self.processing_cancelled = False
        
    def start_email_processing(self, max_emails: int, 
                              progress_callback: Callable[[float, str], None],
                              log_callback: Callable[[str], None]) -> threading.Thread:
        """Start email processing in background thread.
        
        Args:
            max_emails: Maximum number of emails to process
            progress_callback: Function to call with progress updates (percent, message)
            log_callback: Function to call with log messages
            
        Returns:
            The processing thread
        """
        self.processing_cancelled = False
        
        log_callback("🚀 Starting Email Helper Processing...")
        log_callback(f"📊 Processing up to {max_emails} emails")
        log_callback("🔍 Connecting to Outlook...")
        progress_callback(2, "Connecting to Outlook...")
        
        # Connect to Outlook first
        try:
            self.outlook_manager.connect_to_outlook()
            log_callback("[OK] Connected to Outlook successfully")
        except Exception as e:
            log_callback(f"[ERROR] Failed to connect to Outlook: {e}")
            raise
        
        log_callback("📧 Retrieving conversations...")
        progress_callback(5, "Retrieving conversations...")
        
        # Get conversations
        conversation_data = self.outlook_manager.get_emails_with_full_conversations(
            days_back=None, max_emails=max_emails)
        
        log_callback(f"✅ Retrieved {len(conversation_data)} conversations from Outlook")
        log_callback("📝 Enriching conversations with email content...")
        
        # Enrich with email bodies
        enriched_data = self._enrich_conversations(conversation_data)
        
        log_callback(f"✅ Enriched {len(enriched_data)} conversations with email bodies")
        log_callback("🤖 Initializing AI analysis pipeline...")
        progress_callback(15, f"Found {len(enriched_data)} conversations. Starting AI analysis...")
        
        # Start background processing
        processing_thread = threading.Thread(
            target=self._process_emails_background,
            args=(enriched_data, progress_callback, log_callback),
            daemon=True
        )
        processing_thread.start()
        return processing_thread
    
    def _enrich_conversations(self, conversation_data: List[Tuple]) -> List[Tuple]:
        """Enrich conversation data with email bodies.
        
        Args:
            conversation_data: List of (conversation_id, conv_info) tuples
            
        Returns:
            Enriched conversation data with email bodies
        """
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
        
        return enriched_conversation_data
    
    def _process_emails_background(self, conversation_data: List[Tuple],
                                   progress_callback: Callable[[float, str], None],
                                   log_callback: Callable[[str], None]):
        """Background email processing implementation."""
        log_callback("🔧 Initializing email processor...")
        self.email_processor._reset_data_storage()
        
        log_callback("📚 Loading AI learning data...")
        learning_data = self.ai_processor.load_learning_data()
        
        total_conversations = len(conversation_data)
        log_callback(f"🎯 Starting accuracy tracking session for {total_conversations} conversations")
        self.ai_processor.start_accuracy_session(total_conversations)
        
        for i, (conversation_id, conv_info) in enumerate(conversation_data, 1):
            if self.processing_cancelled:
                log_callback("❌ Processing cancelled by user")
                return
            
            progress = 25 + (70 * i / total_conversations)
            
            # Get conversation details for logging
            trigger_subject = conv_info.get('trigger_subject', 'Unknown')
            trigger_sender = conv_info.get('trigger_sender', 'Unknown')
            email_count = len(conv_info.get('emails_with_body', []))
            
            log_callback(f"📧 [{i}/{total_conversations}] Processing: '{trigger_subject[:60]}{'...' if len(trigger_subject) > 60 else ''}' from {trigger_sender} ({email_count} emails)")
            progress_callback(progress, f"Processing {i}/{total_conversations}")
            
            self._process_single_conversation(conversation_id, conv_info, i, total_conversations, learning_data)
        
        # Get suggestions
        log_callback("💾 Storing AI analysis results...")
        email_suggestions = self.email_processor.get_email_suggestions()
        log_callback(f"✅ Generated {len(email_suggestions)} email suggestions")
        
        # Apply holistic analysis
        log_callback("🧠 Applying holistic intelligence to refine classifications...")
        progress_callback(95, "Applying holistic intelligence...")
        email_suggestions = self._apply_holistic_analysis(email_suggestions)
        
        # Reprocess action items
        log_callback("🔄 Reprocessing action items with holistic insights...")
        self._reprocess_action_items(email_suggestions)
        
        # Finalize
        total_emails_processed = len(email_suggestions)
        categories_used = set(s['ai_suggestion'] for s in email_suggestions)
        log_callback(f"🎯 Finalizing accuracy session: {total_emails_processed} emails processed using {len(categories_used)} categories")
        
        self.ai_processor.finalize_accuracy_session(
            success_count=total_emails_processed,
            error_count=0,
            categories_used=categories_used
        )
        log_callback("✅ Accuracy session finalized and recorded!")
        
        # Final summary
        action_items_data = self.email_processor.action_items_data
        log_callback("")
        log_callback("🎉 EMAIL PROCESSING COMPLETE!")
        log_callback(f"📧 Processed: {total_emails_processed} emails")
        log_callback(f"📁 Categories: {len(categories_used)} different types")
        log_callback(f"⚡ Action Items: {sum(len(items) for items in action_items_data.values())} total tasks identified")
        log_callback("🔍 Ready for review and editing in the next tab!")
        
        progress_callback(100, "Processing complete")
        
        return email_suggestions
    
    def _process_single_conversation(self, conversation_id, conv_info, index, total, learning_data):
        """Process a single conversation."""
        emails_with_body = conv_info.get('emails_with_body', [])
        if not emails_with_body:
            return
        
        representative_email_data = emails_with_body[0]
        
        email_content = {
            'subject': representative_email_data['subject'],
            'sender': representative_email_data['sender_name'],
            'body': representative_email_data['body'],
            'received_time': representative_email_data['received_time']
        }
        
        thread_count = len(emails_with_body)
        if thread_count > 1:
            thread_context = self._build_thread_context(emails_with_body, representative_email_data)
            email_content['body'] += f"\n\n--- CONVERSATION THREAD CONTEXT ---\n{thread_context}"
        else:
            thread_context = ""
        
        # AI processing
        try:
            ai_summary = self.ai_processor.generate_email_summary(email_content)
        except Exception as e:
            print(f"⚠️  AI summary failed: {e}")
            ai_summary = f"Summary unavailable - {email_content.get('subject', 'Unknown')[:50]}"
        
        try:
            initial_suggestion = self.ai_processor.classify_email(email_content, learning_data)
        except Exception as e:
            print(f"⚠️  AI classification failed: {e}")
            initial_suggestion = 'fyi'
        
        # Intelligent post-processing
        final_suggestion, processing_notes = self._apply_intelligent_processing(
            initial_suggestion, email_content, thread_context, 
            emails_with_body, representative_email_data
        )
        
        # Store suggestion
        email_suggestion = {
            'email_data': representative_email_data,
            'email_object': representative_email_data['email_object'],
            'ai_suggestion': final_suggestion,
            'ai_summary': ai_summary,
            'initial_classification': initial_suggestion,
            'processing_notes': processing_notes,
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
        self._process_by_category(representative_email_data, email_suggestion['thread_data'], final_suggestion)
    
    def _build_thread_context(self, emails_with_body: List[Dict], representative_email_data: Dict) -> str:
        """Build thread context from emails."""
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
    
    def _apply_intelligent_processing(self, initial_classification: str, email_content: Dict,
                                     thread_context: str, emails_with_body: List[Dict],
                                     representative_email_data: Dict) -> Tuple[str, List[str]]:
        """Apply intelligent post-processing to refine classifications."""
        processing_notes = []
        final_classification = initial_classification
        
        # Check team action resolution
        if initial_classification == 'team_action' and thread_context:
            try:
                is_resolved, resolution_details = self.ai_processor.detect_resolved_team_action(
                    email_content, thread_context)
                if is_resolved:
                    final_classification = 'fyi'
                    processing_notes.append(f"Team action reclassified as FYI: {resolution_details}")
                    print(f"🔄 Intelligent Reclassification: Team action → FYI")
                    print(f"   Reason: {resolution_details}")
            except Exception as e:
                print(f"⚠️  AI team action resolution detection failed: {e}")
        
        # Check optional item deadlines
        if initial_classification in ['optional_action', 'optional_event']:
            try:
                context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}"
                action_details = self.ai_processor.extract_action_item_details(email_content, context)
            except:
                action_details = {}
            
            try:
                is_expired, deadline_details = self.ai_processor.check_optional_item_deadline(
                    email_content, action_details)
                if is_expired:
                    final_classification = 'spam_to_delete'
                    processing_notes.append(f"Optional item marked for deletion: {deadline_details}")
                    print(f"🗑️ Intelligent Cleanup: {initial_classification} → Delete")
                    print(f"   Reason: {deadline_details}")
            except Exception as e:
                print(f"⚠️  AI deadline checking failed: {e}")
        
        return final_classification, processing_notes
    
    def _process_by_category(self, email_data: Dict, thread_data: Dict, category: str):
        """Process email by category and extract relevant information."""
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
            try:
                context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}"
                action_details = self.ai_processor.extract_action_item_details(email_content, context)
            except Exception as e:
                print(f"⚠️  AI action extraction failed: {e}")
                action_details = {
                    'action_required': 'Review email manually - AI processing failed',
                    'due_date': 'No deadline',
                    'explanation': 'AI processing unavailable',
                    'relevance': 'Manual review needed',
                    'links': []
                }
            
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
            try:
                relevance = self.ai_processor.assess_event_relevance(
                    email_data['subject'], email_data['body'], 
                    self.ai_processor.get_job_context())
            except Exception as e:
                print(f"⚠️  AI relevance assessment failed: {e}")
                relevance = "Unable to assess relevance - continuing with processing"
            
            event_item = {
                'relevance': relevance,
                'thread_data': thread_data,
                'email_subject': email_data['subject'],
                'email_sender': email_data['sender_name'],
                'email_date': email_data['received_time']
            }
            self.email_processor.action_items_data[category].append(event_item)
        
        elif category == 'fyi':
            try:
                context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}"
                fyi_summary = self.ai_processor.generate_fyi_summary(email_content, context)
            except Exception as e:
                print(f"⚠️  AI FYI summary failed: {e}")
                fyi_summary = f"• Summary unavailable - {email_data['subject'][:80]}"
            
            fyi_item = {
                'summary': fyi_summary,
                'thread_data': thread_data,
                'email_subject': email_data['subject'],
                'email_sender': email_data['sender_name'],
                'email_date': email_data['received_time']
            }
            self.email_processor.action_items_data[category].append(fyi_item)
        
        elif category == 'newsletter':
            context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}\nRole Details: {self.ai_processor.get_job_role_context()}"
            newsletter_summary = self.ai_processor.generate_newsletter_summary(email_content, context)
            
            newsletter_item = {
                'summary': newsletter_summary,
                'thread_data': thread_data,
                'email_subject': email_data['subject'],
                'email_sender': email_data['sender_name'],
                'email_date': email_data['received_time']
            }
            self.email_processor.action_items_data[category].append(newsletter_item)
    
    def _apply_holistic_analysis(self, email_suggestions: List[Dict]) -> List[Dict]:
        """Apply holistic inbox analysis."""
        try:
            print("🧠 Performing holistic inbox analysis...")
            
            email_data_list = []
            email_lookup = {}
            
            for suggestion in email_suggestions:
                email_data = suggestion['email_data']
                email_data_list.append(email_data)
                email_lookup[email_data.get('entry_id', str(len(email_lookup)))] = suggestion
            
            analysis, analysis_notes = self.ai_processor.analyze_inbox_holistically(email_data_list)
            
            if not analysis:
                print(f"⚠️ Holistic analysis failed: {analysis_notes}")
                return email_suggestions
            
            print(f"✅ Holistic analysis completed: {analysis_notes}")
            
            modified_suggestions = self._apply_holistic_modifications(
                email_suggestions, analysis, email_lookup)
            
            return modified_suggestions
        except Exception as e:
            print(f"⚠️ Holistic analysis error: {e}")
            return email_suggestions
    
    def _apply_holistic_modifications(self, all_email_suggestions: List[Dict],
                                     analysis: Dict, email_lookup: Dict) -> List[Dict]:
        """Apply holistic analysis results to modify email suggestions."""
        modified_suggestions = all_email_suggestions.copy()
        holistic_notes = []
        
        # Handle superseded actions
        for superseded in analysis.get('superseded_actions', []):
            original_id = superseded.get('original_email_id')
            reason = superseded.get('reason', 'Superseded by newer information')
            
            if original_id in email_lookup:
                suggestion = email_lookup[original_id]
                suggestion['ai_suggestion'] = 'fyi'
                suggestion['holistic_notes'] = suggestion.get('holistic_notes', [])
                suggestion['holistic_notes'].append(f"Superseded: {reason}")
                holistic_notes.append(f"Email '{suggestion['email_data'].get('subject', 'Unknown')[:50]}' superseded")
        
        # Handle expired items
        for expired in analysis.get('expired_items', []):
            email_id = expired.get('email_id')
            reason = expired.get('reason', 'Past deadline or event occurred')
            
            if email_id in email_lookup:
                suggestion = email_lookup[email_id]
                suggestion['ai_suggestion'] = 'spam_to_delete'
                suggestion['holistic_notes'] = suggestion.get('holistic_notes', [])
                suggestion['holistic_notes'].append(f"Expired: {reason}")
                holistic_notes.append(f"Email '{suggestion['email_data'].get('subject', 'Unknown')[:50]}' marked for deletion")
        
        # Handle duplicate groups
        for dup_group in analysis.get('duplicate_groups', []):
            keep_id = dup_group.get('keep_email_id')
            archive_ids = dup_group.get('archive_email_ids', [])
            topic = dup_group.get('topic', 'Similar topic')
            
            for archive_id in archive_ids:
                if archive_id in email_lookup and archive_id != keep_id:
                    suggestion = email_lookup[archive_id]
                    suggestion['ai_suggestion'] = 'fyi'
                    suggestion['holistic_notes'] = suggestion.get('holistic_notes', [])
                    suggestion['holistic_notes'].append(f"Duplicate of {topic}")
                    holistic_notes.append(f"Duplicate email archived: {topic}")
        
        # Update priority
        for relevant_action in analysis.get('truly_relevant_actions', []):
            canonical_id = relevant_action.get('canonical_email_id')
            priority = relevant_action.get('priority', 'medium')
            why_relevant = relevant_action.get('why_relevant', '')
            
            if canonical_id in email_lookup:
                suggestion = email_lookup[canonical_id]
                suggestion['holistic_priority'] = priority
                suggestion['holistic_notes'] = suggestion.get('holistic_notes', [])
                suggestion['holistic_notes'].append(f"Priority: {priority} - {why_relevant}")
        
        if holistic_notes:
            print("🧠 Holistic Intelligence Applied:")
            for note in holistic_notes[:5]:
                print(f"   • {note}")
            if len(holistic_notes) > 5:
                print(f"   • ... and {len(holistic_notes) - 5} more modifications")
        
        return modified_suggestions
    
    def _reprocess_action_items(self, email_suggestions: List[Dict]):
        """Reprocess action items after holistic changes."""
        print("🔄 Synchronizing action items after holistic analysis...")
        
        suggestion_lookup = {}
        for suggestion in email_suggestions:
            entry_id = suggestion.get('email_data', {}).get('entry_id')
            if entry_id:
                suggestion_lookup[entry_id] = suggestion
        
        current_action_items = self.email_processor.get_action_items_data()
        changes_made = 0
        
        for category, items in current_action_items.items():
            items_to_remove = []
            items_to_add = []
            
            for i, item in enumerate(items):
                thread_data = item.get('thread_data', {})
                entry_id = thread_data.get('entry_id')
                
                if entry_id and entry_id in suggestion_lookup:
                    suggestion = suggestion_lookup[entry_id]
                    new_category = suggestion['ai_suggestion']
                    
                    if new_category != category:
                        items_to_remove.append(i)
                        changes_made += 1
                        print(f"  🔄 Moving item from '{category}' to '{new_category}': {item.get('email_subject', 'Unknown')[:50]}")
                        
                        if new_category not in current_action_items:
                            current_action_items[new_category] = []
                        
                        new_item = item.copy()
                        items_to_add.append((new_category, new_item))
            
            for i in reversed(items_to_remove):
                items.pop(i)
            
            for new_category, new_item in items_to_add:
                current_action_items[new_category].append(new_item)
        
        self.email_processor.action_items_data = current_action_items
        print(f"✅ Holistic synchronization complete: {changes_made} items moved")
    
    def cancel_processing(self):
        """Cancel ongoing processing."""
        self.processing_cancelled = True
    
    def get_email_suggestions(self) -> List[Dict]:
        """Get current email suggestions."""
        return self.email_processor.get_email_suggestions()
    
    def get_action_items_data(self) -> Dict:
        """Get current action items data."""
        return self.email_processor.get_action_items_data()
