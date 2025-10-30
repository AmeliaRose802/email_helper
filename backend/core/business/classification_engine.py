"""Email Classification Engine - AI-powered email categorization.

Pure business logic for email classification with confidence-based
auto-approval, few-shot learning, and comprehensive explanation generation.

This is PURE BUSINESS LOGIC - no async, no FastAPI, no framework dependencies.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from backend.core.infrastructure.text_utils import clean_ai_response
from backend.core.infrastructure.json_utils import parse_json_with_fallback

logger = logging.getLogger(__name__)


class ClassificationEngine:
    """Handles email classification with confidence thresholds and learning.
    
    Pure business logic for sophisticated email classification using AI with:
    - Asymmetric confidence thresholds per category
    - Few-shot learning from historical feedback
    - Fallback explanation generation
    - Auto-approval decision logic
    
    Attributes:
        CONFIDENCE_THRESHOLDS: Dict mapping categories to confidence thresholds
        AVAILABLE_CATEGORIES: List of valid email categories
    """
    
    # Confidence threshold configuration
    CONFIDENCE_THRESHOLDS = {
        'fyi': 0.9,
        'required_personal_action': 1.0,  # Always review
        'team_action': 1.0,  # Always review
        'optional_action': 0.8,
        'work_relevant': 0.8,
        'newsletter': 0.7,
        'spam_to_delete': 0.7,
        'job_listing': 0.8,
        'optional_event': 0.8
    }
    
    AVAILABLE_CATEGORIES = [
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
    
    def __init__(self, prompt_executor, context_manager):
        """Initialize classification engine.
        
        Args:
            prompt_executor: PromptExecutor instance
            context_manager: UserContextManager instance
        """
        self.prompt_executor = prompt_executor
        self.context_manager = context_manager
    
    def classify_email_with_explanation(self, email_content: dict, learning_data) -> Dict:
        """Classify email and provide detailed explanation.
        
        Args:
            email_content: Dict with email data
            learning_data: DataFrame of historical classification decisions
            
        Returns:
            dict: {'category': str, 'explanation': str}
        """
        # Get few-shot examples for better accuracy
        few_shot_examples = self._get_few_shot_examples(email_content, learning_data)
        
        # Build context with examples
        context = f"""{self.context_manager.get_standard_context()}
Learning History: {len(learning_data)} previous decisions"""
        
        if few_shot_examples:
            context += "\n\nSimilar Examples from Past Classifications:"
            for i, example in enumerate(few_shot_examples, 1):
                context += f"\n{i}. Subject: '{example['subject']}' → Category: {example['category']}"
        
        inputs = self.context_manager.create_email_inputs(email_content, context)
        result = self.prompt_executor.execute_prompty('email_classifier_with_explanation.prompty', inputs)
        
        if not result or result in ["AI processing unavailable", "AI processing failed"]:
            category = 'fyi'
            explanation = self._generate_explanation(email_content, category)
            return {'category': category, 'explanation': explanation}
        
        # Parse classification response
        fallback_category = 'fyi'
        fallback_data = {
            'category': fallback_category,
            'explanation': self._generate_explanation(email_content, fallback_category)
        }
        
        try:
            cleaned_result = clean_ai_response(result)
            parsed = parse_json_with_fallback(cleaned_result, fallback_data)
            
            if not isinstance(parsed, dict) or 'category' not in parsed:
                logger.warning(f"[Classification] Invalid format: {cleaned_result[:100]}")
                return fallback_data
            
            category = clean_ai_response(parsed.get('category', 'fyi')).lower()
            explanation = parsed.get('explanation', '')
            
            if not explanation or len(explanation.strip()) < 10:
                explanation = self._generate_explanation(email_content, category)
            
            return {'category': category, 'explanation': explanation}
            
        except Exception as e:
            logger.warning(f"[Classification] Parse error: {e}")
            return fallback_data
    
    def classify_email(self, email_content: dict, learning_data) -> str:
        """Basic classification returning only category.
        
        Args:
            email_content: Dict with email data
            learning_data: DataFrame of historical decisions
            
        Returns:
            str: Category name
        """
        result = self.classify_email_with_explanation(email_content, learning_data)
        return result.get('category', 'fyi')
    
    def apply_confidence_thresholds(
        self,
        classification_result: Dict,
        confidence_score: Optional[float] = None
    ) -> Dict:
        """Apply asymmetric confidence thresholds for auto-approval.
        
        Args:
            classification_result: Dict with 'category' and 'explanation'
            confidence_score: Optional confidence score (0.0-1.0)
            
        Returns:
            dict: Enhanced result with auto_approve, confidence, review_reason
        """
        category = classification_result.get('category', 'fyi')
        explanation = classification_result.get('explanation', '')
        
        # Estimate confidence if not provided
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
    
    def _get_few_shot_examples(
        self,
        email_content: dict,
        learning_data,
        max_examples: int = 5
    ) -> List[Dict]:
        """Get relevant few-shot examples from learning data.
        
        Args:
            email_content: Current email data
            learning_data: DataFrame of historical classifications
            max_examples: Maximum number of examples to return
            
        Returns:
            list: List of example dicts with subject, sender, body, category
        """
        if learning_data.empty:
            return []
        
        # Filter for successful classifications
        successful = learning_data[
            learning_data.get('user_modified', False) == False
        ].copy() if 'user_modified' in learning_data.columns else learning_data.copy()
        
        if successful.empty:
            return []
        
        current_subject = email_content.get('subject', '').lower()
        current_sender = email_content.get('sender', '').lower()
        current_body = email_content.get('body', '').lower()
        
        examples_with_scores = []
        
        for _, row in successful.iterrows():
            score = 0
            row_subject = str(row.get('subject', '')).lower()
            row_sender = str(row.get('sender', '')).lower()
            row_body = str(row.get('body', '')).lower()[:1000]
            
            # Subject similarity
            subject_words = set(current_subject.split())
            row_subject_words = set(row_subject.split())
            if subject_words and row_subject_words:
                score += len(subject_words.intersection(row_subject_words)) / \
                        len(subject_words.union(row_subject_words)) * 3
            
            # Sender similarity
            if current_sender and row_sender:
                if current_sender in row_sender or row_sender in current_sender:
                    score += 2
            
            # Body keyword overlap
            body_words = set(w for w in current_body.split() if len(w) > 3)
            row_body_words = set(w for w in row_body.split() if len(w) > 3)
            if body_words and row_body_words:
                score += len(body_words.intersection(row_body_words)) / \
                        len(body_words.union(row_body_words)) * 1
            
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
    
    def _generate_explanation(self, email_content: dict, category: str) -> str:
        """Generate fallback explanation when AI fails.
        
        Args:
            email_content: Email data
            category: Classification category
            
        Returns:
            str: Human-readable explanation
        """
        subject = email_content.get('subject', 'Unknown')
        sender = email_content.get('sender', 'Unknown')
        
        explanations = {
            'required_personal_action': f"Email from {sender} appears to require personal action based on direct addressing.",
            'team_action': f"Email indicates action required from your team.",
            'optional_action': f"Email contains optional activities that may be worth considering.",
            'work_relevant': f"Email contains work-related information but requires no immediate action.",
            'fyi': f"Email is informational only with no action required.",
            'newsletter': f"Email appears to be a newsletter or bulk distribution.",
            'spam_to_delete': f"Email does not appear relevant to work.",
            'job_listing': f"Email contains job opportunities or recruitment content.",
            'optional_event': f"Email contains optional event invitation."
        }
        
        base = explanations.get(category, f"Classified as {category} based on content analysis.")
        return f"{base} Subject: '{subject[:50]}...'"
