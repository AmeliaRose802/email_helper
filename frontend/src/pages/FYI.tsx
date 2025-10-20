// FYI page - Shows FYI summaries from tasks
import React, { useMemo } from 'react';
import { useGetTasksQuery, useUpdateTaskMutation, useDeleteTaskMutation } from '@/services/taskApi';
import type { Task } from '@/types/task';

const FYI: React.FC = () => {
  const [updateTask] = useUpdateTaskMutation();
  const [deleteTask] = useDeleteTaskMutation();

  const {
    data: taskData,
    isLoading,
    error,
    refetch,
  } = useGetTasksQuery({ page: 1, per_page: 1000 });

  // Filter for FYI tasks
  const fyiTasks = useMemo(() => {
    if (!taskData?.tasks) return [];
    return taskData.tasks.filter(task => task.category === 'fyi');
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
    if (!window.confirm('Delete this FYI item?')) {
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
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>ℹ️</div>
          <h2 style={{ marginBottom: '8px', color: '#495057' }}>Loading FYI Emails</h2>
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
          <div>Error loading FYI emails</div>
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
        <h1 style={titleStyle}>ℹ️ FYI</h1>
        <div style={statsStyle}>
          {fyiTasks.length} FYI item{fyiTasks.length !== 1 ? 's' : ''}
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
        {fyiTasks.length === 0 ? (
          <div style={{ 
            padding: '48px 24px',
            textAlign: 'center',
            color: '#6c757d'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📭</div>
            <div style={{ fontSize: '18px', marginBottom: '8px' }}>No FYI items yet</div>
            <div style={{ fontSize: '14px' }}>Extract tasks from emails to see FYI summaries here</div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {fyiTasks.map((task) => {
              const isDone = task.status === 'done';
              return (
                <div
                  key={task.id}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    padding: '12px 16px',
                    backgroundColor: isDone ? '#f5f5f5' : '#fff',
                    border: `1px solid ${isDone ? '#d0d0d0' : '#e0e0e0'}`,
                    borderRadius: '6px',
                    opacity: isDone ? 0.6 : 1,
                  }}
                >
                  <input
                    type="checkbox"
                    checked={isDone}
                    onChange={() => handleToggleRead(task)}
                    style={{
                      width: '16px',
                      height: '16px',
                      marginRight: '12px',
                      marginTop: '2px',
                      cursor: 'pointer',
                      flexShrink: 0,
                    }}
                  />
                  <div style={{ flex: 1 }}>
                    {/* Show only summary text without extra email metadata */}
                    <div style={{
                      fontSize: '15px',
                      color: isDone ? '#6c757d' : '#00E6FF',
                      textDecoration: isDone ? 'line-through' : 'none',
                      lineHeight: '1.6',
                    }}>
                      {/* Extract bullet points if present, otherwise show full description */}
                      {task.description.split('\n').map((line, idx) => {
                        const trimmedLine = line.trim();
                        if (!trimmedLine) return null;
                        
                        // Check if line starts with bullet point or dash
                        const isBullet = trimmedLine.match(/^[•\-\*]\s/);
                        const cleanedLine = isBullet 
                          ? trimmedLine.replace(/^[•\-\*]\s/, '') 
                          : trimmedLine;
                        
                        // Skip common email header patterns
                        if (cleanedLine.match(/^(From:|To:|Subject:|Date:|Sent:)/i)) {
                          return null;
                        }
                        
                        return (
                          <div key={idx} style={{ 
                            marginBottom: '4px',
                            paddingLeft: isBullet ? '0' : '0'
                          }}>
                            {isBullet && <span style={{ marginRight: '8px' }}>•</span>}
                            {cleanedLine}
                          </div>
                        );
                      }).filter(Boolean)}
                    </div>
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
                      marginLeft: '12px',
                    }}
                    title="Delete"
                  >
                    🗑️
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default FYI;
