import React from 'react';
import { formatDistanceToNow, isAfter, parseISO, format } from 'date-fns';

interface DeadlineIndicatorProps {
  deadline: string;
  className?: string;
}

export const DeadlineIndicator: React.FC<DeadlineIndicatorProps> = ({ 
  deadline, 
  className = '' 
}) => {
  const deadlineDate = parseISO(deadline);
  const now = new Date();
  const isOverdue = isAfter(now, deadlineDate);
  const timeLeft = formatDistanceToNow(deadlineDate, { addSuffix: true });
  
  const getStatusClass = () => {
    if (isOverdue) return 'deadline-overdue';
    
    const hoursLeft = (deadlineDate.getTime() - now.getTime()) / (1000 * 60 * 60);
    if (hoursLeft <= 24) return 'deadline-urgent';
    if (hoursLeft <= 72) return 'deadline-warning';
    return 'deadline-normal';
  };

  return (
    <div className={`deadline-indicator ${getStatusClass()} ${className}`}>
      <span className="deadline-icon">
        {isOverdue ? '⚠️' : '📅'}
      </span>
      <div className="deadline-info">
        <span className="deadline-time">{timeLeft}</span>
        <span className="deadline-date">{format(deadlineDate, 'MMM d, yyyy')}</span>
      </div>
    </div>
  );
};