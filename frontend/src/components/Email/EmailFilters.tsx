// Email filters component for advanced filtering
import React from 'react';
import type { EmailFilter } from '@/types/email';

interface EmailFiltersProps {
  filters: EmailFilter;
  onChange: (filters: Partial<EmailFilter>) => void;
  className?: string;
}

export const EmailFilters: React.FC<EmailFiltersProps> = ({
  filters,
  onChange,
  className = '',
}) => {
  const handleFilterChange = (key: keyof EmailFilter, value: any) => {
    onChange({ [key]: value === '' ? undefined : value });
  };
  
  const handleCheckboxChange = (key: keyof EmailFilter, checked: boolean) => {
    onChange({ [key]: checked ? true : undefined });
  };
  
  const clearAllFilters = () => {
    onChange({
      folder: undefined,
      sender: undefined,
      subject: undefined,
      date_from: undefined,
      date_to: undefined,
      is_read: undefined,
      has_attachments: undefined,
      importance: undefined,
    });
  };
  
  const hasActiveFilters = Object.values(filters).some(value => value !== undefined);
  
  const containerStyle = {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '16px',
    padding: '16px',
    backgroundColor: '#f8f9fa',
    borderRadius: '8px',
    border: '1px solid #e0e0e0',
  };
  
  const filterGroupStyle = {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '4px',
    minWidth: '120px',
  };
  
  const labelStyle = {
    fontSize: '12px',
    fontWeight: '600',
    color: '#495057',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
  };
  
  const inputStyle = {
    padding: '6px 8px',
    border: '1px solid #ced4da',
    borderRadius: '4px',
    fontSize: '14px',
    outline: 'none',
    transition: 'border-color 0.2s ease',
  };
  
  const selectStyle = {
    ...inputStyle,
    backgroundColor: '#fff',
    cursor: 'pointer',
  };
  
  const checkboxGroupStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginTop: '4px',
  };
  
  const clearButtonStyle = {
    alignSelf: 'flex-end' as const,
    padding: '6px 12px',
    backgroundColor: hasActiveFilters ? '#dc3545' : '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: '600',
    cursor: hasActiveFilters ? 'pointer' : 'not-allowed',
    opacity: hasActiveFilters ? 1 : 0.6,
    transition: 'all 0.2s ease',
  };
  
  return (
    <div className={`email-filters ${className}`} style={containerStyle}>
      <style>
        {`
          .email-filters input:focus,
          .email-filters select:focus {
            border-color: #007acc !important;
            box-shadow: 0 0 0 2px rgba(0, 122, 204, 0.1) !important;
          }
          
          .clear-filters:hover:not(:disabled) {
            background-color: #c82333 !important;
            transform: translateY(-1px);
          }
        `}
      </style>
      
      {/* Read Status Filter */}
      <div style={filterGroupStyle}>
        <label style={labelStyle}>Status</label>
        <div style={checkboxGroupStyle}>
          <input
            type="checkbox"
            id="unread-only"
            checked={filters.is_read === false}
            onChange={(e) => handleCheckboxChange('is_read', !e.target.checked)}
          />
          <label htmlFor="unread-only" style={{ fontSize: '14px', cursor: 'pointer' }}>
            Unread only
          </label>
        </div>
      </div>
      
      {/* Importance Filter */}
      <div style={filterGroupStyle}>
        <label style={labelStyle}>Importance</label>
        <select
          value={filters.importance || ''}
          onChange={(e) => handleFilterChange('importance', e.target.value)}
          style={selectStyle}
        >
          <option value="">All</option>
          <option value="High">High</option>
          <option value="Normal">Normal</option>
          <option value="Low">Low</option>
        </select>
      </div>
      
      {/* Attachments Filter */}
      <div style={filterGroupStyle}>
        <label style={labelStyle}>Attachments</label>
        <div style={checkboxGroupStyle}>
          <input
            type="checkbox"
            id="has-attachments"
            checked={filters.has_attachments === true}
            onChange={(e) => handleCheckboxChange('has_attachments', e.target.checked)}
          />
          <label htmlFor="has-attachments" style={{ fontSize: '14px', cursor: 'pointer' }}>
            Has attachments
          </label>
        </div>
      </div>
      
      {/* Sender Filter */}
      <div style={filterGroupStyle}>
        <label style={labelStyle}>Sender</label>
        <input
          type="text"
          value={filters.sender || ''}
          onChange={(e) => handleFilterChange('sender', e.target.value)}
          placeholder="Filter by sender"
          style={inputStyle}
        />
      </div>
      
      {/* Subject Filter */}
      <div style={filterGroupStyle}>
        <label style={labelStyle}>Subject</label>
        <input
          type="text"
          value={filters.subject || ''}
          onChange={(e) => handleFilterChange('subject', e.target.value)}
          placeholder="Filter by subject"
          style={inputStyle}
        />
      </div>
      
      {/* Date Range Filters */}
      <div style={filterGroupStyle}>
        <label style={labelStyle}>Date From</label>
        <input
          type="date"
          value={filters.date_from || ''}
          onChange={(e) => handleFilterChange('date_from', e.target.value)}
          style={inputStyle}
        />
      </div>
      
      <div style={filterGroupStyle}>
        <label style={labelStyle}>Date To</label>
        <input
          type="date"
          value={filters.date_to || ''}
          onChange={(e) => handleFilterChange('date_to', e.target.value)}
          style={inputStyle}
        />
      </div>
      
      {/* Clear Filters Button */}
      <button
        type="button"
        className="clear-filters"
        onClick={clearAllFilters}
        disabled={!hasActiveFilters}
        style={clearButtonStyle}
        title="Clear all filters"
      >
        Clear Filters
      </button>
    </div>
  );
};