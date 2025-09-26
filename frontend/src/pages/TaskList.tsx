// Task list page component - placeholder for T8
import React, { useState } from 'react';
import { useGetTasksQuery } from '@/services/taskApi';
import type { TaskFilter } from '@/types/task';

const TaskList: React.FC = () => {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<TaskFilter>({});

  const {
    data: taskData,
    isLoading,
    error,
  } = useGetTasksQuery({
    page,
    per_page: 20,
    ...filters,
  });

  const handleFilterChange = (newFilters: Partial<TaskFilter>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
    setPage(1); // Reset to first page when filters change
  };

  if (isLoading) {
    return <div className="task-list-loading">Loading tasks...</div>;
  }

  if (error) {
    return <div className="task-list-error">Error loading tasks</div>;
  }

  return (
    <div className="task-list">
      <h1>Task List</h1>

      <div className="task-filters">
        <h3>Filters</h3>
        <div className="filter-controls">
          <label>
            Status:
            <select
              value={filters.status || ''}
              onChange={(e) =>
                handleFilterChange({
                  status: (e.target.value as TaskFilter['status']) || undefined,
                })
              }
            >
              <option value="">All statuses</option>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </label>

          <label>
            Priority:
            <select
              value={filters.priority || ''}
              onChange={(e) =>
                handleFilterChange({
                  priority: (e.target.value as TaskFilter['priority']) || undefined,
                })
              }
            >
              <option value="">All priorities</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </label>

          <label>
            Category:
            <select
              value={filters.category || ''}
              onChange={(e) =>
                handleFilterChange({
                  category: (e.target.value as TaskFilter['category']) || undefined,
                })
              }
            >
              <option value="">All categories</option>
              <option value="required_action">Required Action</option>
              <option value="team_action">Team Action</option>
              <option value="job_listing">Job Listing</option>
              <option value="optional_event">Optional Event</option>
              <option value="fyi">FYI</option>
            </select>
          </label>
        </div>
      </div>

      <div className="task-results">
        {taskData && (
          <>
            <p>
              Showing {taskData.tasks.length} of {taskData.total_count} tasks
            </p>

            {taskData.tasks.length === 0 ? (
              <p>No tasks found matching your filters.</p>
            ) : (
              <div className="task-items">
                {taskData.tasks.map((task) => (
                  <div
                    key={task.id}
                    className={`task-item priority-${task.priority} status-${task.status}`}
                  >
                    <div className="task-header">
                      <strong>{task.title}</strong>
                      <span className={`task-status ${task.status}`}>
                        {task.status.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="task-meta">
                      <span className={`task-priority ${task.priority}`}>
                        {task.priority} priority
                      </span>
                      <span className="task-category">{task.category}</span>
                      {task.due_date && <span className="task-due-date">Due: {task.due_date}</span>}
                    </div>
                    {task.description && (
                      <div className="task-description">
                        {task.description.substring(0, 200)}...
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            <div className="pagination">
              <button disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
                Previous
              </button>
              <span>Page {page}</span>
              <button disabled={!taskData.has_more} onClick={() => setPage((p) => p + 1)}>
                Next
              </button>
            </div>
          </>
        )}
      </div>

      <div className="task-actions">
        <button>Create New Task</button>
        <p>
          <em>Note: Full task management features will be implemented in T8</em>
        </p>
      </div>
    </div>
  );
};

export default TaskList;
