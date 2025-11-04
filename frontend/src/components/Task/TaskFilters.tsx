import React, { useState } from 'react';
import type { TaskFilter } from '@/types/task';

interface TaskFiltersProps {
  filters: TaskFilter;
  onChange: (filters: TaskFilter) => void;
  onReset: () => void;
}

export const TaskFilters: React.FC<TaskFiltersProps> = ({ filters, onChange, onReset }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [searchInput, setSearchInput] = useState(filters.search || '');

  const handleFilterChange = (key: keyof TaskFilter, value: TaskFilter[keyof TaskFilter]) => {
    onChange({
      ...filters,
      [key]: value || undefined,
    });
  };

  const handleSearchChange = (value: string) => {
    setSearchInput(value);
    // Debounce search
    interface WindowWithSearchTimeout extends Window {
      searchTimeout?: ReturnType<typeof setTimeout>;
    }
    clearTimeout((window as WindowWithSearchTimeout).searchTimeout);
    (window as WindowWithSearchTimeout).searchTimeout = setTimeout(() => {
      handleFilterChange('search', value.trim());
    }, 300);
  };

  const getActiveFilterCount = () => {
    return Object.values(filters).filter(value => 
      value !== undefined && value !== '' && 
      !(Array.isArray(value) && value.length === 0)
    ).length;
  };

  const activeCount = getActiveFilterCount();

  return (
    <div className="task-filters">
      <div className="filters-header">
        <div className="search-box">
          <input
            type="text"
            placeholder="Search tasks..."
            value={searchInput}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="search-input"
          />
          <span className="search-icon">🔍</span>
        </div>
        
        <div className="filter-controls">
          <button
            className="filter-toggle"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            Filters {activeCount > 0 && `(${activeCount})`}
            <span className={`toggle-icon ${isExpanded ? 'expanded' : ''}`}>▼</span>
          </button>
          
          {activeCount > 0 && (
            <button
              className="reset-filters"
              onClick={onReset}
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {isExpanded && (
        <div className="filters-content">
          <div className="filter-row">
            <div className="filter-group">
              <label>Status</label>
              <select
                value={filters.status || ''}
                onChange={(e) => handleFilterChange('status', e.target.value)}
              >
                <option value="">All</option>
                <option value="todo">To Do</option>
                <option value="in-progress">In Progress</option>
                <option value="review">Review</option>
                <option value="done">Done</option>
              </select>
            </div>

            <div className="filter-group">
              <label>Priority</label>
              <select
                value={filters.priority || ''}
                onChange={(e) => handleFilterChange('priority', e.target.value)}
              >
                <option value="">All</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            <div className="filter-group">
              <label>Category</label>
              <select
                value={filters.category || ''}
                onChange={(e) => handleFilterChange('category', e.target.value)}
              >
                <option value="">All</option>
                <option value="required_action">Required Action</option>
                <option value="team_action">Team Action</option>
                <option value="job_listing">Job Listing</option>
                <option value="optional_event">Optional Event</option>
                <option value="fyi">FYI</option>
              </select>
            </div>
          </div>

          <div className="filter-row">
            <div className="filter-group">
              <label>Due Date From</label>
              <input
                type="date"
                value={filters.due_date_from || ''}
                onChange={(e) => handleFilterChange('due_date_from', e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label>Due Date To</label>
              <input
                type="date"
                value={filters.due_date_to || ''}
                onChange={(e) => handleFilterChange('due_date_to', e.target.value)}
              />
            </div>

            <div className="filter-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={filters.overdue || false}
                  onChange={(e) => handleFilterChange('overdue', e.target.checked)}
                />
                Show only overdue
              </label>
            </div>
          </div>

          <div className="filter-row">
            <div className="filter-group">
              <label>Email ID</label>
              <input
                type="text"
                placeholder="Filter by email ID"
                value={filters.email_id || ''}
                onChange={(e) => handleFilterChange('email_id', e.target.value)}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};