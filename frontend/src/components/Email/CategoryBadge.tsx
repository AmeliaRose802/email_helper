// Category badge component for AI email categorization
import React from 'react';
import { getCategoryLabel } from '@/utils/emailUtils';

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
  const label = getCategoryLabel(category);
  
  const sizeClass = `category-badge--${size}`;
  const categoryClass = `category-badge--${category.replace(/_/g, '-')}`;
  
  return (
    <span
      className={`category-badge ${sizeClass} ${categoryClass} ${className}`}
      title={confidence ? `${label} (${Math.round(confidence * 100)}% confidence)` : label}
    >
      {label}
      {showConfidence && confidence && (
        <span className="category-badge__confidence">
          {Math.round(confidence * 100)}%
        </span>
      )}
    </span>
  );
};