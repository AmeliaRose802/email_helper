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

  // Filter for newsletter tasks
  const newsletterTasks = useMemo(() => {
    if (!taskData?.tasks) return [];
    return taskData.tasks.filter(task => task.category === 'newsletter');
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

  const containerStyle = {
    display: 'flex',
    flexDirection: 'column' as const,
    height: '100%',
    backgroundColor: '#f8f9fa',
    padding: '24px',
  };

  const headerStyle = {
    marginBottom: '24px',
  };

  const titleStyle = {
    margin: 0,
    fontSize: '28px',
    fontWeight: '700',
    color: '#333',
  };

  const statsStyle = {
    fontSize: '14px',
    color: '#6c757d',
    marginTop: '8px',
  };

  if (isLoading) {
    return (
      <div style={containerStyle}>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>📰</div>
          <h2 style={{ marginBottom: '8px', color: '#495057' }}>Loading Newsletters</h2>
          <p style={{ color: '#6c757d' }}>Please wait...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={containerStyle}>
        <div style={{ textAlign: 'center', color: '#dc3545', padding: '40px' }}>
          <div style={{ fontSize: '24px', marginBottom: '8px' }}>⚠️</div>
          <div>Error loading newsletters</div>
          <button 
            onClick={refetch}
            style={{
              marginTop: '16px',
              padding: '8px 16px',
              backgroundColor: '#007acc',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <h1 style={titleStyle}>📰 Newsletters</h1>
        <div style={statsStyle}>
          {newsletterTasks.length} newsletter{newsletterTasks.length !== 1 ? 's' : ''}
        </div>
      </div>

      <div style={{ 
        flex: 1,
        backgroundColor: '#fff',
        borderRadius: '8px',
        border: '1px solid #e0e0e0',
        padding: '16px',
        overflowY: 'auto' as const,
      }}>
        {newsletterTasks.length === 0 ? (
          <div style={{ 
            padding: '48px 24px',
            textAlign: 'center',
            color: '#6c757d'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📭</div>
            <div style={{ fontSize: '18px', marginBottom: '8px' }}>No newsletters yet</div>
            <div style={{ fontSize: '14px' }}>Extract tasks from emails to see newsletter summaries here</div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {newsletterTasks.map((task) => {
              const isDone = task.status === 'done';
              return (
                <div
                  key={task.id}
                  style={{
                    padding: '16px',
                    backgroundColor: isDone ? '#f5f5f5' : '#fff',
                    border: `1px solid ${isDone ? '#d0d0d0' : '#e0e0e0'}`,
                    borderRadius: '8px',
                    opacity: isDone ? 0.6 : 1,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                    <input
                      type="checkbox"
                      checked={isDone}
                      onChange={() => handleToggleRead(task)}
                      style={{
                        width: '18px',
                        height: '18px',
                        marginTop: '4px',
                        cursor: 'pointer',
                        flexShrink: 0,
                      }}
                    />
                    <div style={{ flex: 1 }}>
                      <h3 style={{
                        margin: '0 0 12px 0',
                        fontSize: '18px',
                        fontWeight: '600',
                        color: isDone ? '#6c757d' : '#333',
                        textDecoration: isDone ? 'line-through' : 'none',
                      }}>
                        {task.title.replace('📰 ', '')}
                      </h3>
                      <div style={{
                        fontSize: '14px',
                        color: '#495057',
                        lineHeight: '1.6',
                        whiteSpace: 'pre-wrap',
                      }}>
                        {task.description}
                      </div>
                      {task.metadata?.key_points && Array.isArray(task.metadata.key_points) ? (
                        <div style={{ marginTop: '12px' }}>
                          <strong style={{ fontSize: '13px', color: '#007acc' }}>Key Points:</strong>
                          <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
                            {(task.metadata.key_points as unknown as string[]).map((point: string, idx: number) => (
                              <li key={idx} style={{ fontSize: '13px', marginBottom: '4px' }}>{String(point)}</li>
                            ))}
                          </ul>
                        </div>
                      ) : null}
                      {task.created_at && (
                        <div style={{
                          marginTop: '12px',
                          fontSize: '12px',
                          color: '#6c757d',
                        }}>
                          {new Date(task.created_at).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => handleDelete(task.id)}
                      style={{
                        padding: '4px 8px',
                        backgroundColor: 'transparent',
                        border: '1px solid #dc3545',
                        borderRadius: '4px',
                        color: '#dc3545',
                        cursor: 'pointer',
                        fontSize: '12px',
                        flexShrink: 0,
                      }}
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
