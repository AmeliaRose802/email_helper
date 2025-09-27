// Search bar component with debounced search functionality
import React, { useState, useEffect, useCallback } from 'react';
import debounce from 'lodash.debounce';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  isLoading?: boolean;
  placeholder?: string;
  className?: string;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChange,
  isLoading = false,
  placeholder = 'Search emails...',
  className = '',
}) => {
  const [localValue, setLocalValue] = useState(value);
  
  // Debounced search function
  const debouncedSearch = useCallback(
    debounce((searchValue: string) => {
      onChange(searchValue);
    }, 300),
    [onChange]
  );
  
  // Update local value when prop changes
  useEffect(() => {
    setLocalValue(value);
  }, [value]);
  
  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setLocalValue(newValue);
    debouncedSearch(newValue);
  };
  
  // Handle clear button
  const handleClear = () => {
    setLocalValue('');
    debouncedSearch('');
  };
  
  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape') {
      handleClear();
      e.currentTarget.blur();
    }
  };
  
  const searchBarStyle = {
    position: 'relative' as const,
    display: 'flex',
    alignItems: 'center',
    width: '100%',
    maxWidth: '400px',
  };
  
  const inputStyle = {
    width: '100%',
    padding: '12px 16px',
    paddingRight: localValue ? '80px' : '48px',
    border: '2px solid #e0e0e0',
    borderRadius: '24px',
    fontSize: '14px',
    outline: 'none',
    transition: 'border-color 0.2s ease',
    backgroundColor: '#fff',
  };
  
  const iconStyle = {
    position: 'absolute' as const,
    left: '16px',
    fontSize: '16px',
    color: '#6c757d',
    pointerEvents: 'none' as const,
  };
  
  const clearButtonStyle = {
    position: 'absolute' as const,
    right: '12px',
    background: 'none',
    border: 'none',
    fontSize: '16px',
    color: '#6c757d',
    cursor: 'pointer',
    padding: '4px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'color 0.2s ease',
  };
  
  const loadingSpinnerStyle = {
    position: 'absolute' as const,
    right: localValue ? '44px' : '16px',
    fontSize: '14px',
    color: '#007acc',
    animation: 'spin 1s linear infinite',
  };
  
  return (
    <div className={`search-bar ${className}`} style={searchBarStyle}>
      <style>
        {`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          
          .search-input:focus {
            border-color: #007acc !important;
            box-shadow: 0 0 0 3px rgba(0, 122, 204, 0.1) !important;
          }
          
          .clear-button:hover {
            color: #dc3545 !important;
            background-color: rgba(220, 53, 69, 0.1) !important;
          }
        `}
      </style>
      
      <span style={iconStyle}>🔍</span>
      
      <input
        type="text"
        className="search-input"
        value={localValue}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        style={inputStyle}
        disabled={isLoading}
      />
      
      {isLoading && (
        <span style={loadingSpinnerStyle}>⟳</span>
      )}
      
      {localValue && !isLoading && (
        <button
          type="button"
          className="clear-button"
          onClick={handleClear}
          style={clearButtonStyle}
          title="Clear search"
        >
          ✕
        </button>
      )}
    </div>
  );
};