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
    
    def get_time_series_data(self, granularity='daily', days_back=30):
        """Get time series accuracy data for trend charts"""
        if not os.path.exists(self.accuracy_file):
            return []
            
        df = pd.read_csv(self.accuracy_file)
        if df.empty:
            return []
            
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_df = df[df['timestamp'] >= cutoff_date]
        
        if recent_df.empty:
            return []
        
        # Group by granularity
        if granularity == 'daily':
            recent_df['date'] = recent_df['timestamp'].dt.date
            grouped = recent_df.groupby('date').agg({
                'accuracy_rate': 'mean',
                'total_emails_processed': 'sum'
            }).reset_index()
        elif granularity == 'weekly':
            recent_df['week'] = recent_df['timestamp'].dt.to_period('W')
            grouped = recent_df.groupby('week').agg({
                'accuracy_rate': 'mean',
                'total_emails_processed': 'sum'
            }).reset_index()
            grouped['date'] = grouped['week'].dt.start_time.dt.date
        else:  # monthly
            recent_df['month'] = recent_df['timestamp'].dt.to_period('M')
            grouped = recent_df.groupby('month').agg({
                'accuracy_rate': 'mean',
                'total_emails_processed': 'sum'
            }).reset_index()
            grouped['date'] = grouped['month'].dt.start_time.dt.date
        
        return [{
            'date': row['date'],
            'accuracy': round(row['accuracy_rate'], 2),
            'emails_processed': int(row['total_emails_processed'])
        } for _, row in grouped.iterrows()]
    
    def get_category_performance_summary(self, days_back=30):
        """Get category-wise performance summary for bar charts"""
        if not os.path.exists(self.accuracy_file):
            return []
            
        df = pd.read_csv(self.accuracy_file)
        if df.empty:
            return []
            
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_df = df[df['timestamp'] >= cutoff_date]
        
        if recent_df.empty:
            return []
        
        category_data = {}
        total_emails_by_category = {}
        
        for _, row in recent_df.iterrows():
            try:
                modifications = json.loads(row['modifications_by_category'])
                emails_in_session = row['total_emails_processed']
                
                # Estimate emails per category (simplified approach)
                if modifications:
                    avg_per_category = emails_in_session / len(modifications)
                    for category, corrections in modifications.items():
                        if category not in category_data:
                            category_data[category] = {'corrections': 0, 'total_emails': 0}
                        category_data[category]['corrections'] += corrections
                        category_data[category]['total_emails'] += avg_per_category
                        
            except (json.JSONDecodeError, TypeError):
                continue
        
        result = []
        for category, data in category_data.items():
            if data['total_emails'] > 0:
                accuracy = max(0, (data['total_emails'] - data['corrections']) / data['total_emails'] * 100)
                result.append({
                    'category': category.replace('_', ' ').title(),
                    'accuracy': round(accuracy, 1),
                    'corrections': int(data['corrections']),
                    'total_emails': int(data['total_emails'])
                })
        
        return sorted(result, key=lambda x: x['accuracy'], reverse=True)
    
    def get_session_comparison_data(self, session_count=10):
        """Get recent session data for comparison charts"""
        if not os.path.exists(self.accuracy_file):
            return []
            
        df = pd.read_csv(self.accuracy_file)
        if df.empty:
            return []
            
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp', ascending=False)
        recent_sessions = df.head(session_count)
        
        result = []
        for _, row in recent_sessions.iterrows():
            result.append({
                'session_id': row['run_id'],
                'date': row['timestamp'].strftime('%Y-%m-%d %H:%M'),
                'accuracy': round(row['accuracy_rate'], 1),
                'emails_processed': int(row['total_emails_processed']),
                'corrections': int(row['emails_modified'])
            })
        
        return list(reversed(result))  # Chronological order
    
    def get_dashboard_metrics(self):
        """Get key metrics for summary dashboard widgets"""
        if not os.path.exists(self.accuracy_file):
            return {
                'overall_accuracy': 0,
                'seven_day_average': 0,
                'total_sessions': 0,
                'total_emails': 0,
                'trend_indicator': 'stable'
            }
            
        df = pd.read_csv(self.accuracy_file)
        if df.empty:
            return {
                'overall_accuracy': 0,
                'seven_day_average': 0,
                'total_sessions': 0,
                'total_emails': 0,
                'trend_indicator': 'stable'
            }
            
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Overall metrics
        overall_accuracy = round(df['accuracy_rate'].mean(), 1)
        total_sessions = len(df)
        total_emails = int(df['total_emails_processed'].sum())
        
        # 7-day average
        cutoff_date = datetime.now() - timedelta(days=7)
        recent_df = df[df['timestamp'] >= cutoff_date]
        seven_day_average = round(recent_df['accuracy_rate'].mean(), 1) if not recent_df.empty else overall_accuracy
        
        # Trend indicator
        trend_indicator = self._calculate_improvement_trend(df)
        
        return {
            'overall_accuracy': overall_accuracy,
            'seven_day_average': seven_day_average,
            'total_sessions': total_sessions,
            'total_emails': total_emails,
            'trend_indicator': trend_indicator
        }
