"""Email accuracy tracking service for monitoring AI classification accuracy.

This service calculates accuracy statistics comparing AI predictions
with user-corrected classifications.
"""

import asyncio
import logging
from collections import defaultdict
from typing import Dict, Any

from backend.database.connection import db_manager


# Configure module logger
logger = logging.getLogger(__name__)


class AccuracyError(Exception):
    """Base exception for accuracy tracking errors."""
    pass


class EmailAccuracyService:
    """Service for tracking AI classification accuracy."""

    def __init__(self):
        """Initialize the accuracy tracking service."""
        pass

    async def get_accuracy_statistics(self) -> Dict[str, Any]:
        """Calculate AI classification accuracy statistics.

        Compares ai_category (original AI prediction) with category (user-corrected)
        to determine accuracy metrics.

        Returns:
            Dictionary with overall and per-category accuracy statistics

        Raises:
            AccuracyError: If database query fails
        """
        try:
            loop = asyncio.get_event_loop()

            def _calculate_accuracy_sync():
                with db_manager.get_connection() as conn:
                    # Get all emails with both AI and user categories
                    cursor = conn.execute("""
                        SELECT ai_category, category
                        FROM emails
                        WHERE ai_category IS NOT NULL 
                          AND ai_category != ''
                          AND category IS NOT NULL
                          AND category != ''
                    """)

                    rows = cursor.fetchall()

                if not rows:
                    return {
                        "overall_accuracy": 0,
                        "total_emails": 0,
                        "total_correct": 0,
                        "categories": []
                    }

                # Calculate per-category statistics
                category_stats = defaultdict(lambda: {
                    'total': 0,
                    'correct': 0,
                    'true_positives': 0,
                    'false_positives': 0,
                    'false_negatives': 0
                })

                total_emails = len(rows)
                total_correct = 0

                # First pass: count totals and correct classifications
                for ai_cat, user_cat in rows:
                    ai_cat = ai_cat.lower()
                    user_cat = user_cat.lower()

                    # Track per category
                    category_stats[ai_cat]['total'] += 1
                    category_stats[user_cat]['true_positives'] += 1

                    if ai_cat == user_cat:
                        category_stats[ai_cat]['correct'] += 1
                        total_correct += 1
                    else:
                        # False positive for AI prediction
                        category_stats[ai_cat]['false_positives'] += 1
                        # False negative for true category
                        category_stats[user_cat]['false_negatives'] += 1

                # Calculate overall accuracy
                overall_accuracy = (total_correct / total_emails * 100) if total_emails > 0 else 0

                # Format per-category statistics
                categories = []
                for category, stats in category_stats.items():
                    accuracy = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0

                    # Calculate precision and recall
                    tp = stats['true_positives']
                    fp = stats['false_positives']
                    fn = stats['false_negatives']

                    precision = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 0
                    recall = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 0
                    f1_score = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0

                    categories.append({
                        'category': category,
                        'total': stats['total'],
                        'correct': stats['correct'],
                        'accuracy': round(accuracy, 2),
                        'precision': round(precision, 2),
                        'recall': round(recall, 2),
                        'f1_score': round(f1_score, 2)
                    })

                # Sort by total count (most common categories first)
                categories.sort(key=lambda x: x['total'], reverse=True)

                return {
                    "overall_accuracy": round(overall_accuracy, 2),
                    "total_emails": total_emails,
                    "total_correct": total_correct,
                    "categories": categories
                }

            result = await loop.run_in_executor(None, _calculate_accuracy_sync)

            logger.info(f"[Accuracy] Overall accuracy: {result['overall_accuracy']}% "
                       f"({result['total_correct']}/{result['total_emails']})")

            return result

        except Exception as e:
            logger.error(f"[Accuracy] Failed to calculate accuracy statistics: {e}")
            raise AccuracyError(f"Accuracy calculation failed: {str(e)}")
