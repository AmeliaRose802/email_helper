#!/usr/bin/env python3
"""
Accuracy Tracker - Monitors AI classification accuracy based on user corrections
"""

import os
import pandas as pd
from datetime import datetime, timedelta
import json


class AccuracyTracker:
    def __init__(self, runtime_data_dir):
        self.runtime_data_dir = runtime_data_dir
        self.user_feedback_dir = os.path.join(runtime_data_dir, 'user_feedback')
        self.accuracy_file = os.path.join(self.user_feedback_dir, 'accuracy_tracking.csv')
        self.accuracy_summary_file = os.path.join(self.user_feedback_dir, 'accuracy_summary.json')
        self.modifications_file = os.path.join(self.user_feedback_dir, 'suggestion_modifications.csv')
        self.batch_file = os.path.join(self.user_feedback_dir, 'ai_learning_feedback.csv')
        
        # Ensure directories exist
        os.makedirs(self.user_feedback_dir, exist_ok=True)
    
    def calculate_accuracy_for_session(self, total_emails_processed, user_modifications):
        """Calculate accuracy rate for the current session"""
        if total_emails_processed == 0:
            return 0.0
            
        # Accuracy = (emails_not_modified) / total_emails
        correct_predictions = total_emails_processed - len(user_modifications)
        accuracy_rate = (correct_predictions / total_emails_processed) * 100
        
        return round(accuracy_rate, 2)
    
    def record_session_accuracy(self, session_data):
        """Record accuracy metrics for a processing session"""
        accuracy_entry = {
            'timestamp': datetime.now().isoformat(),
            'run_id': session_data.get('run_id', self._generate_run_id()),
            'total_emails_processed': session_data['total_emails'],
            'emails_modified': session_data['modifications_count'],
            'emails_correct': session_data['total_emails'] - session_data['modifications_count'],
            'accuracy_rate': session_data['accuracy_rate'],
            'categories_used': session_data.get('categories_used', 0),
            'processing_errors': session_data.get('errors', 0),
            'session_duration_minutes': session_data.get('duration_minutes', 0),
            'modifications_by_category': json.dumps(session_data.get('category_modifications', {}))
        }
        
        # Save to CSV
        new_df = pd.DataFrame([accuracy_entry])
        
        if os.path.exists(self.accuracy_file):
            existing_df = pd.read_csv(self.accuracy_file)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined_df = new_df
            
        combined_df.to_csv(self.accuracy_file, index=False)
        print(f"📊 Accuracy metrics recorded: {session_data['accuracy_rate']:.1f}% accuracy")
    
    def get_accuracy_trends(self, days_back=30):
        """Get accuracy trends over the specified time period"""
        if not os.path.exists(self.accuracy_file):
            return None
            
        df = pd.read_csv(self.accuracy_file)
        if df.empty:
            return None
            
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filter to recent data
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_df = df[df['timestamp'] >= cutoff_date]
        
        if recent_df.empty:
            return None
            
        # Calculate trends
        trends = {
            'total_runs': len(recent_df),
            'total_emails_processed': recent_df['total_emails_processed'].sum(),
            'total_modifications': recent_df['emails_modified'].sum(),
            'average_accuracy': round(recent_df['accuracy_rate'].mean(), 2),
            'best_accuracy': recent_df['accuracy_rate'].max(),
            'worst_accuracy': recent_df['accuracy_rate'].min(),
            'latest_accuracy': recent_df.iloc[-1]['accuracy_rate'],
            'accuracy_improvement': self._calculate_improvement_trend(recent_df),
            'most_corrected_categories': self._analyze_category_corrections(recent_df),
            'date_range': {
                'start': recent_df['timestamp'].min().strftime('%Y-%m-%d'),
                'end': recent_df['timestamp'].max().strftime('%Y-%m-%d')
            }
        }
        
        return trends
    
    def _calculate_improvement_trend(self, df):
        """Calculate if accuracy is improving or declining"""
        if len(df) < 2:
            return "insufficient_data"
            
        # Compare first half vs second half of the period
        mid_point = len(df) // 2
        first_half_avg = df.iloc[:mid_point]['accuracy_rate'].mean()
        second_half_avg = df.iloc[mid_point:]['accuracy_rate'].mean()
        
        improvement = second_half_avg - first_half_avg
        
        if improvement > 2:
            return "improving"
        elif improvement < -2:
            return "declining"
        else:
            return "stable"
    
    def _analyze_category_corrections(self, df):
        """Analyze which categories get corrected most often"""
        category_corrections = {}
        
        for _, row in df.iterrows():
            try:
                modifications = json.loads(row['modifications_by_category'])
                for category, count in modifications.items():
                    category_corrections[category] = category_corrections.get(category, 0) + count
            except (json.JSONDecodeError, TypeError):
                continue
                
        # Sort by correction frequency
        sorted_corrections = sorted(category_corrections.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_corrections[:5])  # Top 5 most corrected categories
    
    def display_accuracy_report(self, days_back=30):
        """Display a comprehensive accuracy report"""
        trends = self.get_accuracy_trends(days_back)
        
        if not trends:
            print("📊 No accuracy data available yet.")
            print("   Run the email processor and make some corrections to start tracking accuracy.")
            return
            
        print(f"\n{'='*60}")
        print("📊 AI CLASSIFICATION ACCURACY REPORT")
        print(f"{'='*60}")
        print(f"📅 Period: {trends['date_range']['start']} to {trends['date_range']['end']}")
        print(f"🔄 Total runs: {trends['total_runs']}")
        print(f"📧 Emails processed: {trends['total_emails_processed']}")
        print(f"✏️  User corrections: {trends['total_modifications']}")
        
        print(f"\n📈 ACCURACY METRICS:")
        print(f"   Current accuracy: {trends['latest_accuracy']:.1f}%")
        print(f"   Average accuracy: {trends['average_accuracy']:.1f}%")
        print(f"   Best accuracy: {trends['best_accuracy']:.1f}%")
        print(f"   Worst accuracy: {trends['worst_accuracy']:.1f}%")
        
        # Trend analysis
        trend_emoji = {"improving": "📈", "declining": "📉", "stable": "➡️"}
        trend_text = {"improving": "Improving", "declining": "Declining", "stable": "Stable"}
        
        print(f"\n🎯 TREND ANALYSIS:")
        trend = trends['accuracy_improvement']
        print(f"   Overall trend: {trend_emoji.get(trend, '❓')} {trend_text.get(trend, 'Unknown')}")
        
        # Category analysis
        if trends['most_corrected_categories']:
            print(f"\n🔍 MOST CORRECTED CATEGORIES:")
            for category, count in trends['most_corrected_categories'].items():
                category_name = category.replace('_', ' ').title()
                print(f"   • {category_name}: {count} corrections")
                
        # Recommendations
        self._display_accuracy_recommendations(trends)
    
    def _display_accuracy_recommendations(self, trends):
        """Display recommendations based on accuracy trends"""
        print(f"\n💡 RECOMMENDATIONS:")
        
        accuracy = trends['average_accuracy']
        
        if accuracy >= 90:
            print("   🎉 Excellent accuracy! The AI is performing very well.")
        elif accuracy >= 80:
            print("   ✅ Good accuracy. Consider fine-tuning based on most corrected categories.")
        elif accuracy >= 70:
            print("   ⚠️  Moderate accuracy. Review classification rules and examples.")
        else:
            print("   🔴 Low accuracy. Consider updating prompts or adding more training examples.")
            
        if trends['accuracy_improvement'] == "declining":
            print("   📉 Accuracy is declining. Review recent changes or data quality issues.")
        elif trends['accuracy_improvement'] == "improving":
            print("   📈 Great! Accuracy is improving over time.")
            
        # Category-specific recommendations
        if trends['most_corrected_categories']:
            top_problematic = list(trends['most_corrected_categories'].keys())[0]
            print(f"   🎯 Focus improvement efforts on '{top_problematic.replace('_', ' ').title()}' category.")
    
    def _generate_run_id(self):
        """Generate a unique run ID"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def get_modifications_from_current_session(self):
        """Get user modifications from the current processing session"""
        if not os.path.exists(self.modifications_file):
            return []
            
        df = pd.read_csv(self.modifications_file)
        if df.empty:
            return []
            
        # Get modifications from today
        today = datetime.now().strftime('%Y-%m-%d')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        today_modifications = df[df['timestamp'].dt.strftime('%Y-%m-%d') == today]
        
        return today_modifications.to_dict('records')
    
    def analyze_category_accuracy(self):
        """Analyze accuracy by category to identify problem areas"""
        if not os.path.exists(self.modifications_file):
            return {}
            
        df = pd.read_csv(self.modifications_file)
        if df.empty:
            return {}
            
        # Count corrections by old category (what AI predicted incorrectly)
        category_errors = df['old_suggestion'].value_counts().to_dict()
        
        # Also look at what categories users prefer (new suggestions)
        preferred_categories = df['new_suggestion'].value_counts().to_dict()
        
        return {
            'frequently_incorrect': category_errors,
            'user_preferences': preferred_categories,
            'total_corrections': len(df)
        }
    
    def save_accuracy_summary(self, session_summary):
        """Save a summary of accuracy metrics for quick reference"""
        summary = {
            'last_updated': datetime.now().isoformat(),
            'latest_accuracy': session_summary['accuracy_rate'],
            'total_sessions': self._count_total_sessions(),
            'improvement_trend': self.get_accuracy_trends(7)['accuracy_improvement'] if self.get_accuracy_trends(7) else "no_data",
            'problem_categories': list(self.analyze_category_accuracy().get('frequently_incorrect', {}).keys())[:3]
        }
        
        with open(self.accuracy_summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
    
    def _count_total_sessions(self):
        """Count total number of processing sessions"""
        if not os.path.exists(self.accuracy_file):
            return 0
            
        df = pd.read_csv(self.accuracy_file)
        return len(df)
