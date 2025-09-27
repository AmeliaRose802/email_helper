// Complete Task Management with Kanban Board - T8 Implementation
import React, { useState, useMemo } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { useGetTasksQuery } from '@/services/taskApi';
import { TaskBoard } from '@/components/Task/TaskBoard';
import { TaskFilters } from '@/components/Task/TaskFilters';
import { ProgressTracker } from '@/components/Task/ProgressTracker';
import { TaskForm } from '@/components/Task/TaskForm';
import { filterTasks } from '@/utils/taskUtils';
import type { Task, TaskFilter } from '@/types/task';

const TaskList: React.FC = () => {
  const [filters, setFilters] = useState<TaskFilter>({});
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [viewMode, setViewMode] = useState<'board' | 'list'>('board');

  const {
    data: taskData,
    error,
    isLoading,
    refetch
  } = useGetTasksQuery({
    page: 1,
    per_page: 1000, // Get all tasks for Kanban board
  });

  // Filter tasks client-side for better UX
  const filteredTasks = useMemo(() => {
    if (!taskData?.tasks) return [];
    return filterTasks(taskData.tasks, filters);
  }, [taskData?.tasks, filters]);

  const handleFilterChange = (newFilters: TaskFilter) => {
    setFilters(newFilters);
  };

  const handleFilterReset = () => {
    setFilters({});
  };

  const handleEditTask = (task: Task) => {
    setEditingTask(task);
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
    <DndProvider backend={HTML5Backend}>
      <div className="task-list-container">
        <div className="task-list-header">
          <div className="header-title">
            <h1>Task Board</h1>
            <div className="task-count">
              {filteredTasks.length} of {taskData?.total_count || 0} tasks
            </div>
          </div>
          
          <div className="header-actions">
            <div className="view-toggle">
              <button
                className={viewMode === 'board' ? 'active' : ''}
                onClick={() => setViewMode('board')}
              >
                Board
              </button>
              <button
                className={viewMode === 'list' ? 'active' : ''}
                onClick={() => setViewMode('list')}
              >
                List
              </button>
            </div>
            
            <button 
              className="create-task-btn primary"
              onClick={() => setShowCreateForm(true)}
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
          ) : viewMode === 'board' ? (
            <TaskBoard 
              tasks={filteredTasks}
              onEditTask={handleEditTask}
              isLoading={isLoading}
              onRefresh={refetch}
            />
          ) : (
            <div className="task-list-view">
              <div className="task-items">
                {filteredTasks.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-icon">📋</div>
                    <h3>No tasks found</h3>
                    <p>
                      {Object.keys(filters).length > 0 
                        ? 'Try adjusting your filters or create a new task.'
                        : 'Get started by creating your first task.'
                      }
                    </p>
                    <button 
                      className="create-first-task-btn"
                      onClick={() => setShowCreateForm(true)}
                    >
                      Create Task
                    </button>
                  </div>
                ) : (
                  filteredTasks.map((task) => (
                    <div
                      key={task.id}
                      className={`task-item priority-${task.priority} status-${task.status}`}
                      onClick={() => handleEditTask(task)}
                    >
                      <div className="task-header">
                        <strong>{task.title}</strong>
                        <span className={`task-status ${task.status}`}>
                          {task.status.replace('-', ' ')}
                        </span>
                      </div>
                      <div className="task-meta">
                        <span className={`task-priority ${task.priority}`}>
                          {task.priority} priority
                        </span>
                        <span className="task-category">{task.category.replace('_', ' ')}</span>
                        {task.due_date && <span className="task-due-date">Due: {task.due_date}</span>}
                      </div>
                      {task.description && (
                        <div className="task-description">
                          {task.description.substring(0, 200)}
                          {task.description.length > 200 && '...'}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        <TaskForm
          task={editingTask}
          onClose={handleCloseForm}
          isOpen={showCreateForm || !!editingTask}
        />
      </div>
    </DndProvider>
  );
};

export default TaskList;
