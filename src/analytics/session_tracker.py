"""Session tracking for accuracy and modifications"""

from datetime import datetime
from utils.date_utils import get_timestamp, get_run_id


class SessionTracker:
    def __init__(self, accuracy_tracker):
        self.accuracy_tracker = accuracy_tracker
        self.session_start_time = datetime.now()
        self.session_total_emails = 0
        self.session_modifications = []
    
    def start_accuracy_session(self, total_emails):
        self.session_start_time = datetime.now()
        self.session_total_emails = total_emails
        self.session_modifications = []
    
    def add_modification(self, old_category, new_category):
        self.session_modifications.append({
            'old_category': old_category,
            'new_category': new_category,
            'timestamp': datetime.now()
        })
    
    def finalize_session(self, success_count=None, error_count=None, categories_used=None):
        print(f"🔍 FINALIZE SESSION: total_emails={self.session_total_emails}, modifications={len(self.session_modifications)}")
        if self.session_total_emails == 0:
            print("⚠️ Early return: session_total_emails is 0")
            return
            
        modifications_count = len(self.session_modifications)
        accuracy_rate = self.accuracy_tracker.calculate_accuracy_for_session(
            self.session_total_emails, self.session_modifications
        )
        
        category_modifications = {}
        for mod in self.session_modifications:
            old_cat = mod['old_category']
            category_modifications[old_cat] = category_modifications.get(old_cat, 0) + 1
        
        session_data = {
            'run_id': get_run_id(),
            'total_emails': self.session_total_emails,
            'modifications_count': modifications_count,
            'accuracy_rate': accuracy_rate,
            'category_modifications': category_modifications
        }
        
        self.accuracy_tracker.record_session_accuracy(session_data)
        print(f"Session: {self.session_total_emails} emails, {modifications_count} corrections, {accuracy_rate:.1f}% accuracy")
