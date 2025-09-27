import React from 'react';
import type { Task } from '@/types/task';

interface ProgressTrackerProps {
  tasks: Task[];
}

export const ProgressTracker: React.FC<ProgressTrackerProps> = ({ tasks }) => {
  const stats = React.useMemo(() => {
    const total = tasks.length;
    const todoCount = tasks.filter(t => t.status === 'todo').length;
    const inProgressCount = tasks.filter(t => t.status === 'in-progress').length;
    const reviewCount = tasks.filter(t => t.status === 'review').length;
    const doneCount = tasks.filter(t => t.status === 'done').length;
    
    const overdue = tasks.filter(t => 
      t.due_date && new Date(t.due_date) < new Date()
    ).length;
    
    const highPriority = tasks.filter(t => t.priority === 'high').length;
    
    const completionRate = total > 0 ? (doneCount / total) * 100 : 0;
    
    return {
      total,
      todoCount,
      inProgressCount,
      reviewCount,
      doneCount,
      overdue,
      highPriority,
      completionRate,
    };
  }, [tasks]);

  return (
    <div className="progress-tracker">
      <div className="progress-summary">
        <div className="overall-progress">
          <h3>Overall Progress</h3>
          <div className="progress-circle">
            <div className="progress-text">
              <span className="percentage">{Math.round(stats.completionRate)}%</span>
              <span className="label">Complete</span>
            </div>
            <svg className="progress-ring" width="120" height="120">
              <circle
                className="progress-ring-background"
                cx="60"
                cy="60"
                r="54"
                fill="transparent"
                stroke="#e5e7eb"
                strokeWidth="6"
              />
              <circle
                className="progress-ring-progress"
                cx="60"
                cy="60"
                r="54"
                fill="transparent"
                stroke="#10b981"
                strokeWidth="6"
                strokeDasharray={`${2 * Math.PI * 54}`}
                strokeDashoffset={`${2 * Math.PI * 54 * (1 - stats.completionRate / 100)}`}
                transform="rotate(-90 60 60)"
              />
            </svg>
          </div>
        </div>

        <div className="status-breakdown">
          <h4>Status Breakdown</h4>
          <div className="status-stats">
            <div className="stat-item todo">
              <div className="stat-bar">
                <div 
                  className="stat-fill"
                  style={{ 
                    width: stats.total > 0 ? `${(stats.todoCount / stats.total) * 100}%` : '0%' 
                  }}
                />
              </div>
              <div className="stat-info">
                <span className="stat-label">To Do</span>
                <span className="stat-count">{stats.todoCount}</span>
              </div>
            </div>

            <div className="stat-item in-progress">
              <div className="stat-bar">
                <div 
                  className="stat-fill"
                  style={{ 
                    width: stats.total > 0 ? `${(stats.inProgressCount / stats.total) * 100}%` : '0%' 
                  }}
                />
              </div>
              <div className="stat-info">
                <span className="stat-label">In Progress</span>
                <span className="stat-count">{stats.inProgressCount}</span>
              </div>
            </div>

            <div className="stat-item review">
              <div className="stat-bar">
                <div 
                  className="stat-fill"
                  style={{ 
                    width: stats.total > 0 ? `${(stats.reviewCount / stats.total) * 100}%` : '0%' 
                  }}
                />
              </div>
              <div className="stat-info">
                <span className="stat-label">Review</span>
                <span className="stat-count">{stats.reviewCount}</span>
              </div>
            </div>

            <div className="stat-item done">
              <div className="stat-bar">
                <div 
                  className="stat-fill"
                  style={{ 
                    width: stats.total > 0 ? `${(stats.doneCount / stats.total) * 100}%` : '0%' 
                  }}
                />
              </div>
              <div className="stat-info">
                <span className="stat-label">Done</span>
                <span className="stat-count">{stats.doneCount}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="alert-stats">
          <div className="alert-item overdue">
            <span className="alert-icon">⚠️</span>
            <div className="alert-info">
              <span className="alert-count">{stats.overdue}</span>
              <span className="alert-label">Overdue</span>
            </div>
          </div>

          <div className="alert-item high-priority">
            <span className="alert-icon">🔴</span>
            <div className="alert-info">
              <span className="alert-count">{stats.highPriority}</span>
              <span className="alert-label">High Priority</span>
            </div>
          </div>

          <div className="alert-item total">
            <span className="alert-icon">📋</span>
            <div className="alert-info">
              <span className="alert-count">{stats.total}</span>
              <span className="alert-label">Total Tasks</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};