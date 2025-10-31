// Progress bar component for email loading and classification
import React from 'react';

interface ProgressBarProps {
  current: number;
  total: number;
  label?: string;
  showPercentage?: boolean;
  color?: string;
  height?: number;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  current,
  total,
  label = 'Processing...',
  showPercentage = true,
  color = '#4a90e2',
  height = 24,
}) => {
  const percentage = total > 0 ? Math.min(100, Math.round((current / total) * 100)) : 0;

  return (
    <div className="email-progress-container">
      {label && (
        <div className="email-progress-label">
          <span>{label}</span>
          {showPercentage && (
            <span className="email-progress-count">
              {current} / {total} ({percentage}%)
            </span>
          )}
        </div>
      )}
      <div 
        className="email-progress-track"
        style={{ height: `${height}px` }}
      >
        <div
          className="email-progress-fill"
          style={{
            width: `${percentage}%`,
            backgroundColor: color,
          }}
        >
          <div className="email-progress-shimmer" />
        </div>
      </div>
    </div>
  );
};
