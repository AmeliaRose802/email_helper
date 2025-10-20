// Newsletters page - Shows newsletter summaries from tasks
import React, { useMemo } from 'react';
import { useGetTasksQuery, useUpdateTaskMutation, useDeleteTaskMutation } from '@/services/taskApi';
import type { Task } from '@/types/task';

const Newsletters: React.FC = () => {
  const [updateTask] = useUpdateTaskMutation();
  const [deleteTask] = useDeleteTaskMutation();

  const {
    data: taskData,
    isLoading,
    error,
    refetch,
  } = useGetTasksQuery({ page: 1, per_page: 1000 });

  // Filter for newsletter tasks - hide completed ones
  const newsletterTasks = useMemo(() => {
    if (!taskData?.tasks) return [];
    return taskData.tasks.filter(task => task.category === 'newsletter' && task.status !== 'done');
  }, [taskData?.tasks]);

  const handleToggleRead = async (task: Task) => {
    try {
      const newStatus = task.status === 'done' ? 'todo' : 'done';
      await updateTask({
        id: task.id,
        data: { status: newStatus as any }
      }).unwrap();
      refetch();
    } catch (error) {
      console.error('Failed to update task:', error);
    }
  };

  const handleDelete = async (taskId: string) => {
    if (!window.confirm('Delete this newsletter summary?')) {
      return;
    }
    
    try {
      await deleteTask(taskId).unwrap();
      refetch();
    } catch (error) {
      console.error('Failed to delete task:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="page-container">
        <div className="loading-container">
          <div className="loading-container__icon">📰</div>
          <h2 className="loading-container__title">Loading Newsletters</h2>
          <p className="loading-container__message">Please wait...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="error-container">
          <div className="text-2xl mb-sm">⚠️</div>
          <div>Error loading newsletters</div>
          <button 
            onClick={refetch}
            className="synthwave-button mt-md"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">📰 Newsletters</h1>
        <div className="page-stats">
          {newsletterTasks.length} newsletter{newsletterTasks.length !== 1 ? 's' : ''}
        </div>
      </div>

      <div className="page-content">
        {newsletterTasks.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state__icon">📭</div>
            <div className="empty-state__title">No newsletters yet</div>
            <div className="empty-state__description">Extract tasks from emails to see newsletter summaries here</div>
          </div>
        ) : (
          <div className="flex-column gap-16">
            {newsletterTasks.map((task) => {
              const isDone = task.status === 'done';
              return (
                <div
                  key={task.id}
                  className={`newsletter-item ${isDone ? 'newsletter-item--done' : ''}`}
                >
                  <div className="newsletter-item__header">
                    <input
                      type="checkbox"
                      checked={isDone}
                      onChange={() => handleToggleRead(task)}
                      className="newsletter-item__checkbox"
                    />
                    <div className="newsletter-item__content">
                      {/* Show only summary without extra noise - clean newsletter format */}
                      <div className="newsletter-item__summary">
                        {/* Clean up description - remove email headers and format paragraphs */}
                        {task.description?.split('\n\n').map((paragraph, idx) => {
                          const trimmedPara = paragraph.trim();
                          
                          // Skip email headers and metadata
                          if (trimmedPara.match(/^(From:|To:|Subject:|Date:|Sent:|Email from)/i)) {
                            return null;
                          }
                          
                          // Skip empty paragraphs
                          if (!trimmedPara) return null;
                          
                          return (
                            <p key={idx} className={`newsletter-item__summary ${isDone ? 'newsletter-item__summary--done' : ''}`} style={{
                              margin: idx === 0 ? '0 0 12px 0' : '12px 0'
                            }}>
                              {trimmedPara}
                            </p>
                          );
                        }).filter(Boolean)}
                      </div>
                      
                      {/* Show key points if available */}
                      {task.metadata?.key_points && Array.isArray(task.metadata.key_points) && (task.metadata.key_points as unknown as string[]).length > 0 ? (
                        <div className="newsletter-item__highlights">
                          <strong className="newsletter-item__highlights-title">
                            Key Takeaways:
                          </strong>
                          <ul className="newsletter-item__highlights-list">
                            {(task.metadata.key_points as unknown as string[]).map((point: string, idx: number) => (
                              <li key={idx} className="newsletter-item__highlight">
                                {String(point)}
                              </li>
                            ))}
                          </ul>
                        </div>
                      ) : null}
                    </div>
                    <button
                      onClick={() => handleDelete(task.id)}
                      className="newsletter-item__delete-btn"
                      title="Delete"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default Newsletters;
