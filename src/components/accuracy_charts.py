#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Accuracy Charts Component - Matplotlib charts for accuracy dashboard
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from datetime import datetime, timedelta


class AccuracyChartsComponent:
    """Component for creating and managing accuracy visualization charts"""
    
    def __init__(self, parent_frame, accuracy_tracker):
        self.parent_frame = parent_frame
        self.accuracy_tracker = accuracy_tracker
        self.charts = {}
        
        # Set matplotlib style
        plt.style.use('default')
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72', 
            'success': '#2ECC71',
            'warning': '#F39C12',
            'danger': '#E74C3C',
            'background': '#F8F9FA',
            'text': '#2C3E50'
        }
        
    def create_trend_chart(self, chart_frame, granularity='daily'):
        """Create accuracy trend line chart"""
        try:
            # Get data
            data = self.accuracy_tracker.get_time_series_data(granularity=granularity, days_back=30)
            
            if not data:
                return self._create_no_data_chart(chart_frame, "No trend data available")
            
            # Create figure
            fig = Figure(figsize=(8, 4), dpi=100, facecolor='white')
            ax = fig.add_subplot(111)
            
            # Extract data for plotting
            dates = [item['date'] for item in data]
            accuracies = [item['accuracy'] for item in data]
            
            # Plot line with markers
            ax.plot(dates, accuracies, color=self.colors['primary'], 
                   linewidth=2, marker='o', markersize=6, alpha=0.8)
            
            # Fill area under curve
            ax.fill_between(dates, accuracies, alpha=0.2, color=self.colors['primary'])
            
            # Styling
            ax.set_title('Accuracy Trend Over Time', fontsize=14, fontweight='bold', 
                        color=self.colors['text'], pad=20)
            ax.set_ylabel('Accuracy (%)', fontsize=12, color=self.colors['text'])
            ax.set_xlabel('Date', fontsize=12, color=self.colors['text'])
            
            # Grid and formatting
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.set_ylim(0, 100)
            
            # Format x-axis dates
            if len(dates) > 7:
                ax.tick_params(axis='x', rotation=45)
            
            # Tight layout
            fig.tight_layout()
            
            # Embed in tkinter
            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            
            self.charts['trend'] = {'figure': fig, 'canvas': canvas}
            return canvas
            
        except Exception as e:
            print(f"Error creating trend chart: {e}")
            return self._create_error_chart(chart_frame, f"Error: {e}")
    
    def create_category_performance_chart(self, chart_frame):
        """Create category performance horizontal bar chart"""
        try:
            # Get data
            data = self.accuracy_tracker.get_category_performance_summary(days_back=30)
            
            if not data:
                return self._create_no_data_chart(chart_frame, "No category data available")
            
            # Limit to top 8 categories for readability
            data = data[:8]
            
            # Create figure
            fig = Figure(figsize=(8, 6), dpi=100, facecolor='white')
            ax = fig.add_subplot(111)
            
            # Extract data for plotting
            categories = [item['category'] for item in data]
            accuracies = [item['accuracy'] for item in data]
            
            # Color code by performance
            colors = []
            for accuracy in accuracies:
                if accuracy >= 85:
                    colors.append(self.colors['success'])
                elif accuracy >= 70:
                    colors.append(self.colors['warning'])
                else:
                    colors.append(self.colors['danger'])
            
            # Create horizontal bar chart
            bars = ax.barh(categories, accuracies, color=colors, alpha=0.8, height=0.6)
            
            # Add value labels on bars
            for i, (bar, accuracy) in enumerate(zip(bars, accuracies)):
                ax.text(accuracy + 1, bar.get_y() + bar.get_height()/2, 
                       f'{accuracy:.1f}%', va='center', fontweight='bold',
                       color=self.colors['text'])
            
            # Styling
            ax.set_title('Category Performance (Last 30 Days)', fontsize=14, 
                        fontweight='bold', color=self.colors['text'], pad=20)
            ax.set_xlabel('Accuracy (%)', fontsize=12, color=self.colors['text'])
            ax.set_xlim(0, 100)
            
            # Grid
            ax.grid(True, axis='x', alpha=0.3, linestyle='--')
            
            # Tight layout
            fig.tight_layout()
            
            # Embed in tkinter
            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            
            self.charts['category'] = {'figure': fig, 'canvas': canvas}
            return canvas
            
        except Exception as e:
            print(f"Error creating category chart: {e}")
            return self._create_error_chart(chart_frame, f"Error: {e}")
    
    def create_session_comparison_chart(self, chart_frame):
        """Create session comparison bar chart"""
        try:
            # Get data
            data = self.accuracy_tracker.get_session_comparison_data(session_count=10)
            
            if not data:
                return self._create_no_data_chart(chart_frame, "No session data available")
            
            # Create figure
            fig = Figure(figsize=(8, 4), dpi=100, facecolor='white')
            ax = fig.add_subplot(111)
            
            # Extract data for plotting
            session_labels = [f"S{i+1}" for i in range(len(data))]
            accuracies = [item['accuracy'] for item in data]
            
            # Calculate session-to-session changes
            changes = [0]  # First session has no change
            for i in range(1, len(accuracies)):
                changes.append(accuracies[i] - accuracies[i-1])
            
            # Color code by change
            colors = []
            for change in changes:
                if change > 2:
                    colors.append(self.colors['success'])
                elif change < -2:
                    colors.append(self.colors['danger'])
                else:
                    colors.append(self.colors['primary'])
            
            # Create bar chart
            bars = ax.bar(session_labels, accuracies, color=colors, alpha=0.8, width=0.6)
            
            # Add value labels on bars
            for bar, accuracy, change in zip(bars, accuracies, changes):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                       f'{accuracy:.1f}%', ha='center', va='bottom', fontweight='bold',
                       color=self.colors['text'])
                
                # Add change indicator for sessions after the first
                if change != 0:
                    symbol = '↑' if change > 0 else '↓'
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2,
                           f'{symbol}{abs(change):.1f}', ha='center', va='center',
                           color='white', fontweight='bold', fontsize=10)
            
            # Styling
            ax.set_title('Recent Session Comparison', fontsize=14, fontweight='bold',
                        color=self.colors['text'], pad=20)
            ax.set_ylabel('Accuracy (%)', fontsize=12, color=self.colors['text'])
            ax.set_xlabel('Sessions (Most Recent)', fontsize=12, color=self.colors['text'])
            ax.set_ylim(0, 100)
            
            # Grid
            ax.grid(True, axis='y', alpha=0.3, linestyle='--')
            
            # Tight layout
            fig.tight_layout()
            
            # Embed in tkinter
            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            
            self.charts['session'] = {'figure': fig, 'canvas': canvas}
            return canvas
            
        except Exception as e:
            print(f"Error creating session chart: {e}")
            return self._create_error_chart(chart_frame, f"Error: {e}")
    
    def create_summary_gauges(self, gauge_frame):
        """Create summary gauge widgets"""
        try:
            # Get dashboard metrics
            metrics = self.accuracy_tracker.get_dashboard_metrics()
            
            # Clear existing widgets
            for widget in gauge_frame.winfo_children():
                widget.destroy()
            
            # Create gauge widgets in a grid
            self._create_gauge_widget(gauge_frame, "Overall Accuracy", 
                                    f"{metrics['overall_accuracy']}%", 
                                    metrics['overall_accuracy'], row=0, col=0)
            
            self._create_gauge_widget(gauge_frame, "7-Day Average", 
                                    f"{metrics['seven_day_average']}%", 
                                    metrics['seven_day_average'], row=0, col=1)
            
            self._create_gauge_widget(gauge_frame, "Total Sessions", 
                                    str(metrics['total_sessions']), 
                                    100, row=1, col=0)  # Full bar for count
            
            trend_text = metrics['trend_indicator'].title()
            trend_emoji = {"improving": "📈", "declining": "📉", "stable": "➡️"}
            self._create_trend_widget(gauge_frame, "Trend", 
                                    f"{trend_emoji.get(metrics['trend_indicator'], '➡️')} {trend_text}",
                                    metrics['trend_indicator'], row=1, col=1)
            
        except Exception as e:
            print(f"Error creating summary gauges: {e}")
            # Create error display
            ttk.Label(gauge_frame, text=f"Error loading metrics: {e}",
                     foreground='red').pack(pady=10)
    
    def _create_gauge_widget(self, parent, title, value, percentage, row, col):
        """Create a single gauge widget"""
        frame = ttk.LabelFrame(parent, text=title, padding=10)
        frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        
        # Value label
        value_label = ttk.Label(frame, text=value, font=('Arial', 16, 'bold'))
        value_label.pack()
        
        # Progress bar for percentage
        if percentage <= 100:
            progress = ttk.Progressbar(frame, length=100, mode='determinate')
            progress['value'] = percentage
            progress.pack(pady=(5, 0))
    
    def _create_trend_widget(self, parent, title, value, trend, row, col):
        """Create a trend indicator widget"""
        frame = ttk.LabelFrame(parent, text=title, padding=10)
        frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        
        # Color based on trend
        color = 'green' if trend == 'improving' else 'red' if trend == 'declining' else 'blue'
        
        value_label = ttk.Label(frame, text=value, font=('Arial', 12, 'bold'), 
                               foreground=color)
        value_label.pack()
    
    def _create_no_data_chart(self, parent, message):
        """Create a placeholder chart when no data is available"""
        fig = Figure(figsize=(8, 4), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)
        
        ax.text(0.5, 0.5, message, ha='center', va='center', fontsize=16,
               color=self.colors['text'], transform=ax.transAxes)
        ax.text(0.5, 0.3, "Process some emails to see charts", ha='center', va='center', 
               fontsize=12, color='gray', transform=ax.transAxes)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        return canvas
    
    def _create_error_chart(self, parent, error_message):
        """Create an error display chart"""
        fig = Figure(figsize=(8, 4), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)
        
        ax.text(0.5, 0.5, "Chart Error", ha='center', va='center', fontsize=16,
               color=self.colors['danger'], transform=ax.transAxes, fontweight='bold')
        ax.text(0.5, 0.3, error_message, ha='center', va='center', fontsize=10,
               color='gray', transform=ax.transAxes, wrap=True)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        return canvas
    
    def refresh_all_charts(self, granularity='daily'):
        """Refresh all charts with latest data"""
        try:
            # Find chart containers and refresh them
            for chart_name, chart_info in self.charts.items():
                if 'canvas' in chart_info:
                    # Destroy old canvas
                    chart_info['canvas'].get_tk_widget().destroy()
            
            # Clear charts dict
            self.charts.clear()
            
            # Note: This method should be called by the parent to recreate charts
            print("Charts cleared - parent should recreate them")
            
        except Exception as e:
            print(f"Error refreshing charts: {e}")