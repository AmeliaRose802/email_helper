"""Data recording and persistence for AI learning"""

import os
from utils import save_to_csv, normalize_data_for_storage, get_timestamp, format_datetime_for_storage


class DataRecorder:
    def __init__(self, runtime_data_dir):
        self.runtime_data_dir = runtime_data_dir
        self.learning_file = os.path.join(runtime_data_dir, 'ai_learning_feedback.csv')
        self.modification_file = os.path.join(runtime_data_dir, 'suggestion_modifications.csv')
    
    def record_learning_feedback(self, feedback_entries):
        """Save learning feedback to improve AI over time"""
        processed_entries = normalize_data_for_storage(feedback_entries)
        save_to_csv(processed_entries, self.learning_file)
    
    def record_batch_processing(self, success_count, error_count, categories_used):
        """Record batch processing results for learning"""
        batch_entry = [{
            'timestamp': get_timestamp(),
            'action': 'batch_categorization',
            'emails_processed': success_count + error_count,
            'successful': success_count,
            'errors': error_count,
            'categories_used': categories_used
        }]
        
        save_to_csv(batch_entry, self.learning_file)
    
    def record_suggestion_modification(self, email_data, old_category, new_category, user_explanation):
        email_date = email_data.get('date', email_data.get('received_time', 'Unknown'))
        if hasattr(email_date, 'strftime'):
            email_date = format_datetime_for_storage(email_date)
            
        modification_entry = [{
            'timestamp': get_timestamp(),
            'subject': email_data.get('subject', 'Unknown'),
            'sender': email_data.get('sender', 'Unknown'),
            'email_date': str(email_date),
            'old_suggestion': old_category,
            'new_suggestion': new_category,
            'user_explanation': user_explanation,
            'body_preview': email_data.get('body', '')[:200]
        }]
        
        save_to_csv(modification_entry, self.modification_file)
    
    def record_accepted_suggestions(self, email_suggestions):
        """Record all accepted suggestions that were applied to Outlook for fine-tuning data"""
        accepted_file = os.path.join(self.runtime_data_dir, 'accepted_suggestions.csv')
        
        accepted_entries = []
        for suggestion_data in email_suggestions:
            email_data = suggestion_data.get('email_data', {})
            suggestion = suggestion_data.get('ai_suggestion', 'unknown')
            initial_classification = suggestion_data.get('initial_classification', suggestion)
            processing_notes = suggestion_data.get('processing_notes', [])
            ai_summary = suggestion_data.get('ai_summary', '')
            
            # Determine if this was modified or accepted as-is
            was_modified = suggestion != initial_classification
            modification_reason = "User modified in review" if was_modified else "Accepted as suggested"
            
            # Get email date
            email_date = email_data.get('received_time', email_data.get('date', 'Unknown'))
            if hasattr(email_date, 'strftime'):
                email_date = format_datetime_for_storage(email_date)
            
            accepted_entry = {
                'timestamp': get_timestamp(),
                'subject': email_data.get('subject', 'Unknown'),
                'sender': email_data.get('sender_name', email_data.get('sender', 'Unknown')),
                'email_date': str(email_date),
                'initial_ai_suggestion': initial_classification,
                'final_applied_category': suggestion,
                'was_modified': was_modified,
                'modification_reason': modification_reason,
                'processing_notes': '; '.join(processing_notes) if processing_notes else '',
                'ai_summary': ai_summary[:500],
                'body_preview': email_data.get('body', '')[:300],
                'thread_count': suggestion_data.get('thread_data', {}).get('thread_count', 1)
            }
            accepted_entries.append(accepted_entry)
        
        if accepted_entries:
            save_to_csv(accepted_entries, accepted_file)
            print(f"📊 Recorded {len(accepted_entries)} accepted suggestions for fine-tuning data")
