import React from 'react';
import { useDrag } from 'react-dnd';
import { DeadlineIndicator } from './DeadlineIndicator';
import { formatDistanceToNow, parseISO } from 'date-fns';
import type { Task } from '@/types/task';

interface TaskCardProps {
  task: Task;
  onEdit: () => void;
  onDelete?: () => void;
}

export const TaskCard: React.FC<TaskCardProps> = ({ task, onEdit, onDelete }) => {
  const [{ isDragging }, drag] = useDrag({
    type: 'task',
    item: { 
      id: task.id, 
      currentStatus: task.status 
    },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  const priorityColors = {
    low: 'priority-low',
    medium: 'priority-medium', 
    high: 'priority-high',
  };

  const handleCardClick = (e: React.MouseEvent) => {
    e.preventDefault();
    onEdit();
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete();
    }
  };

  return (
    <div
      ref={drag as unknown as React.Ref<HTMLDivElement>}
      className={`task-card ${priorityColors[task.priority]} ${isDragging ? 'dragging' : ''}`}
      onClick={handleCardClick}
      style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
    >
      <div className="task-card-header">
        <h4 className="task-title">{task.title}</h4>
        <div className="task-actions">
          <span className={`priority-badge ${task.priority}`}>
            {task.priority}
          </span>
          {onDelete && (
            <button 
              className="delete-btn"
              onClick={handleDeleteClick}
              aria-label="Delete task"
            >
              ×
            </button>
          )}
        </div>
      </div>

      {task.description && (
        <p className="task-description">
          {task.description.length > 100 
            ? `${task.description.substring(0, 100)}...`
            : task.description
          }
        </p>
      )}

      {task.progress !== undefined && task.progress > 0 && (
        <div className="task-progress">
          <div className="progress-label">
            <span>Progress</span>
            <span>{task.progress}%</span>
          </div>
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ width: `${task.progress}%` }}
            />
          </div>
        </div>
      )}

      {task.tags && task.tags.length > 0 && (
        <div className="task-tags">
          {task.tags.slice(0, 3).map(tag => (
            <span key={tag} className="task-tag">{tag}</span>
          ))}
          {task.tags.length > 3 && (
            <span className="task-tag-more">+{task.tags.length - 3}</span>
          )}
        </div>
      )}

      <div className="task-card-footer">
        <div className="task-meta">
          {task.email_id && (
            <span className="email-link" title="Created from email">📧</span>
          )}
          <span className="task-date">
            {formatDistanceToNow(parseISO(task.created_at), { addSuffix: true })}
          </span>
        </div>
        
        {task.due_date && (
          <DeadlineIndicator deadline={task.due_date} />
        )}
      </div>
    </div>
  );
};