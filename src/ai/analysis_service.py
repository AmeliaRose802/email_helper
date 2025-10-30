"""Email Analysis Services - Deduplication, deadline checking, and holistic analysis.

This module provides advanced email analysis including:
- AI-powered action item deduplication
- Deadline checking for optional items
- Team action resolution detection
- Holistic inbox context analysis
"""

import json
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from utils import parse_json_with_fallback, parse_date_string, format_date_for_display

logger = logging.getLogger(__name__)


class EmailAnalysisService:
    """Advanced email analysis and intelligence services.
    
    Provides sophisticated analysis features:
    - AI-based action item deduplication
    - Expired deadline detection
    - Team action resolution tracking
    - Whole-inbox holistic analysis
    """
    
    def __init__(self, prompt_executor, context_manager):
        """Initialize analysis service.
        
        Args:
            prompt_executor: Object with execute_prompty method
            context_manager: UserContextManager for context
        """
        self.prompt_executor = prompt_executor
        self.context_manager = context_manager
    
    def advanced_deduplicate_action_items(self, action_items: List[Dict]) -> List[Dict]:
        """Use AI to intelligently deduplicate action items.
        
        Args:
            action_items: List of action item dicts
            
        Returns:
            list: Deduplicated action items with merge tracking
        """
        if not action_items or len(action_items) <= 1:
            return action_items
        
        try:
            # Format for AI analysis
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
            
            inputs = {'action_items': json.dumps(items_for_analysis, indent=2)}
            
            logger.info(f"[Deduplication] Running AI on {len(action_items)} items")
            result = self.prompt_executor.execute_prompty('action_item_deduplication.prompty', inputs)
            
            if result:
                dedup_result = parse_json_with_fallback(result.strip())
                if dedup_result and 'duplicates_found' in dedup_result:
                    return self._apply_deduplication_results(action_items, dedup_result)
                logger.warning("[Deduplication] Invalid AI response format")
                
        except Exception as e:
            logger.warning(f"[Deduplication] Failed: {e}")
        
        return action_items
    
    def check_optional_item_deadline(
        self,
        email_content: dict,
        action_details: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """Check if optional item's deadline has passed.
        
        Args:
            email_content: Email data dict
            action_details: Optional action details with due_date
            
        Returns:
            tuple: (is_expired: bool, reason: str)
        """
        current_date = datetime.now()
        
        # Check action details first
        if action_details and 'due_date' in action_details:
            due_date_str = action_details['due_date']
            if due_date_str and due_date_str != "No specific deadline":
                deadline = parse_date_string(due_date_str)
                if deadline and deadline < current_date:
                    return True, f"Deadline {due_date_str} has passed"
        
        # Use AI for deadline analysis
        inputs = self.context_manager.create_email_inputs(
            email_content,
            self.context_manager.get_standard_context()
        )
        inputs['current_date'] = current_date.strftime('%Y-%m-%d')
        
        result = self.prompt_executor.execute_prompty('optional_item_deadline_checker.prompty', inputs)
        
        if not result:
            return False, "Unable to analyze deadline"
        
        fallback_data = {
            'is_expired': False,
            'deadline_date': 'Unknown',
            'deadline_type': 'general'
        }
        parsed = parse_json_with_fallback(result, fallback_data)
        
        if parsed and parsed != fallback_data:
            is_expired = parsed.get('is_expired', False)
            deadline_info = parsed.get('deadline_date', 'Unknown')
            deadline_type = parsed.get('deadline_type', 'general')
            
            if is_expired:
                return True, f"Expired {deadline_type} deadline: {deadline_info}"
            return False, f"Active or no deadline found: {deadline_info}"
        
        # Text analysis fallback
        result_lower = result.lower()
        expired_keywords = ['expired', 'passed', 'missed', 'closed', 'ended']
        is_expired = any(keyword in result_lower for keyword in expired_keywords)
        return is_expired, f"Text analysis: {result[:100]}"
    
    def detect_resolved_team_action(
        self,
        email_content: dict,
        thread_context: str = ""
    ) -> Tuple[bool, str]:
        """Detect if team action already handled by someone else.
        
        Args:
            email_content: Email data dict
            thread_context: Email thread history
            
        Returns:
            tuple: (is_resolved: bool, evidence: str)
        """
        if not thread_context:
            return False, "No thread context available"
        
        inputs = self.context_manager.create_email_inputs(
            email_content,
            self.context_manager.get_standard_context()
        )
        inputs['thread_context'] = thread_context
        
        result = self.prompt_executor.execute_prompty('team_action_resolution_detector.prompty', inputs)
        
        if not result:
            return False, "AI analysis unavailable"
        
        fallback_data = {
            'is_resolved': False,
            'resolution_evidence': 'No evidence found',
            'resolver': 'Unknown'
        }
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
    
    def analyze_inbox_holistically(self, all_email_data: List[Dict]) -> Tuple[Optional[Dict], str]:
        """Analyze entire inbox to identify truly relevant actions and relationships.
        
        Args:
            all_email_data: List of all email data dicts
            
        Returns:
            tuple: (analysis_dict or None, status_message)
        """
        inbox_summary = self._build_inbox_context_summary(all_email_data)
        
        inputs = {
            'context': self.context_manager.get_standard_context(),
            'job_role_context': self.context_manager.get_job_role_context(),
            'username': self.context_manager.get_username(),
            'inbox_summary': inbox_summary,
            'current_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        result = self.prompt_executor.execute_prompty('holistic_inbox_analyzer.prompty', inputs)
        
        if not result:
            return None, "Holistic analysis unavailable"
        
        fallback_data = {
            "truly_relevant_actions": [],
            "superseded_actions": [],
            "duplicate_groups": [],
            "expired_items": []
        }
        
        analysis = parse_json_with_fallback(result, fallback_data)
        
        if analysis and analysis != fallback_data:
            return analysis, "Holistic analysis completed successfully"
        
        return fallback_data, "Analysis completed with parsing issues"
    
    def _build_inbox_context_summary(self, all_email_data: List[Dict]) -> str:
        """Build comprehensive inbox summary for holistic analysis.
        
        Args:
            all_email_data: List of email dicts
            
        Returns:
            str: Formatted inbox summary
        """
        summary_parts = []
        
        for i, email_data in enumerate(all_email_data):
            entry_id = email_data.get('entry_id', f'email_{i}')
            subject = email_data.get('subject', 'Unknown Subject')
            sender = email_data.get('sender_name', email_data.get('sender', 'Unknown Sender'))
            received_time = email_data.get('received_time', 'Unknown Date')
            body_preview = email_data.get('body', '')[:300]
            if len(email_data.get('body', '')) > 300:
                body_preview += '...'
            
            date_str = format_date_for_display(received_time) \
                if hasattr(received_time, 'strftime') else str(received_time)
            
            email_summary = f"""EMAIL_ID: {entry_id}
Subject: {subject}
From: {sender}
Date: {date_str}
Preview: {body_preview}
"""
            summary_parts.append(email_summary)
        
        return "\n---\n".join(summary_parts)
    
    def _apply_deduplication_results(
        self,
        original_items: List[Dict],
        dedup_result: Dict
    ) -> List[Dict]:
        """Apply AI deduplication results to merge related items.
        
        Args:
            original_items: Original action item list
            dedup_result: AI deduplication analysis result
            
        Returns:
            list: Deduplicated items with merge tracking
        """
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
                
                # Extract indices
                try:
                    primary_idx = int(primary_id.replace('item_', '')) - 1
                    duplicate_indices = [int(id_.replace('item_', '')) - 1 for id_ in duplicate_ids]
                except (ValueError, AttributeError):
                    continue
                
                # Validate indices
                if not (0 <= primary_idx < len(original_items) and
                       all(0 <= idx < len(original_items) for idx in duplicate_indices)):
                    continue
                
                # Create merged item
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
                
                # Track contributing emails
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
                
                # Enhanced explanation
                original_explanation = primary_item.get('explanation', '')
                primary_item['explanation'] = \
                    f"{original_explanation} [AI merged {len(duplicate_indices)} related reminder(s): {reason}]"
                
                deduplicated_items.append(primary_item)
                processed_indices.update([primary_idx] + duplicate_indices)
                duplicates_merged += len(duplicate_indices)
                
                logger.info(f"[Deduplication] Merged {len(duplicate_indices)} into '{primary_item.get('subject', 'Unknown')}': {reason}")
            
            # Add remaining unique items
            for i, item in enumerate(original_items):
                if i not in processed_indices:
                    deduplicated_items.append(item)
            
            if duplicates_merged > 0:
                logger.info(f"[Deduplication] Complete: {duplicates_merged} merged, {len(deduplicated_items)} unique remain")
            
            return deduplicated_items
            
        except Exception as e:
            logger.warning(f"[Deduplication] Error applying results: {e}")
            return original_items
