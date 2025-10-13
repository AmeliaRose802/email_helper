#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Accuracy Tab - Accuracy tracking dashboard interface (VIEW ONLY - NO BUSINESS LOGIC)."""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Dict, Any, List, Optional, Callable


class AccuracyTab:
    """Accuracy tracking dashboard tab - pure view component.
    
    This view delegates all business logic to the AccuracyController.
    """
    
    def __init__(
        self,
        parent,
        on_refresh_callback: Callable,
        on_export_callback: Optional[Callable] = None
    ):
        """Initialize accuracy tab view.
        
        Args:
            parent: Parent widget
            on_refresh_callback: Callback for refresh button
            on_export_callback: Optional callback for export button
        """
        self.parent = parent
        self.on_refresh_callback = on_refresh_callback
        self.on_export_callback = on_export_callback
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create all UI widgets."""
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Header with controls
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(
            header_frame,
            text="📊 AI Accuracy Dashboard",
            font=('Segoe UI', 14, 'bold')
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        button_frame = ttk.Frame(header_frame)
        button_frame.pack(side=tk.RIGHT)
        
        self.refresh_btn = ttk.Button(
            button_frame,
            text="🔄 Refresh Metrics",
            command=self.on_refresh_callback,
            style="Accent.TButton"
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        if self.on_export_callback:
            ttk.Button(
                button_frame,
                text="💾 Export Report",
                command=self.on_export_callback
            ).pack(side=tk.LEFT, padx=5)
        
        # Dashboard content area
        self.dashboard_text = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=('Consolas', 10),
            padx=10,
            pady=10
        )
        self.dashboard_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Tag configuration for formatting
        self.dashboard_text.tag_config("heading", font=('Segoe UI', 12, 'bold'), spacing1=10, spacing3=5)
        self.dashboard_text.tag_config("subheading", font=('Segoe UI', 11, 'bold'), spacing1=8, spacing3=3, foreground="#0066CC")
        self.dashboard_text.tag_config("metric_label", font=('Segoe UI', 10, 'bold'))
        self.dashboard_text.tag_config("metric_value", font=('Segoe UI', 10), foreground="#006600")
        self.dashboard_text.tag_config("warning", font=('Segoe UI', 10), foreground="#CC6600")
        self.dashboard_text.tag_config("error", font=('Segoe UI', 10), foreground="#CC0000")
        self.dashboard_text.tag_config("success", font=('Segoe UI', 10), foreground="#009900")
        self.dashboard_text.tag_config("monospace", font=('Consolas', 9))
        
        # Initial message
        self._show_initial_message()
    
    def _show_initial_message(self):
        """Show initial welcome message."""
        self.dashboard_text.config(state=tk.NORMAL)
        self.dashboard_text.delete(1.0, tk.END)
        
        msg = '''Welcome to the Accuracy Dashboard! 📊

This dashboard tracks the AI classification accuracy:

📈 Overall Metrics:
   • Accuracy rate across all email categories
   • Precision and recall for each category
   • Confusion matrix showing misclassifications
   • Trend analysis over time

🎯 Category Performance:
   • Breakdown by email category
   • Common misclassification patterns
   • Improvement opportunities

📅 Time Series:
   • Daily accuracy trends
   • Performance over last 7/30 days
   • Visual trend charts (when available)

To view metrics:
1. Process and categorize emails
2. Provide feedback on classifications in the Editing tab
3. Click "Refresh Metrics" above to update the dashboard

Your accuracy data will appear here! 🚀'''
        
        self.dashboard_text.insert(tk.END, msg)
        self.dashboard_text.config(state=tk.DISABLED)
    
    # Public methods for updating UI from controller
    
    def display_metrics(self, metrics_data: Dict[str, Any]):
        """Display accuracy metrics dashboard.
        
        Args:
            metrics_data: Dictionary containing:
                - overall_accuracy: Float 0-1
                - total_classifications: Int
                - total_feedback: Int
                - category_metrics: Dict[str, Dict] with per-category stats
                - confusion_matrix: Dict for misclassifications
                - time_series: List[Dict] with daily metrics
                - trends: Dict with trend analysis
        """
        self.dashboard_text.config(state=tk.NORMAL)
        self.dashboard_text.delete(1.0, tk.END)
        
        # Header
        self.dashboard_text.insert(tk.END, "📊 AI Classification Accuracy Dashboard\n", "heading")
        self.dashboard_text.insert(tk.END, f"Last Updated: {metrics_data.get('updated_time', 'Unknown')}\n\n")
        
        # Overall metrics
        self._display_overall_metrics(metrics_data)
        
        # Category breakdown
        self._display_category_metrics(metrics_data)
        
        # Confusion matrix
        self._display_confusion_matrix(metrics_data)
        
        # Time series trends
        self._display_trends(metrics_data)
        
        self.dashboard_text.config(state=tk.DISABLED)
    
    def _display_overall_metrics(self, metrics_data: Dict[str, Any]):
        """Display overall metrics section."""
        self.dashboard_text.insert(tk.END, "📈 Overall Performance\n", "subheading")
        self.dashboard_text.insert(tk.END, "─" * 80 + "\n", "monospace")
        
        accuracy = metrics_data.get('overall_accuracy', 0.0)
        total_classifications = metrics_data.get('total_classifications', 0)
        total_feedback = metrics_data.get('total_feedback', 0)
        
        # Color code accuracy
        if accuracy >= 0.9:
            accuracy_tag = "success"
            emoji = "🎉"
        elif accuracy >= 0.75:
            accuracy_tag = "metric_value"
            emoji = "✅"
        elif accuracy >= 0.6:
            accuracy_tag = "warning"
            emoji = "⚠️"
        else:
            accuracy_tag = "error"
            emoji = "❌"
        
        self.dashboard_text.insert(tk.END, f"{emoji} Overall Accuracy: ", "metric_label")
        self.dashboard_text.insert(tk.END, f"{accuracy:.1%}\n", accuracy_tag)
        
        self.dashboard_text.insert(tk.END, f"📧 Total Classifications: ", "metric_label")
        self.dashboard_text.insert(tk.END, f"{total_classifications:,}\n", "metric_value")
        
        self.dashboard_text.insert(tk.END, f"✏️ User Feedback Provided: ", "metric_label")
        self.dashboard_text.insert(tk.END, f"{total_feedback:,}\n", "metric_value")
        
        if total_classifications > 0:
            feedback_rate = total_feedback / total_classifications
            self.dashboard_text.insert(tk.END, f"📊 Feedback Rate: ", "metric_label")
            self.dashboard_text.insert(tk.END, f"{feedback_rate:.1%}\n", "metric_value")
        
        self.dashboard_text.insert(tk.END, "\n")
    
    def _display_category_metrics(self, metrics_data: Dict[str, Any]):
        """Display per-category metrics section."""
        category_metrics = metrics_data.get('category_metrics', {})
        if not category_metrics:
            return
        
        self.dashboard_text.insert(tk.END, "🎯 Category Performance\n", "subheading")
        self.dashboard_text.insert(tk.END, "─" * 80 + "\n", "monospace")
        
        # Table header
        self.dashboard_text.insert(tk.END, f"{'Category':<25} {'Accuracy':<12} {'Precision':<12} {'Recall':<12} {'Count':<8}\n", "monospace")
        self.dashboard_text.insert(tk.END, "─" * 80 + "\n", "monospace")
        
        # Sort by accuracy (best first)
        sorted_categories = sorted(
            category_metrics.items(),
            key=lambda x: x[1].get('accuracy', 0),
            reverse=True
        )
        
        for category, stats in sorted_categories:
            accuracy = stats.get('accuracy', 0.0)
            precision = stats.get('precision', 0.0)
            recall = stats.get('recall', 0.0)
            count = stats.get('count', 0)
            
            # Determine emoji based on accuracy
            if accuracy >= 0.9:
                emoji = "🟢"
            elif accuracy >= 0.75:
                emoji = "🟡"
            else:
                emoji = "🔴"
            
            line = f"{emoji} {category:<23} {accuracy:>10.1%}  {precision:>10.1%}  {recall:>10.1%}  {count:>6}\n"
            self.dashboard_text.insert(tk.END, line, "monospace")
        
        self.dashboard_text.insert(tk.END, "\n")
    
    def _display_confusion_matrix(self, metrics_data: Dict[str, Any]):
        """Display confusion matrix section."""
        confusion_matrix = metrics_data.get('confusion_matrix', {})
        if not confusion_matrix:
            return
        
        self.dashboard_text.insert(tk.END, "🔀 Common Misclassifications\n", "subheading")
        self.dashboard_text.insert(tk.END, "─" * 80 + "\n", "monospace")
        
        # Show top misclassifications
        misclassifications = []
        for predicted, actual_dict in confusion_matrix.items():
            for actual, count in actual_dict.items():
                if predicted != actual:
                    misclassifications.append((predicted, actual, count))
        
        # Sort by count
        misclassifications.sort(key=lambda x: x[2], reverse=True)
        
        if misclassifications:
            self.dashboard_text.insert(tk.END, f"{'Predicted As':<25} {'Actually Was':<25} {'Count':<10}\n", "monospace")
            self.dashboard_text.insert(tk.END, "─" * 80 + "\n", "monospace")
            
            for predicted, actual, count in misclassifications[:10]:  # Top 10
                line = f"❌ {predicted:<23} ➜ {actual:<23} {count:>6}\n"
                self.dashboard_text.insert(tk.END, line, "warning")
        else:
            self.dashboard_text.insert(tk.END, "✅ No misclassifications recorded yet!\n", "success")
        
        self.dashboard_text.insert(tk.END, "\n")
    
    def _display_trends(self, metrics_data: Dict[str, Any]):
        """Display time series trends section."""
        time_series = metrics_data.get('time_series', [])
        trends = metrics_data.get('trends', {})
        
        if not time_series and not trends:
            return
        
        self.dashboard_text.insert(tk.END, "📅 Trends & Historical Performance\n", "subheading")
        self.dashboard_text.insert(tk.END, "─" * 80 + "\n", "monospace")
        
        # Trend summary
        if trends:
            trend_direction = trends.get('direction', 'stable')
            if trend_direction == 'improving':
                emoji = "📈"
                tag = "success"
            elif trend_direction == 'declining':
                emoji = "📉"
                tag = "warning"
            else:
                emoji = "➡️"
                tag = "metric_value"
            
            self.dashboard_text.insert(tk.END, f"{emoji} Trend: ", "metric_label")
            self.dashboard_text.insert(tk.END, f"{trend_direction.capitalize()}\n", tag)
            
            if 'change_7day' in trends:
                change = trends['change_7day']
                sign = "+" if change > 0 else ""
                self.dashboard_text.insert(tk.END, f"📊 7-Day Change: ", "metric_label")
                self.dashboard_text.insert(tk.END, f"{sign}{change:.1%}\n", tag)
            
            if 'change_30day' in trends:
                change = trends['change_30day']
                sign = "+" if change > 0 else ""
                self.dashboard_text.insert(tk.END, f"📊 30-Day Change: ", "metric_label")
                self.dashboard_text.insert(tk.END, f"{sign}{change:.1%}\n", tag)
        
        # Recent daily metrics
        if time_series:
            self.dashboard_text.insert(tk.END, "\nRecent Daily Accuracy:\n", "metric_label")
            self.dashboard_text.insert(tk.END, "─" * 80 + "\n", "monospace")
            
            for day_data in time_series[-7:]:  # Last 7 days
                date = day_data.get('date', 'Unknown')
                accuracy = day_data.get('accuracy', 0.0)
                count = day_data.get('count', 0)
                
                # Simple ASCII bar chart
                bar_length = int(accuracy * 20)
                bar = "█" * bar_length + "░" * (20 - bar_length)
                
                line = f"{date:<12} {bar} {accuracy:>6.1%}  ({count} emails)\n"
                self.dashboard_text.insert(tk.END, line, "monospace")
        
        self.dashboard_text.insert(tk.END, "\n")
        
        # Chart availability message
        try:
            import matplotlib
            self.dashboard_text.insert(tk.END, "💡 Tip: Install matplotlib for visual trend charts: pip install matplotlib\n", "metric_value")
        except ImportError:
            pass
    
    def show_error(self, error_message: str):
        """Show an error message in the dashboard area.
        
        Args:
            error_message: Error message to display
        """
        self.dashboard_text.config(state=tk.NORMAL)
        self.dashboard_text.delete(1.0, tk.END)
        self.dashboard_text.insert(tk.END, f"❌ Error loading accuracy metrics:\n\n{error_message}\n\nPlease try refreshing.", "error")
        self.dashboard_text.config(state=tk.DISABLED)
    
    def clear_dashboard(self):
        """Clear the dashboard display."""
        self.dashboard_text.config(state=tk.NORMAL)
        self.dashboard_text.delete(1.0, tk.END)
        self.dashboard_text.config(state=tk.DISABLED)
    
    def set_refresh_button_state(self, enabled: bool):
        """Set refresh button state.
        
        Args:
            enabled: Whether button should be enabled
        """
        self.refresh_btn.config(state=tk.NORMAL if enabled else tk.DISABLED)
    
    def append_text(self, text: str, tag: Optional[str] = None):
        """Append text to dashboard area.
        
        Args:
            text: Text to append
            tag: Optional tag for formatting
        """
        self.dashboard_text.config(state=tk.NORMAL)
        if tag:
            self.dashboard_text.insert(tk.END, text, tag)
        else:
            self.dashboard_text.insert(tk.END, text)
        self.dashboard_text.see(tk.END)
        self.dashboard_text.config(state=tk.DISABLED)
