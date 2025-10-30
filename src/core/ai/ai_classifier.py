"""AI Classifier - Email Classification Logic.

This module handles email classification using AI, including
few-shot learning and confidence threshold management.
"""

import logging
from datetime import datetime
from .prompt_manager import PromptManager
from .response_parser import ResponseParser

logger = logging.getLogger(__name__)


class AIClassifier:
    """Handles email classification using AI.
    
    This class is responsible for classifying emails into categories,
    managing few-shot learning examples, and applying confidence thresholds
    for auto-approval decisions.
    """
    
    # Confidence threshold configuration
    CONFIDENCE_THRESHOLDS = {
        'fyi': 0.9,
        'required_personal_action': 1.0,
        'team_action': 1.0,
        'optional_action': 0.8,
        'work_relevant': 0.8,
        'newsletter': 0.7,
        'spam_to_delete': 0.7,
        'job_listing': 0.8,
        'optional_event': 0.8
    }
    
    def __init__(self, prompt_manager: PromptManager, response_parser: ResponseParser):
        """Initialize the classifier.
        
        Args:
            prompt_manager: PromptManager instance for executing prompts
            response_parser: ResponseParser instance for parsing responses
        """
        self.prompt_manager = prompt_manager
        self.response_parser = response_parser
    
    def classify_email(self, email_content, context, learning_data):
        """Classify email with explanation.
        
        Args:
            email_content: Email data to classify
            context: Job context and user information
            learning_data: Historical classification data for few-shot learning
            
        Returns:
            dict: Classification result with category and explanation
        """
        subject = email_content.get('subject', 'No subject')
        logger.info(f"[AIClassifier] Classifying email: {subject[:50]}...")
        
        # Get few-shot examples
        few_shot_examples = self._get_few_shot_examples(email_content, learning_data)
        
        # Build enhanced context
        enhanced_context = context
        if few_shot_examples:
            enhanced_context += "\n\nSimilar Examples from Past Classifications:"
            for i, example in enumerate(few_shot_examples, 1):
                enhanced_context += f"\n{i}. Subject: '{example['subject']}' → Category: {example['category']}"
        
        # Create inputs
        inputs = self._create_email_inputs(email_content, enhanced_context)
        
        # Execute classification prompt
        result = self.prompt_manager.execute_prompty('email_classifier_with_explanation.prompty', inputs)
        
        # Parse response
        classification = self.response_parser.parse_classification_response(
            result, email_content
        )
        
        logger.info(f"[AIClassifier] [OK] Classification: {classification['category']}")
        return classification
    
    def apply_confidence_thresholds(self, classification_result, confidence_score=None):
        """Apply asymmetric confidence thresholds for auto-approval decisions.
        
        Args:
            classification_result: Classification result dict
            confidence_score: Optional confidence score (estimated if not provided)
            
        Returns:
            dict: Enhanced result with confidence and auto-approval decision
        """
        category = classification_result.get('category', 'fyi')
        explanation = classification_result.get('explanation', '')
        
        if confidence_score is None:
            confidence_score = min(0.8, 0.3 + len(explanation.split()) * 0.05)
        
        threshold = self.CONFIDENCE_THRESHOLDS.get(category, 0.8)
        auto_approve = confidence_score >= threshold
        
        if not auto_approve:
            if category in ['required_personal_action', 'team_action']:
                review_reason = 'High priority category'
            else:
                review_reason = f'Low confidence ({confidence_score:.1%} < {threshold:.1%})'
        else:
            review_reason = f'Auto-approved ({confidence_score:.1%} ≥ {threshold:.1%})'
        
        return {
            'category': category,
            'explanation': explanation,
            'confidence': confidence_score,
            'auto_approve': auto_approve,
            'review_reason': review_reason,
            'threshold': threshold
        }
    
    def get_available_categories(self):
        """Get list of available email categories for classification."""
        return [
            'required_personal_action',
            'team_action',
            'optional_action',
            'work_relevant',
            'fyi',
            'newsletter',
            'spam_to_delete',
            'job_listing',
            'optional_event'
        ]
    
    def _get_few_shot_examples(self, email_content, learning_data, max_examples=5):
        """Get relevant few-shot examples from learning data."""
        if isinstance(learning_data, list):
            if not learning_data:
                return []
            return []
        
        if not hasattr(learning_data, 'empty'):
            return []
        
        if learning_data.empty:
            return []
        
        successful_classifications = learning_data[
            learning_data.get('user_modified', False) == False
        ].copy() if 'user_modified' in learning_data.columns else learning_data.copy()
        
        if successful_classifications.empty:
            return []
        
        current_subject = email_content.get('subject', '').lower()
        current_sender = email_content.get('sender', '').lower()
        current_body = email_content.get('body', '').lower()
        
        examples_with_scores = []
        
        for _, row in successful_classifications.iterrows():
            score = 0
            row_subject = str(row.get('subject', '')).lower()
            row_sender = str(row.get('sender', '')).lower()
            row_body = str(row.get('body', '')).lower()[:1000]
            
            # Subject similarity
            subject_words = set(current_subject.split())
            row_subject_words = set(row_subject.split())
            if subject_words and row_subject_words:
                score += len(subject_words.intersection(row_subject_words)) / len(subject_words.union(row_subject_words)) * 3
            
            # Sender similarity
            if current_sender and row_sender:
                if current_sender in row_sender or row_sender in current_sender:
                    score += 2
            
            # Body keyword overlap
            body_words = set(w for w in current_body.split() if len(w) > 3)
            row_body_words = set(w for w in row_body.split() if len(w) > 3)
            if body_words and row_body_words:
                score += len(body_words.intersection(row_body_words)) / len(body_words.union(row_body_words)) * 1
            
            if score > 0:
                examples_with_scores.append((score, row))
        
        examples_with_scores.sort(key=lambda x: x[0], reverse=True)
        
        examples = []
        for score, row in examples_with_scores[:max_examples]:
            example = {
                'subject': str(row.get('subject', ''))[:100],
                'sender': str(row.get('sender', ''))[:50],
                'body': str(row.get('body', ''))[:300],
                'category': str(row.get('category', 'fyi'))
            }
            examples.append(example)
        
        return examples
    
    def _create_email_inputs(self, email_content, context):
        """Create input dictionary for email classification prompts."""
        return {
            'context': context,
            'subject': email_content.get('subject', ''),
            'sender': email_content.get('sender', ''),
            'date': email_content.get('date', ''),
            'body': email_content.get('body', '')[:8000]
        }
