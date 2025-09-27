import React from 'react';
import { useDrop } from 'react-dnd';
import { TaskCard } from './TaskCard';
import type { Task } from '@/types/task';

export type TaskStatus = 'todo' | 'in-progress' | 'review' | 'done';

interface TaskColumnProps {
  column: {
    id: TaskStatus;
    title: string;
    color: string;
  };
  tasks: Task[];
  onTaskMove: (taskId: string, newStatus: TaskStatus) => void;
  onEditTask: (task: Task) => void;
  onDeleteTask?: (taskId: string) => void;
}

export const TaskColumn: React.FC<TaskColumnProps> = ({
  column,
  tasks,
  onTaskMove,
  onEditTask,
  onDeleteTask,
}) => {
  const [{ isOver, canDrop }, drop] = useDrop({
    accept: 'task',
    drop: (item: { id: string; currentStatus: TaskStatus }) => {
      if (item.currentStatus !== column.id) {
        onTaskMove(item.id, column.id);
      }
    },
    collect: (monitor) => ({
      isOver: monitor.isOver(),
      canDrop: monitor.canDrop(),
    }),
  });

  const getColumnClass = () => {
    let baseClass = `task-column ${column.color}`;
    if (isOver && canDrop) baseClass += ' drag-over';
    if (canDrop && !isOver) baseClass += ' can-drop';
    return baseClass;
  };

  return (
    <div className={getColumnClass()}>
      <div 
        ref={drop as unknown as React.Ref<HTMLDivElement>}
        className="task-column-content"
      >
        <div className="task-column-header">
          <h3 className="column-title">{column.title}</h3>
          <span className="task-count">{tasks.length}</span>
        </div>

        <div className="task-column-body">
          {tasks.length === 0 ? (
            <div className="task-column-empty">
              <div className="empty-state">
                <span className="empty-icon">📋</span>
                <p>No tasks</p>
                {isOver && canDrop && (
                  <p className="drop-hint">Drop task here</p>
                )}
              </div>
            </div>
          ) : (
            <div className="task-list">
              {tasks.map(task => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onEdit={() => onEditTask(task)}
                  onDelete={onDeleteTask ? () => onDeleteTask(task.id) : undefined}
                />
              ))}
              {isOver && canDrop && (
                <div className="drop-indicator">
                  <div className="drop-zone">Drop here</div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};