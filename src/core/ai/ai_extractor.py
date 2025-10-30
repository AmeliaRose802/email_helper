"""AI Extractor - Action Item Extraction and Analysis.

This module handles extraction of action items, deadlines, and task details
from emails, including deduplication and relevance assessment.
"""

import json
import logging
from datetime import datetime
from utils import parse_date_string
from .prompt_manager import PromptManager
from .response_parser import ResponseParser

logger = logging.getLogger(__name__)


class AIExtractor:
    """Handles action item extraction and analysis.
    
    This class is responsible for extracting action items from emails,
    analyzing deadlines, detecting duplicates, and performing holistic
    inbox analysis.
    """
    
    def __init__(self, prompt_manager: PromptManager, response_parser: ResponseParser):
        """Initialize the extractor.
        
        Args:
            prompt_manager: PromptManager instance for executing prompts
            response_parser: ResponseParser instance for parsing responses
        """
        self.prompt_manager = prompt_manager
        self.response_parser = response_parser
    
    def extract_action_item_details(self, email_content, context=""):
        """Extract action item details from email.
        
        Args:
            email_content: Email data to analyze
            context: Additional context for extraction
            
        Returns:
            dict: Action item details including due date, links, etc.
        """
        inputs = self._create_email_inputs(email_content, context)
        result = self.prompt_manager.execute_prompty('summarize_action_item.prompty', inputs)
        
        return self.response_parser.parse_action_item_response(result, email_content)
    
    def detect_resolved_team_action(self, email_content, thread_context=""):
        """Detect if a team action has already been addressed.
        
        Args:
            email_content: Email data to analyze
            thread_context: Thread conversation context
            
        Returns:
            tuple: (is_resolved, evidence_string)
        """
        if not thread_context:
            return False, "No thread context available"
        
        inputs = self._create_email_inputs(email_content, "")
        inputs['thread_context'] = thread_context
        
        result = self.prompt_manager.execute_prompty('team_action_resolution_detector.prompty', inputs)
        
        if not result:
            return False, "AI analysis unavailable"
        
        from utils import parse_json_with_fallback
        fallback_data = {'is_resolved': False, 'resolution_evidence': 'No evidence found', 'resolver': 'Unknown'}
        parsed = parse_json_with_fallback(result, fallback_data)
        
        if parsed and parsed != fallback_data:
            is_resolved = parsed.get('is_resolved', False)
            evidence = parsed.get('resolution_evidence', 'No evidence found')
            resolver = parsed.get('resolver', 'Unknown')
            return is_resolved, f"Resolution evidence: {evidence} (by {resolver})"
        
        # Fallback text analysis
        result_lower = result.lower()
        resolution_keywords = ['resolved', 'completed', 'done', 'fixed', 'handled', 'taken care of']
        is_resolved = any(keyword in result_lower for keyword in resolution_keywords)
        return is_resolved, f"Text analysis result: {result[:100]}"
    
    def check_optional_item_deadline(self, email_content, action_details=None):
        """Check if an optional item's deadline has passed.
        
        Args:
            email_content: Email data to analyze
            action_details: Optional pre-extracted action details
            
        Returns:
            tuple: (is_expired, deadline_info_string)
        """
        current_date = datetime.now()
        
        # Try to extract deadline from action details first
        if action_details and 'due_date' in action_details:
            due_date_str = action_details['due_date']
            if due_date_str and due_date_str != "No specific deadline":
                deadline = parse_date_string(due_date_str)
                if deadline and deadline < current_date:
                    return True, f"Deadline {due_date_str} has passed"
        
        # Use prompty for deadline analysis
        inputs = self._create_email_inputs(email_content, "")
        inputs['current_date'] = current_date.strftime('%Y-%m-%d')
        
        result = self.prompt_manager.execute_prompty('optional_item_deadline_checker.prompty', inputs)
        
        if not result:
            return False, "Unable to analyze deadline"
        
        from utils import parse_json_with_fallback
        fallback_data = {'is_expired': False, 'deadline_date': 'Unknown', 'deadline_type': 'general'}
        parsed = parse_json_with_fallback(result, fallback_data)
        
        if parsed and parsed != fallback_data:
            is_expired = parsed.get('is_expired', False)
            deadline_info = parsed.get('deadline_date', 'Unknown')
            deadline_type = parsed.get('deadline_type', 'general')
            
            if is_expired:
                return True, f"Expired {deadline_type} deadline: {deadline_info}"
            else:
                return False, f"Active or no deadline found: {deadline_info}"
        
        # Fallback text analysis
        result_lower = result.lower()
        expired_keywords = ['expired', 'passed', 'missed', 'closed', 'ended']
        is_expired = any(keyword in result_lower for keyword in expired_keywords)
        return is_expired, f"Text analysis: {result[:100]}"
    
    def analyze_inbox_holistically(self, all_email_data, job_context_func, username_func):
        """Analyze the entire inbox context to identify relevant actions.
        
        Args:
            all_email_data: List of all email data
            job_context_func: Function to get job context
            username_func: Function to get username
            
        Returns:
            tuple: (analysis_dict, status_message)
        """
        inbox_summary = self._build_inbox_context_summary(all_email_data)
        
        inputs = {
            'context': job_context_func(),
            'username': username_func(),
            'inbox_summary': inbox_summary,
            'current_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        result = self.prompt_manager.execute_prompty('holistic_inbox_analyzer.prompty', inputs)
        
        if not result:
            return None, "Holistic analysis unavailable"
        
        fallback_data = {
            "truly_relevant_actions": [],
            "superseded_actions": [],
            "duplicate_groups": [],
            "expired_items": []
        }
        
        from utils import parse_json_with_fallback
        analysis = parse_json_with_fallback(result, fallback_data)
        
        if analysis and analysis != fallback_data:
            return analysis, "Holistic analysis completed successfully"
        
        return fallback_data, "Analysis completed with parsing issues"
    
    def deduplicate_action_items(self, action_items):
        """Use AI to intelligently deduplicate action items.
        
        Args:
            action_items: List of action item dictionaries
            
        Returns:
            list: Deduplicated action items
        """
        if not action_items or len(action_items) <= 1:
            return action_items
        
        try:
            items_for_analysis = []
            for i, item in enumerate(action_items):
                item_summary = {
                    'id': f"item_{i+1}",
                    'subject': item.get('subject', 'No subject'),
                    'sender': item.get('sender', 'Unknown sender'),
                    'action_required': item.get('action_required', 'No action specified'),
                    'due_date': item.get('due_date', 'No deadline'),
                    'explanation': item.get('explanation', 'No details'),
                    'entry_id': item.get('_entry_id', 'No ID')
                }
                items_for_analysis.append(item_summary)
            
            inputs = {
                'action_items': json.dumps(items_for_analysis, indent=2)
            }
            
            print(f"[AI] Running advanced AI deduplication on {len(action_items)} action items...")
            result = self.prompt_manager.execute_prompty('action_item_deduplication.prompty', inputs)
            
            if result:
                from utils import parse_json_with_fallback
                dedup_result = parse_json_with_fallback(result.strip())
                if dedup_result and 'duplicates_found' in dedup_result:
                    return self._apply_deduplication_results(action_items, dedup_result)
                else:
                    print("[WARN] AI deduplication returned invalid format, keeping all items")
                    
        except Exception as e:
            print(f"[WARN] Advanced AI deduplication failed: {e}")
        
        return action_items
    
    def _build_inbox_context_summary(self, all_email_data):
        """Build comprehensive summary of all emails for holistic analysis."""
        from utils import format_date_for_display
        summary_parts = []
        
        for i, email_data in enumerate(all_email_data):
            entry_id = email_data.get('entry_id', f'email_{i}')
            subject = email_data.get('subject', 'Unknown Subject')
            sender = email_data.get('sender_name', email_data.get('sender', 'Unknown Sender'))
            received_time = email_data.get('received_time', 'Unknown Date')
            body_preview = email_data.get('body', '')[:300]
            if len(email_data.get('body', '')) > 300:
                body_preview += '...'
            
            date_str = format_date_for_display(received_time) if hasattr(received_time, 'strftime') else str(received_time)
            
            email_summary = f"""EMAIL_ID: {entry_id}
Subject: {subject}
From: {sender}
Date: {date_str}
Preview: {body_preview}
"""
            summary_parts.append(email_summary)
        
        return "\n---\n".join(summary_parts)
    
    def _apply_deduplication_results(self, original_items, dedup_result):
        """Apply AI deduplication results to merge related action items."""
        try:
            deduplicated_items = []
            processed_indices = set()
            duplicates_merged = 0
            
            for dup_group in dedup_result.get('duplicates_found', []):
                primary_id = dup_group.get('primary_item_id', '')
                duplicate_ids = dup_group.get('duplicate_item_ids', [])
                merged_action = dup_group.get('merged_action', '')
                merged_due_date = dup_group.get('merged_due_date', '')
                reason = dup_group.get('reason', 'Similar underlying task')
                confidence = dup_group.get('confidence', 0.0)
                
                try:
                    primary_idx = int(primary_id.replace('item_', '')) - 1
                    duplicate_indices = [int(id_.replace('item_', '')) - 1 for id_ in duplicate_ids]
                except (ValueError, AttributeError):
                    continue
                
                if 0 <= primary_idx < len(original_items) and all(0 <= idx < len(original_items) for idx in duplicate_indices):
                    primary_item = original_items[primary_idx].copy()
                    
                    if merged_action:
                        primary_item['action_required'] = merged_action
                    if merged_due_date and merged_due_date != 'earliest_deadline_from_group':
                        primary_item['due_date'] = merged_due_date
                    
                    # Find earliest deadline
                    all_indices = [primary_idx] + duplicate_indices
                    earliest_date = None
                    for idx in all_indices:
                        item_date = original_items[idx].get('due_date', '')
                        if item_date and item_date != 'No specific deadline':
                            try:
                                parsed_date = parse_date_string(item_date)
                                if parsed_date and (not earliest_date or parsed_date < earliest_date):
                                    earliest_date = parsed_date
                                    primary_item['due_date'] = item_date
                            except:
                                pass
                    
                    if 'contributing_emails' not in primary_item:
                        primary_item['contributing_emails'] = []
                    
                    for dup_idx in duplicate_indices:
                        dup_item = original_items[dup_idx]
                        contrib_info = {
                            'subject': dup_item.get('subject', ''),
                            'sender': dup_item.get('sender', ''),
                            'entry_id': dup_item.get('_entry_id', ''),
                            'merge_reason': reason,
                            'confidence': confidence
                        }
                        primary_item['contributing_emails'].append(contrib_info)
                    
                    original_explanation = primary_item.get('explanation', '')
                    primary_item['explanation'] = f"{original_explanation} [AI merged {len(duplicate_indices)} related reminder(s): {reason}]"
                    
                    deduplicated_items.append(primary_item)
                    processed_indices.update([primary_idx] + duplicate_indices)
                    duplicates_merged += len(duplicate_indices)
                    
                    try:
                        subject = primary_item.get('subject', 'Unknown')
                        subject_safe = subject[:50].encode('ascii', errors='replace').decode('ascii')
                    except:
                        subject_safe = 'Unknown'
                    print(f"   [MERGE] Merged {len(duplicate_indices)} duplicates: {subject_safe} - {reason}")
            
            for i, item in enumerate(original_items):
                if i not in processed_indices:
                    deduplicated_items.append(item)
            
            if duplicates_merged > 0:
                print(f"[OK] Advanced AI deduplication completed: {duplicates_merged} duplicates merged, {len(deduplicated_items)} unique items remain")
            
            return deduplicated_items
            
        except Exception as e:
            print(f"[WARN] Error applying deduplication results: {e}")
            return original_items
    
    def _create_email_inputs(self, email_content, context):
        """Create input dictionary for email extraction prompts."""
        return {
            'context': context,
            'subject': email_content.get('subject', ''),
            'sender': email_content.get('sender', ''),
            'date': email_content.get('date', ''),
            'body': email_content.get('body', '')[:8000]
        }
