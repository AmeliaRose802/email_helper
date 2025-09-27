import React from 'react';
import { TaskColumn } from './TaskColumn';
import type { TaskStatus } from './TaskColumn';
import { useMoveTaskMutation, useDeleteTaskMutation } from '@/services/taskApi';
import type { Task } from '@/types/task';

interface TaskBoardProps {
  tasks: Task[];
  onEditTask: (task: Task) => void;
  isLoading?: boolean;
  onRefresh?: () => void;
}

const COLUMNS: Array<{ id: TaskStatus; title: string; color: string }> = [
  { id: 'todo', title: 'To Do', color: 'gray' },
  { id: 'in-progress', title: 'In Progress', color: 'blue' },
  { id: 'review', title: 'Review', color: 'yellow' },
  { id: 'done', title: 'Done', color: 'green' },
];

export const TaskBoard: React.FC<TaskBoardProps> = ({ 
  tasks, 
  onEditTask, 
  isLoading = false,
  onRefresh 
}) => {
  const [moveTask, { isLoading: isMoving }] = useMoveTaskMutation();
  const [deleteTask, { isLoading: isDeleting }] = useDeleteTaskMutation();

  const handleTaskMove = async (taskId: string, newStatus: TaskStatus) => {
    try {
      await moveTask({ id: taskId, status: newStatus }).unwrap();
    } catch (error) {
      console.error('Failed to move task:', error);
      // In a real app, you'd show a user-friendly error notification
      if (onRefresh) {
        onRefresh(); // Refresh to revert optimistic update
      }
    }
  };

  const handleTaskDelete = async (taskId: string) => {
    if (!window.confirm('Are you sure you want to delete this task?')) {
      return;
    }

    try {
      await deleteTask(taskId).unwrap();
    } catch (error) {
      console.error('Failed to delete task:', error);
      // Show error notification
    }
  };

  const getTasksForColumn = (status: TaskStatus) => {
    return tasks.filter(task => task.status === status);
  };

  if (isLoading) {
    return (
      <div className="task-board-loading">
        <div className="loading-spinner"></div>
        <p>Loading tasks...</p>
      </div>
    );
  }

  return (
    <div className="task-board">
      <div className="task-columns">
        {COLUMNS.map(column => (
          <TaskColumn
            key={column.id}
            column={column}
            tasks={getTasksForColumn(column.id)}
            onTaskMove={handleTaskMove}
            onEditTask={onEditTask}
            onDeleteTask={handleTaskDelete}
          />
        ))}
      </div>
      
      {(isMoving || isDeleting) && (
        <div className="task-board-overlay">
          <div className="loading-spinner"></div>
          <p>{isMoving ? 'Moving task...' : 'Deleting task...'}</p>
        </div>
      )}
    </div>
  );
};