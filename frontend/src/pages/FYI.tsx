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

  // Filter for FYI tasks - hide completed ones
  const fyiTasks = useMemo(() => {
    if (!taskData?.tasks) return [];
    return taskData.tasks.filter(task => task.category === 'fyi' && task.status !== 'done');
  }, [taskData?.tasks]);

  const handleToggleRead = async (task: Task) => {
    try {
      const newStatus = task.status === 'done' ? 'todo' : 'done';
      await updateTask({
        id: task.id,
        data: { status: newStatus }
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

  if (isLoading) {
    return (
      <div className="page-container">
        <div className="loading-container">
          <div className="loading-container__icon">ℹ️</div>
          <h2 className="loading-container__title">Loading FYI Emails</h2>
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
          <div>Error loading FYI emails</div>
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

  const handleDismissAll = async () => {
    if (!window.confirm(`Dismiss all ${fyiTasks.length} FYI items?`)) {
      return;
    }
    
    try {
      // Mark all FYI items as done
      await Promise.all(
        fyiTasks.map(task => 
          updateTask({
            id: task.id,
            data: { status: 'done' }
          }).unwrap()
        )
      );
      refetch();
    } catch (error) {
      console.error('Failed to dismiss all FYI items:', error);
      alert('Failed to dismiss all FYI items');
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">ℹ️ FYI</h1>
        <div className="page-stats">
          {fyiTasks.length} FYI item{fyiTasks.length !== 1 ? 's' : ''}
        </div>
        {fyiTasks.length > 0 && (
          <button
            onClick={handleDismissAll}
            className="synthwave-button-secondary dismiss-all-btn"
          >
            Dismiss All
          </button>
        )}
      </div>

      <div className="page-content">
        {fyiTasks.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state__icon">📭</div>
            <div className="empty-state__title">No FYI items yet</div>
            <div className="empty-state__description">
              FYI summaries will appear here after you process emails.
              <br /><br />
              <strong>To get started:</strong>
              <br />1. Go to the <a href="#/emails" style={{color: '#00f9ff', textDecoration: 'underline'}}>📧 Emails</a> tab
              <br />2. Wait for emails to be classified (happens automatically)
              <br />3. Click the <strong>"Approve"</strong> button to extract tasks
            </div>
          </div>
        ) : (
          <div className="flex-column gap-12">
            {fyiTasks.map((task) => {
              const isDone = task.status === 'done';
              return (
                <div
                  key={task.id}
                  className={`fyi-item ${isDone ? 'fyi-item--done' : ''}`}
                >
                  <input
                    type="checkbox"
                    checked={isDone}
                    onChange={() => handleToggleRead(task)}
                    className="fyi-item__checkbox"
                  />
                  <div className="fyi-item__content">
                    {/* Show only summary text without extra email metadata */}
                    <div className={`fyi-item__text ${isDone ? 'fyi-item__text--done' : ''}`}>
                      {/* Extract bullet points if present, otherwise show full description */}
                      {task.description?.split('\n').map((line, idx) => {
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
                          <div key={idx} className="fyi-item__line">
                            {isBullet && <span className="fyi-item__bullet">•</span>}
                            {cleanedLine}
                          </div>
                        );
                      }).filter(Boolean)}
                    </div>
                  </div>
                  <button
                    onClick={() => handleDelete(task.id)}
                    className="fyi-item__delete-btn"
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
