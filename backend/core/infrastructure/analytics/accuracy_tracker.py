"""Accuracy Tracker for Email Helper - Classification Accuracy Monitoring and Analytics.

This module provides comprehensive accuracy tracking and analytics for the
email classification system, monitoring AI performance, user corrections,
and classification trends over time to support continuous improvement.

The AccuracyTracker class manages:
- Session-based accuracy calculation and tracking
- User modification recording and analysis
- Performance trend analysis over time
- Category-specific accuracy metrics
- Learning feedback collection for AI improvement
- Historical performance data storage and retrieval

Key Features:
- Real-time accuracy calculation for processing sessions
- Detailed tracking of user corrections and modifications
- Category-specific performance analytics
- Trend analysis for continuous improvement
- CSV-based data storage for analysis and reporting
- Integration with user feedback collection systems

Analytics Capabilities:
- Overall accuracy rate calculation
- Category-specific performance metrics
- Temporal trend analysis
- User correction pattern identification
- Performance improvement tracking

This module supports the learning and improvement cycle of the
AI classification system through comprehensive data collection.
"""

import os
import pandas as pd
from datetime import datetime, timedelta
import json
import numpy as np


class AccuracyTracker:
    """Accuracy tracking and analytics engine for email classification performance.

    This class provides comprehensive tracking of AI classification accuracy,
    user corrections, and performance analytics to support continuous
    improvement of the email helper system's classification capabilities.

    The tracker manages:
    - Session-based accuracy calculation and recording
    - User modification tracking and analysis
    - Performance trend monitoring over time
    - Category-specific accuracy metrics
    - Historical data storage and retrieval
    - Analytics and reporting capabilities

    Attributes:
        user_feedback_dir (str): Directory for storing feedback and accuracy data
        accuracy_file (str): Path to accuracy tracking CSV file
        modifications_file (str): Path to user modifications CSV file

    Example:
        >>> tracker = AccuracyTracker('/path/to/runtime_data')
        >>> accuracy = tracker.calculate_accuracy_for_session(100, modifications)
        >>> print(f"Session accuracy: {accuracy}%")
    """

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
            print("\n🔍 Most Corrected:")
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

    def get_time_series_data(self, start_date=None, end_date=None, granularity='daily'):
        """
        Get time-series accuracy data for dashboard charts.

        Args:
            start_date (datetime, optional): Start date for filtering
            end_date (datetime, optional): End date for filtering  
            granularity (str): 'daily', 'weekly', 'monthly' aggregation

        Returns:
            pd.DataFrame: Time-indexed DataFrame with accuracy metrics
        """
        if not os.path.exists(self.accuracy_file):
            return pd.DataFrame()

        df = pd.read_csv(self.accuracy_file)
        if df.empty:
            return pd.DataFrame()

        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Apply date filtering if provided
        if start_date:
            df = df[df['timestamp'] >= start_date]
        if end_date:
            df = df[df['timestamp'] <= end_date]

        if df.empty:
            return pd.DataFrame()

        # Set timestamp as index for time-series operations
        df.set_index('timestamp', inplace=True)

        # Define aggregation functions
        agg_funcs = {
            'accuracy_rate': 'mean',
            'total_emails_processed': 'sum',
            'emails_modified': 'sum',
            'run_id': 'count'  # Number of sessions
        }

        # Perform granularity-based aggregation
        if granularity == 'daily':
            result_df = df.resample('D').agg(agg_funcs)
        elif granularity == 'weekly':
            result_df = df.resample('W').agg(agg_funcs)
        elif granularity == 'monthly':
            result_df = df.resample('M').agg(agg_funcs)
        else:
            # Default to daily if invalid granularity provided
            result_df = df.resample('D').agg(agg_funcs)

        # Rename columns for clarity
        result_df.rename(columns={'run_id': 'session_count'}, inplace=True)

        # Round accuracy to 2 decimal places and fill NaN values
        result_df['accuracy_rate'] = result_df['accuracy_rate'].round(2)
        result_df = result_df.fillna(0)

        # Remove rows where no sessions occurred
        result_df = result_df[result_df['session_count'] > 0]

        return result_df

    def get_category_performance_summary(self, days_back=30):
        """
        Analyze accuracy by email category for dashboard widgets.

        Args:
            days_back (int): Number of days back to analyze

        Returns:
            dict: Category-keyed performance statistics
        """
        if not os.path.exists(self.accuracy_file):
            return {}

        df = pd.read_csv(self.accuracy_file)
        if df.empty:
            return {}

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_df = df[df['timestamp'] >= cutoff_date]

        if recent_df.empty:
            return {}

        category_stats = {}
        total_categories_processed = {}

        # Parse modifications_by_category JSON fields
        for _, row in recent_df.iterrows():
            try:
                modifications = json.loads(row['modifications_by_category'])
                total_emails = row['total_emails_processed']

                # Track corrections per category
                for category, corrections_count in modifications.items():
                    if category not in category_stats:
                        category_stats[category] = {
                            'total_corrections': 0,
                            'total_emails_processed': 0,
                            'sessions_involved': 0
                        }

                    category_stats[category]['total_corrections'] += corrections_count
                    category_stats[category]['sessions_involved'] += 1

                # Estimate total emails processed per category (simplified approach)
                # This is an approximation since we don't have exact per-category email counts
                if modifications:
                    emails_per_category = total_emails // len(modifications)
                    for category in modifications.keys():
                        if category not in total_categories_processed:
                            total_categories_processed[category] = 0
                        total_categories_processed[category] += emails_per_category

            except (json.JSONDecodeError, TypeError, ZeroDivisionError):
                continue

        # Calculate accuracy rates for each category
        summary = {}
        for category, stats in category_stats.items():
            estimated_total = total_categories_processed.get(category, stats['total_corrections'])
            # Ensure we don't divide by zero and have reasonable estimates
            if estimated_total > 0:
                accuracy_rate = max(0, round(((estimated_total - stats['total_corrections']) / estimated_total) * 100, 2))
            else:
                accuracy_rate = 0.0

            summary[category] = {
                'accuracy_rate': accuracy_rate,
                'total_corrections': stats['total_corrections'],
                'sessions_involved': stats['sessions_involved'],
                'category_name': category.replace('_', ' ').title()
            }

        # Sort by number of corrections (most problematic categories first)
        summary = dict(sorted(summary.items(), key=lambda x: x[1]['total_corrections'], reverse=True))

        return summary

    def get_dashboard_metrics(self, date_range=None):
        """
        Get comprehensive summary data for dashboard widgets.

        Args:
            date_range (tuple, optional): (start_date, end_date) for filtering

        Returns:
            dict: Structured metrics for dashboard components
        """
        if not os.path.exists(self.accuracy_file):
            return {
                'overall_stats': {'total_sessions': 0, 'total_emails': 0, 'average_accuracy': 0.0},
                'trend_analysis': {'improvement_trend': 'no_data', 'trend_percentage': 0.0},
                'category_summary': {},
                'recent_performance': {'last_7_days': 0.0, 'last_30_days': 0.0},
                'session_statistics': {'min_accuracy': 0.0, 'max_accuracy': 0.0, 'std_accuracy': 0.0}
            }

        df = pd.read_csv(self.accuracy_file)
        if df.empty:
            return {
                'overall_stats': {'total_sessions': 0, 'total_emails': 0, 'average_accuracy': 0.0},
                'trend_analysis': {'improvement_trend': 'no_data', 'trend_percentage': 0.0},
                'category_summary': {},
                'recent_performance': {'last_7_days': 0.0, 'last_30_days': 0.0},
                'session_statistics': {'min_accuracy': 0.0, 'max_accuracy': 0.0, 'std_accuracy': 0.0}
            }

        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Apply date range filtering if provided
        if date_range and len(date_range) == 2:
            start_date, end_date = date_range
            if start_date:
                df = df[df['timestamp'] >= start_date]
            if end_date:
                df = df[df['timestamp'] <= end_date]

        if df.empty:
            return {
                'overall_stats': {'total_sessions': 0, 'total_emails': 0, 'average_accuracy': 0.0},
                'trend_analysis': {'improvement_trend': 'no_data', 'trend_percentage': 0.0},
                'category_summary': {},
                'recent_performance': {'last_7_days': 0.0, 'last_30_days': 0.0},
                'session_statistics': {'min_accuracy': 0.0, 'max_accuracy': 0.0, 'std_accuracy': 0.0}
            }

        # Overall statistics
        overall_stats = {
            'total_sessions': len(df),
            'total_emails': int(df['total_emails_processed'].sum()),
            'total_corrections': int(df['emails_modified'].sum()),
            'average_accuracy': round(df['accuracy_rate'].mean(), 2),
            'latest_accuracy': round(df.iloc[-1]['accuracy_rate'], 2) if not df.empty else 0.0
        }

        # Trend analysis
        trend_info = self._calculate_improvement_trend(df)
        trend_percentage = 0.0
        if len(df) >= 2:
            mid_point = len(df) // 2
            first_half = df.iloc[:mid_point]['accuracy_rate'].mean()
            second_half = df.iloc[mid_point:]['accuracy_rate'].mean()
            trend_percentage = round(second_half - first_half, 2)

        # Recent performance (last 7 and 30 days)
        now = datetime.now()
        last_7_days = df[df['timestamp'] >= (now - timedelta(days=7))]
        last_30_days = df[df['timestamp'] >= (now - timedelta(days=30))]

        recent_performance = {
            'last_7_days': round(last_7_days['accuracy_rate'].mean(), 2) if not last_7_days.empty else 0.0,
            'last_30_days': round(last_30_days['accuracy_rate'].mean(), 2) if not last_30_days.empty else 0.0,
            'sessions_last_7_days': len(last_7_days),
            'sessions_last_30_days': len(last_30_days)
        }

        # Session statistics
        session_stats = {
            'min_accuracy': round(df['accuracy_rate'].min(), 2),
            'max_accuracy': round(df['accuracy_rate'].max(), 2),
            'std_accuracy': round(df['accuracy_rate'].std(), 2),
            'median_accuracy': round(df['accuracy_rate'].median(), 2)
        }

        # Category summary (top 5 most corrected)
        category_corrections = self._analyze_category_corrections(df)
        category_summary = {}
        for i, (category, count) in enumerate(list(category_corrections.items())[:5]):
            category_summary[f"rank_{i+1}"] = {
                'category': category.replace('_', ' ').title(),
                'corrections': count
            }

        return {
            'overall_stats': overall_stats,
            'trend_analysis': {
                'improvement_trend': trend_info,
                'trend_percentage': trend_percentage
            },
            'category_summary': category_summary,
            'recent_performance': recent_performance,
            'session_statistics': session_stats,
            'data_quality': {
                'total_data_points': len(df),
                'date_range': {
                    'earliest': df['timestamp'].min().isoformat() if not df.empty else None,
                    'latest': df['timestamp'].max().isoformat() if not df.empty else None
                }
            }
        }

    def export_dashboard_data(self, format='csv', date_range=None):
        """
        Export dashboard data for external analysis or backup.

        Args:
            format (str): Export format - 'csv' or 'json'
            date_range (tuple, optional): (start_date, end_date) for filtering

        Returns:
            str: Path to exported file or JSON string for json format
        """
        if not os.path.exists(self.accuracy_file):
            if format == 'json':
                return json.dumps({'error': 'No accuracy data available'})
            return None

        df = pd.read_csv(self.accuracy_file)
        if df.empty:
            if format == 'json':
                return json.dumps({'error': 'No accuracy data available'})
            return None

        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Apply date range filtering if provided
        if date_range and len(date_range) == 2:
            start_date, end_date = date_range
            if start_date:
                df = df[df['timestamp'] >= start_date]
            if end_date:
                df = df[df['timestamp'] <= end_date]

        if df.empty:
            if format == 'json':
                return json.dumps({'error': 'No data in specified date range'})
            return None

        # Prepare export data with dashboard-friendly structure
        export_data = []
        for _, row in df.iterrows():
            try:
                modifications = json.loads(row['modifications_by_category'])
            except (json.JSONDecodeError, TypeError):
                modifications = {}

            export_row = {
                'timestamp': row['timestamp'].isoformat(),
                'run_id': row['run_id'],
                'total_emails_processed': int(row['total_emails_processed']),
                'emails_modified': int(row['emails_modified']),
                'accuracy_rate': round(row['accuracy_rate'], 2),
                'modifications_by_category': modifications,
                'date': row['timestamp'].date().isoformat(),
                'hour': row['timestamp'].hour,
                'day_of_week': row['timestamp'].strftime('%A'),
                'week_of_year': row['timestamp'].isocalendar()[1],
                'month': row['timestamp'].strftime('%B'),
                'quarter': f"Q{((row['timestamp'].month - 1) // 3) + 1}"
            }
            export_data.append(export_row)

        if format.lower() == 'json':
            # Return JSON string with summary metadata
            export_summary = {
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'total_records': len(export_data),
                    'date_range': {
                        'start': export_data[0]['timestamp'] if export_data else None,
                        'end': export_data[-1]['timestamp'] if export_data else None
                    },
                    'format_version': '1.0'
                },
                'data': export_data
            }
            return json.dumps(export_summary, indent=2)

        elif format.lower() == 'csv':
            # Create DataFrame and export to CSV
            export_df = pd.DataFrame(export_data)

            # Flatten modifications_by_category for CSV compatibility
            export_df['modifications_json'] = export_df['modifications_by_category'].apply(json.dumps)
            export_df.drop('modifications_by_category', axis=1, inplace=True)

            # Generate timestamped filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"accuracy_dashboard_export_{timestamp}.csv"
            export_path = os.path.join(self.user_feedback_dir, filename)

            export_df.to_csv(export_path, index=False)
            return export_path

        else:
            raise ValueError(f"Unsupported export format: {format}. Use 'csv' or 'json'.")

    def get_session_comparison_data(self):
        """
        Get session-over-session comparison data for trend analysis.

        Returns:
            pd.DataFrame: DataFrame with session comparison metrics
        """
        if not os.path.exists(self.accuracy_file):
            return pd.DataFrame()

        df = pd.read_csv(self.accuracy_file)
        if df.empty or len(df) < 2:
            return pd.DataFrame()

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        # Calculate session-to-session changes
        comparison_data = []

        for i in range(1, len(df)):
            current_session = df.iloc[i]
            previous_session = df.iloc[i-1]

            # Calculate changes
            accuracy_change = current_session['accuracy_rate'] - previous_session['accuracy_rate']
            emails_change = current_session['total_emails_processed'] - previous_session['total_emails_processed']
            modifications_change = current_session['emails_modified'] - previous_session['emails_modified']

            # Calculate percentage changes (avoid division by zero)
            accuracy_pct_change = (accuracy_change / previous_session['accuracy_rate'] * 100) if previous_session['accuracy_rate'] != 0 else 0
            emails_pct_change = (emails_change / previous_session['total_emails_processed'] * 100) if previous_session['total_emails_processed'] != 0 else 0

            # Time between sessions
            time_diff = current_session['timestamp'] - previous_session['timestamp']
            hours_between = time_diff.total_seconds() / 3600

            # Analyze category changes
            try:
                current_categories = json.loads(current_session['modifications_by_category'])
                previous_categories = json.loads(previous_session['modifications_by_category'])

                # Find categories that improved or worsened
                category_changes = {}
                all_categories = set(current_categories.keys()) | set(previous_categories.keys())

                for category in all_categories:
                    current_count = current_categories.get(category, 0)
                    previous_count = previous_categories.get(category, 0)
                    category_changes[category] = current_count - previous_count

                # Find most improved and most worsened categories
                most_improved = min(category_changes.items(), key=lambda x: x[1]) if category_changes else ('none', 0)
                most_worsened = max(category_changes.items(), key=lambda x: x[1]) if category_changes else ('none', 0)

            except (json.JSONDecodeError, TypeError):
                most_improved = ('parse_error', 0)
                most_worsened = ('parse_error', 0)
                category_changes = {}

            comparison_row = {
                'session_date': current_session['timestamp'],
                'previous_session_date': previous_session['timestamp'],
                'hours_between_sessions': round(hours_between, 2),
                'current_accuracy': round(current_session['accuracy_rate'], 2),
                'previous_accuracy': round(previous_session['accuracy_rate'], 2),
                'accuracy_change': round(accuracy_change, 2),
                'accuracy_pct_change': round(accuracy_pct_change, 2),
                'current_emails': int(current_session['total_emails_processed']),
                'previous_emails': int(previous_session['total_emails_processed']),
                'emails_change': int(emails_change),
                'emails_pct_change': round(emails_pct_change, 2),
                'current_modifications': int(current_session['emails_modified']),
                'previous_modifications': int(previous_session['emails_modified']),
                'modifications_change': int(modifications_change),
                'trend_direction': 'improving' if accuracy_change > 0 else 'declining' if accuracy_change < 0 else 'stable',
                'most_improved_category': most_improved[0],
                'most_improved_change': most_improved[1],
                'most_worsened_category': most_worsened[0],
                'most_worsened_change': most_worsened[1],
                'session_run_id': current_session['run_id'],
                'previous_run_id': previous_session['run_id']
            }

            comparison_data.append(comparison_row)

        comparison_df = pd.DataFrame(comparison_data)

        if not comparison_df.empty:
            # Add rolling averages for trend smoothing
            comparison_df['accuracy_change_rolling_avg'] = comparison_df['accuracy_change'].rolling(window=3, min_periods=1).mean().round(2)
            comparison_df['accuracy_trend_strength'] = np.abs(comparison_df['accuracy_change_rolling_avg'])

            # Add trend categorization
            comparison_df['trend_category'] = comparison_df['accuracy_change_rolling_avg'].apply(
                lambda x: 'strong_improvement' if x > 5 else
                         'improvement' if x > 1 else
                         'strong_decline' if x < -5 else
                         'decline' if x < -1 else 'stable'
            )

        return comparison_df

    def calculate_running_accuracy(self, days_back=None):
        """
        Calculate running accuracy averages for dashboard display.

        Args:
            days_back (int, optional): Days to look back. If None, calculates both 7-day and 30-day

        Returns:
            dict: Running accuracy metrics with 7-day and 30-day moving averages
        """
        if not os.path.exists(self.accuracy_file):
            return {
                'last_7_days': 0.0,
                'last_30_days': 0.0,
                'current_trend': 'no_data',
                'total_sessions_7d': 0,
                'total_sessions_30d': 0,
                'total_emails_7d': 0,
                'total_emails_30d': 0
            }

        df = pd.read_csv(self.accuracy_file)
        if df.empty:
            return {
                'last_7_days': 0.0,
                'last_30_days': 0.0,
                'current_trend': 'no_data',
                'total_sessions_7d': 0,
                'total_sessions_30d': 0,
                'total_emails_7d': 0,
                'total_emails_30d': 0
            }

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        current_time = datetime.now()

        # Calculate 7-day metrics
        seven_days_ago = current_time - timedelta(days=7)
        df_7d = df[df['timestamp'] >= seven_days_ago]

        # Calculate 30-day metrics
        thirty_days_ago = current_time - timedelta(days=30)
        df_30d = df[df['timestamp'] >= thirty_days_ago]

        # Calculate accuracies
        accuracy_7d = round(df_7d['accuracy_rate'].mean(), 2) if not df_7d.empty else 0.0
        accuracy_30d = round(df_30d['accuracy_rate'].mean(), 2) if not df_30d.empty else 0.0

        # Determine trend based on comparison of recent vs older data within 30 days
        trend = 'stable'
        if len(df_30d) >= 4:  # Need enough data for trend analysis
            # Compare first half vs second half of 30-day period
            mid_point = len(df_30d) // 2
            first_half_avg = df_30d.iloc[:mid_point]['accuracy_rate'].mean()
            second_half_avg = df_30d.iloc[mid_point:]['accuracy_rate'].mean()
            diff = second_half_avg - first_half_avg

            if diff > 2:
                trend = 'improving'
            elif diff < -2:
                trend = 'declining'

        return {
            'last_7_days': accuracy_7d,
            'last_30_days': accuracy_30d,
            'current_trend': trend,
            'total_sessions_7d': len(df_7d),
            'total_sessions_30d': len(df_30d),
            'total_emails_7d': int(df_7d['total_emails_processed'].sum()) if not df_7d.empty else 0,
            'total_emails_30d': int(df_30d['total_emails_processed'].sum()) if not df_30d.empty else 0
        }

    def persist_accuracy_metrics(self, metrics_data=None):
        """
        Persist accuracy metrics to long-term storage for historical analysis.

        Args:
            metrics_data (dict, optional): Additional metrics to persist. 
                                         If None, calculates current metrics

        Returns:
            bool: True if persistence was successful, False otherwise
        """
        try:
            # Get current running accuracy if no specific data provided
            if metrics_data is None:
                metrics_data = self.calculate_running_accuracy()

            # Create long-term metrics directory
            long_term_dir = os.path.join(self.user_feedback_dir, 'long_term_metrics')
            os.makedirs(long_term_dir, exist_ok=True)

            # Create metrics file path (monthly files for organization)
            current_month = datetime.now().strftime('%Y_%m')
            metrics_file = os.path.join(long_term_dir, f'accuracy_metrics_{current_month}.jsonl')

            # Prepare metrics entry with timestamp
            metrics_entry = {
                'timestamp': datetime.now().isoformat(),
                'calculation_date': datetime.now().strftime('%Y-%m-%d'),
                'metrics': metrics_data,
                'system_info': {
                    'total_historical_sessions': self._count_total_sessions(),
                    'data_retention_days': 365  # Configurable retention policy
                }
            }

            # Append to JSONL file (allows easy streaming and analysis)
            with open(metrics_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(metrics_entry, default=str) + '\n')

            # Optional: Clean up old metrics files beyond retention period
            self._cleanup_old_metrics_files(long_term_dir, retention_months=12)

            return True

        except Exception as e:
            print(f"⚠️ Error persisting accuracy metrics: {e}")
            return False

    def _count_total_sessions(self):
        """Count total sessions in accuracy tracking file."""
        if not os.path.exists(self.accuracy_file):
            return 0
        try:
            df = pd.read_csv(self.accuracy_file)
            return len(df)
        except:
            return 0

    def _cleanup_old_metrics_files(self, metrics_dir, retention_months=12):
        """Clean up old metrics files beyond retention period."""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_months * 30)
            cutoff_month = cutoff_date.strftime('%Y_%m')

            for filename in os.listdir(metrics_dir):
                if filename.startswith('accuracy_metrics_') and filename.endswith('.jsonl'):
                    # Extract month from filename
                    month_part = filename.replace('accuracy_metrics_', '').replace('.jsonl', '')
                    if month_part < cutoff_month:
                        old_file = os.path.join(metrics_dir, filename)
                        os.remove(old_file)
                        print(f"🧹 Cleaned up old metrics file: {filename}")
        except Exception as e:
            print(f"⚠️ Error during metrics cleanup: {e}")
