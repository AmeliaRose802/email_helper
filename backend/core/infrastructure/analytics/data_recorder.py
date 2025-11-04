"""Data recorder for AI learning feedback and analytics."""
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DataRecorder:
    """Records AI feedback and decisions for learning and improvement."""

    def __init__(self, runtime_data_dir):
        self.runtime_data_dir = runtime_data_dir
        self.learning_file = os.path.join(runtime_data_dir, 'ai_learning_feedback.csv')
        self.batch_results_file = os.path.join(runtime_data_dir, 'batch_results.json')
        self.modifications_file = os.path.join(runtime_data_dir, 'user_modifications.json')
        self.accepted_suggestions_file = os.path.join(runtime_data_dir, 'accepted_suggestions.json')
        os.makedirs(runtime_data_dir, exist_ok=True)

    def record_learning_feedback(self, feedback_entries):
        """Record AI learning feedback to CSV."""
        if not feedback_entries:
            return

        import csv
        file_exists = os.path.exists(self.learning_file)

        try:
            with open(self.learning_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['timestamp', 'email_id', 'category', 'confidence', 'user_feedback'])
                if not file_exists:
                    writer.writeheader()
                for entry in feedback_entries:
                    writer.writerow(entry)
            logger.info(f"[DataRecorder] Recorded {len(feedback_entries)} learning feedback entries")
        except Exception as e:
            logger.error(f"[DataRecorder] Failed to record learning feedback: {e}")

    def record_batch_processing(self, success_count, error_count, categories_used):
        """Record batch processing results."""
        try:
            result = {
                'timestamp': datetime.now().isoformat(),
                'success_count': success_count,
                'error_count': error_count,
                'categories_used': categories_used
            }

            results = []
            if os.path.exists(self.batch_results_file):
                with open(self.batch_results_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)

            results.append(result)

            with open(self.batch_results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)

            logger.info(f"[DataRecorder] Recorded batch: {success_count} success, {error_count} errors")
        except Exception as e:
            logger.error(f"[DataRecorder] Failed to record batch processing: {e}")

    def record_suggestion_modification(self, email_data, old_category, new_category, user_explanation):
        """Record user modification of AI suggestions."""
        try:
            modification = {
                'timestamp': datetime.now().isoformat(),
                'email_id': email_data.get('id', 'unknown'),
                'subject': email_data.get('subject', '')[:100],
                'old_category': old_category,
                'new_category': new_category,
                'user_explanation': user_explanation
            }

            modifications = []
            if os.path.exists(self.modifications_file):
                with open(self.modifications_file, 'r', encoding='utf-8') as f:
                    modifications = json.load(f)

            modifications.append(modification)

            with open(self.modifications_file, 'w', encoding='utf-8') as f:
                json.dump(modifications, f, indent=2)

            logger.info(f"[DataRecorder] Recorded modification: {old_category} -> {new_category}")
        except Exception as e:
            logger.error(f"[DataRecorder] Failed to record modification: {e}")

    def record_accepted_suggestions(self, email_suggestions):
        """Record accepted AI suggestions for fine-tuning data."""
        if not email_suggestions:
            return

        try:
            batch = {
                'timestamp': datetime.now().isoformat(),
                'count': len(email_suggestions),
                'suggestions': email_suggestions
            }

            batches = []
            if os.path.exists(self.accepted_suggestions_file):
                with open(self.accepted_suggestions_file, 'r', encoding='utf-8') as f:
                    batches = json.load(f)

            batches.append(batch)

            with open(self.accepted_suggestions_file, 'w', encoding='utf-8') as f:
                json.dump(batches, f, indent=2)

            logger.info(f"[DataRecorder] Recorded {len(email_suggestions)} accepted suggestions")
        except Exception as e:
            logger.error(f"[DataRecorder] Failed to record accepted suggestions: {e}")
