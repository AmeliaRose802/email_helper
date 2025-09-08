import os
import pandas as pd
from datetime import datetime, timedelta
import json


class AccuracyTracker:
    def __init__(self, runtime_data_dir):
        self.user_feedback_dir = os.path.join(runtime_data_dir, 'user_feedback')
        self.accuracy_file = os.path.join(self.user_feedback_dir, 'accuracy_tracking.csv')
        self.modifications_file = os.path.join(self.user_feedback_dir, 'suggestion_modifications.csv')
        os.makedirs(self.user_feedback_dir, exist_ok=True)
    
    def calculate_accuracy_for_session(self, total_emails_processed, user_modifications):
        if total_emails_processed == 0:
            return 0.0
        correct_predictions = total_emails_processed - len(user_modifications)
        return round((correct_predictions / total_emails_processed) * 100, 2)
    
    def record_session_accuracy(self, session_data):
        accuracy_entry = {
            'timestamp': datetime.now().isoformat(),
            'run_id': session_data.get('run_id', datetime.now().strftime("%Y%m%d_%H%M%S")),
            'total_emails_processed': session_data['total_emails'],
            'emails_modified': session_data['modifications_count'],
            'accuracy_rate': session_data['accuracy_rate'],
            'modifications_by_category': json.dumps(session_data.get('category_modifications', {}))
        }
        
        new_df = pd.DataFrame([accuracy_entry])
        
        if os.path.exists(self.accuracy_file):
            existing_df = pd.read_csv(self.accuracy_file)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined_df = new_df
            
        combined_df.to_csv(self.accuracy_file, index=False)
    
    def get_accuracy_trends(self, days_back=30):
        if not os.path.exists(self.accuracy_file):
            return None
            
        df = pd.read_csv(self.accuracy_file)
        if df.empty:
            return None
            
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_df = df[df['timestamp'] >= cutoff_date]
        
        if recent_df.empty:
            return None
            
        return {
            'total_runs': len(recent_df),
            'total_emails_processed': recent_df['total_emails_processed'].sum(),
            'total_modifications': recent_df['emails_modified'].sum(),
            'average_accuracy': round(recent_df['accuracy_rate'].mean(), 2),
            'latest_accuracy': recent_df.iloc[-1]['accuracy_rate'],
            'improvement_trend': self._calculate_improvement_trend(recent_df),
            'most_corrected_categories': self._analyze_category_corrections(recent_df),
        }
    
    def _calculate_improvement_trend(self, df):
        if len(df) < 2:
            return "stable"
            
        mid_point = len(df) // 2
        first_half = df.iloc[:mid_point]['accuracy_rate'].mean()
        second_half = df.iloc[mid_point:]['accuracy_rate'].mean()
        improvement = second_half - first_half
        
        if improvement > 2:
            return "improving"
        elif improvement < -2:
            return "declining"
        return "stable"
    
    def _analyze_category_corrections(self, df):
        category_corrections = {}
        for _, row in df.iterrows():
            try:
                modifications = json.loads(row['modifications_by_category'])
                for category, count in modifications.items():
                    category_corrections[category] = category_corrections.get(category, 0) + count
            except (json.JSONDecodeError, TypeError):
                continue
        return dict(sorted(category_corrections.items(), key=lambda x: x[1], reverse=True)[:5])
    
    def display_accuracy_report(self, days_back=30):
        trends = self.get_accuracy_trends(days_back)
        
        if not trends:
            print("📊 No accuracy data available yet.")
            return
            
        print(f"\n{'='*50}")
        print("📊 ACCURACY REPORT")
        print(f"{'='*50}")
        print(f" Runs: {trends['total_runs']} | 📧 Emails: {trends['total_emails_processed']} | ✏️ Corrections: {trends['total_modifications']}")
        print(f"📈 Current: {trends['latest_accuracy']:.1f}% | Average: {trends['average_accuracy']:.1f}%")
        
        trend_emoji = {"improving": "📈", "declining": "📉", "stable": "➡️"}
        print(f"🎯 Trend: {trend_emoji[trends['improvement_trend']]} {trends['improvement_trend'].title()}")
        
        if trends['most_corrected_categories']:
            print(f"\n🔍 Most Corrected:")
            for category, count in list(trends['most_corrected_categories'].items())[:3]:
                print(f"   • {category.replace('_', ' ').title()}: {count}")
                
        accuracy = trends['average_accuracy']
        if accuracy >= 85:
            print("💡 Good accuracy performance")
        elif accuracy >= 75:
            print("💡 Consider reviewing classification rules")
        else:
            print("💡 Classification needs improvement")
    
    def analyze_category_accuracy(self):
        if not os.path.exists(self.modifications_file):
            return {}
        df = pd.read_csv(self.modifications_file)
        if df.empty:
            return {}
        return {
            'frequently_incorrect': df['old_suggestion'].value_counts().to_dict(),
            'total_corrections': len(df)
        }
