// Category badge component for AI email categorization
import React from 'react';
import { getCategoryColor, getCategoryLabel } from '@/utils/emailUtils';

interface CategoryBadgeProps {
  category: string;
  confidence?: number;
  size?: 'small' | 'medium' | 'large';
  showConfidence?: boolean;
  className?: string;
}

export const CategoryBadge: React.FC<CategoryBadgeProps> = ({
  category,
  confidence,
  size = 'medium',
  showConfidence = false,
  className = '',
}) => {
  const color = getCategoryColor(category);
  const label = getCategoryLabel(category);
  
  const sizeClasses = {
    small: 'px-2 py-1 text-xs',
    medium: 'px-3 py-1 text-sm',
    large: 'px-4 py-2 text-base',
  };
  
  const badgeStyle = {
    backgroundColor: color,
    color: 'white',
    borderRadius: '12px',
    fontWeight: '500',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    whiteSpace: 'nowrap' as const,
  };
  
  return (
    <span
      className={`category-badge ${sizeClasses[size]} ${className}`}
      style={badgeStyle}
      title={confidence ? `${label} (${Math.round(confidence * 100)}% confidence)` : label}
    >
      {label}
      {showConfidence && confidence && (
        <span className="confidence-indicator" style={{ fontSize: '0.8em', opacity: 0.9 }}>
          {Math.round(confidence * 100)}%
        </span>
      )}
    </span>
  );
};