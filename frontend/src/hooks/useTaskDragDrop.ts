import { useCallback } from 'react';
import { useMoveTaskMutation } from '@/services/taskApi';
import type { TaskStatus } from '@/components/Task/TaskColumn';

export const useTaskDragDrop = () => {
  const [moveTask, { isLoading: isMoving, error }] = useMoveTaskMutation();

  const handleTaskMove = useCallback(async (taskId: string, newStatus: TaskStatus) => {
    try {
      await moveTask({ id: taskId, status: newStatus }).unwrap();
      return { success: true };
    } catch (error) {
      console.error('Failed to move task:', error);
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Failed to move task' 
      };
    }
  }, [moveTask]);

  return {
    handleTaskMove,
    isMoving,
    error,
  };
};