// Complete Task Management - Simplified List View
import React, { useState, useMemo } from 'react';
import { useGetTasksQuery } from '@/services/taskApi';
import { SimpleTaskList } from '@/components/Task/SimpleTaskList';
import { TaskFilters } from '@/components/Task/TaskFilters';
import { ProgressTracker } from '@/components/Task/ProgressTracker';
import { TaskForm } from '@/components/Task/TaskForm';
import { filterTasks } from '@/utils/taskUtils';
import type { Task, TaskFilter } from '@/types/task';

const TaskList: React.FC = () => {
  const [filters, setFilters] = useState<TaskFilter>({});
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);

  const {
    data: taskData,
    error,
    isLoading,
    refetch
  } = useGetTasksQuery({
    page: 1,
    per_page: 1000, // Get all tasks for Kanban board
  });

  // Filter tasks client-side for better UX - exclude newsletters and FYI (they have their own tabs)
  const filteredTasks = useMemo(() => {
    if (!taskData?.tasks) return [];
    const tasksWithoutNewslettersAndFYI = taskData.tasks.filter(
      task => task.category !== 'newsletter' && task.category !== 'fyi'
    );
    return filterTasks(tasksWithoutNewslettersAndFYI, filters);
  }, [taskData?.tasks, filters]);

  const handleFilterChange = (newFilters: TaskFilter) => {
    setFilters(newFilters);
  };

  const handleFilterReset = () => {
    setFilters({});
  };

  const handleCloseForm = () => {
    setShowCreateForm(false);
    setEditingTask(null);
  };

  if (error) {
    return (
      <div className="task-list-error">
        <h2>Error loading tasks</h2>
        <p>Unable to load your tasks. Please try again.</p>
        <button onClick={() => refetch()} className="retry-btn">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="task-list-container">
      <div className="task-list-header">
        <div className="header-title">
          <h1>Task Board</h1>
          <div className="task-count">
            {filteredTasks.length} of {taskData?.total_count || 0} tasks
          </div>
        </div>
        
        <div className="header-actions">
          <button 
            className="create-task-btn primary"
            onClick={() => setShowCreateForm(true)}
            data-testid="create-task-button"
          >
            + New Task
          </button>
        </div>
      </div>

      <div className="task-progress-section">
        <ProgressTracker tasks={filteredTasks} />
      </div>

      <div className="task-filters-section">
        <TaskFilters 
          filters={filters}
          onChange={handleFilterChange}
          onReset={handleFilterReset}
        />
      </div>

      <div className="task-content-section">
        {isLoading ? (
          <div className="task-list-loading">
            <div className="loading-spinner"></div>
            <p>Loading tasks...</p>
          </div>
        ) : (
          <SimpleTaskList 
            tasks={filteredTasks}
            onRefresh={refetch}
          />
        )}
      </div>

      <TaskForm
        task={editingTask}
        onClose={handleCloseForm}
        isOpen={showCreateForm || !!editingTask}
      />
    </div>
  );
};

export default TaskList;
