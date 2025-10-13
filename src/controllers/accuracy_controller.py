"""Accuracy Controller - Handles accuracy tracking and metrics business logic."""

from typing import Dict, List, Optional
import pandas as pd


class AccuracyController:
    """Controller for accuracy tracking and dashboard operations."""
    
    def __init__(self, accuracy_tracker, task_persistence, db_migrations):
        """Initialize controller with required services.
        
        Args:
            accuracy_tracker: Service for accuracy tracking
            task_persistence: Service for task persistence
            db_migrations: Service for database operations
        """
        self.accuracy_tracker = accuracy_tracker
        self.task_persistence = task_persistence
        self.db_migrations = db_migrations
    
    def get_dashboard_metrics(self) -> Dict:
        """Get all metrics for the accuracy dashboard.
        
        Returns:
            Dictionary containing all dashboard metrics
        """
        # Get running accuracy metrics
        running_metrics = self.accuracy_tracker.calculate_running_accuracy()
        
        # Get overall dashboard metrics
        dashboard_metrics = self.accuracy_tracker.get_dashboard_metrics()
        overall = dashboard_metrics.get('overall_stats', {})
        
        # Get task resolution metrics
        resolution_history = self.task_persistence.get_resolution_history(
            days_back=30, include_stats=True)
        
        metrics = {
            'overall_accuracy': overall.get('average_accuracy', 0),
            'seven_day_accuracy': running_metrics.get('last_7_days', 0),
            'thirty_day_accuracy': running_metrics.get('last_30_days', 0),
            'total_sessions': overall.get('total_sessions', 0),
            'current_trend': running_metrics.get('current_trend', 'stable'),
            'total_sessions_7d': running_metrics.get('total_sessions_7d', 0),
            'total_sessions_30d': running_metrics.get('total_sessions_30d', 0),
            'total_emails_7d': running_metrics.get('total_emails_7d', 0),
            'total_emails_30d': running_metrics.get('total_emails_30d', 0),
            'resolution_history': resolution_history
        }
        
        # Store metrics for historical tracking
        self.accuracy_tracker.persist_accuracy_metrics(running_metrics)
        if hasattr(self, 'db_migrations'):
            self.db_migrations.store_accuracy_metrics(running_metrics)
        
        return metrics
    
    def get_time_series_data(self, start_date, end_date, granularity: str) -> pd.DataFrame:
        """Get time series data for trends chart.
        
        Args:
            start_date: Start date for data
            end_date: End date for data
            granularity: Data granularity ('daily', 'weekly', 'monthly')
            
        Returns:
            DataFrame containing time series data
        """
        return self.accuracy_tracker.get_time_series_data(start_date, end_date, granularity)
    
    def get_category_performance(self, days_back: int) -> Dict:
        """Get category performance summary.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Dictionary containing category performance data
        """
        return self.accuracy_tracker.get_category_performance_summary(days_back)
    
    def get_session_comparison_data(self) -> pd.DataFrame:
        """Get session comparison data.
        
        Returns:
            DataFrame containing session comparison data
        """
        return self.accuracy_tracker.get_session_comparison_data()
    
    def get_task_resolution_history(self, days_back: int, 
                                    resolution_type: Optional[str] = None) -> Dict:
        """Get task resolution history.
        
        Args:
            days_back: Number of days to look back
            resolution_type: Optional filter for resolution type
            
        Returns:
            Dictionary containing resolution history data
        """
        return self.task_persistence.get_resolution_history(
            days_back=days_back,
            resolution_type=resolution_type,
            include_stats=True
        )
    
    def export_dashboard_data(self, format: str = 'csv') -> Optional[str]:
        """Export dashboard data to file.
        
        Args:
            format: Export format ('csv')
            
        Returns:
            Path to exported file or None if no data
        """
        return self.accuracy_tracker.export_dashboard_data(format=format)
