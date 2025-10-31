"""Service for calculating AI classification accuracy statistics."""

from typing import Dict, List, Any
from collections import defaultdict
import logging

from backend.database.connection import db_manager

logger = logging.getLogger(__name__)


def calculate_accuracy_stats() -> Dict[str, Any]:
    """Calculate AI classification accuracy statistics.
    
    Compares ai_category (original AI prediction) with category (user-corrected)
    to determine accuracy metrics.
    
    Returns:
        Dictionary with overall and per-category accuracy statistics including:
        - total emails analyzed
        - overall accuracy percentage
        - per-category stats (total, correct, accuracy, precision, recall, f1)
    """
    with db_manager.get_connection() as conn:
        cursor = conn.execute(""""""
            SELECT ai_category, category
            FROM emails
            WHERE ai_category IS NOT NULL 
              AND ai_category != ''
              AND category IS NOT NULL
              AND category != ''
        """""")
        
        rows = cursor.fetchall()
    
    if not rows:
        return {
            "overall_accuracy": 0,
            "total_emails": 0,
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
        
        category_stats[ai_cat]['total'] += 1
        
        if ai_cat == user_cat:
            category_stats[ai_cat]['correct'] += 1
            category_stats[ai_cat]['true_positives'] += 1
            total_correct += 1
    
    # Second pass: calculate false positives and false negatives
    for ai_cat, user_cat in rows:
        ai_cat = ai_cat.lower()
        user_cat = user_cat.lower()
        
        if ai_cat != user_cat:
            category_stats[ai_cat]['false_positives'] += 1
            category_stats[user_cat]['false_negatives'] += 1
    
    # Calculate metrics for each category
    categories = []
    for cat, stats in category_stats.items():
        total = stats['total']
        correct = stats['correct']
        tp = stats['true_positives']
        fp = stats['false_positives']
        fn = stats['false_negatives']
        
        accuracy = (correct / total * 100) if total > 0 else 0
        precision = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 0
        recall = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0
        
        cat_display = cat.replace('_', ' ').title()
        
        categories.append({
            'category': cat_display,
            'total': total,
            'correct': correct,
            'accuracy': round(accuracy, 1),
            'precision': round(precision, 1),
            'recall': round(recall, 1),
            'f1': round(f1, 1),
            'truePositives': tp,
            'falsePositives': fp,
            'falseNegatives': fn
        })
    
    categories.sort(key=lambda x: x['total'], reverse=True)
    
    overall_accuracy = (total_correct / total_emails * 100) if total_emails > 0 else 0
    
    return {
        "overall_accuracy": round(overall_accuracy, 1),
        "total_emails": total_emails,
        "total_correct": total_correct,
        "categories": categories
    }
