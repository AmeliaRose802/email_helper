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
    <div style={{
      width: '100%',
      padding: '16px',
      backgroundColor: '#f8f9fa',
      borderRadius: '8px',
      marginBottom: '16px',
    }}>
      {label && (
        <div style={{
          marginBottom: '8px',
          fontSize: '14px',
          color: '#495057',
          fontWeight: '500',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <span>{label}</span>
          {showPercentage && (
            <span style={{ color: '#6c757d' }}>
              {current} / {total} ({percentage}%)
            </span>
          )}
        </div>
      )}
      <div style={{
        width: '100%',
        height: `${height}px`,
        backgroundColor: '#e9ecef',
        borderRadius: `${height / 2}px`,
        overflow: 'hidden',
        position: 'relative',
      }}>
        <div
          style={{
            width: `${percentage}%`,
            height: '100%',
            backgroundColor: color,
            transition: 'width 0.3s ease-in-out',
            borderRadius: `${height / 2}px`,
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Animated shimmer effect */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: '-100%',
              width: '100%',
              height: '100%',
              background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
              animation: 'shimmer 2s infinite',
            }}
          />
        </div>
      </div>
      <style>
        {`
          @keyframes shimmer {
            0% { left: -100%; }
            100% { left: 100%; }
          }
        `}
      </style>
    </div>
  );
};
