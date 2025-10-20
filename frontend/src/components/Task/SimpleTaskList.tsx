// Simple Task List - Just tasks with checkboxes - ADHD-Friendly Edition
import React, { useState } from 'react';
import { useUpdateTaskMutation, useDeleteTaskMutation } from '@/services/taskApi';
import type { Task } from '@/types/task';
import { TaskCelebration } from './TaskCelebration';

interface SimpleTaskListProps {
  tasks: Task[];
  onRefresh?: () => void;
}

const ENCOURAGEMENTS = [
  "🎉 Amazing work!",
  "⭐ You're crushing it!",
  "🔥 On fire today!",
  "💪 Keep it up!",
  "🚀 Unstoppable!",
  "✨ You're doing great!",
  "🎯 Nailed it!",
  "👏 Fantastic!",
  "🌟 Brilliant!"
];

export const SimpleTaskList: React.FC<SimpleTaskListProps> = ({ tasks, onRefresh }) => {
  const [updateTask] = useUpdateTaskMutation();
  const [deleteTask] = useDeleteTaskMutation();
  const [showCelebration, setShowCelebration] = useState(false);
  const [recentlyCompleted, setRecentlyCompleted] = useState<Set<string>>(new Set());

  // Calculate completion stats for motivation
  const completedCount = tasks.filter(t => t.status === 'done').length;
  const totalCount = tasks.length;
  const completionPercentage = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  const handleToggleComplete = async (task: Task) => {
    try {
      const newStatus = task.status === 'done' ? 'todo' : 'done';
      
      // Play completion sound if marking as done
      if (newStatus === 'done') {
        playCompletionSound();
        setShowCelebration(true);
        setRecentlyCompleted(prev => new Set([...prev, task.id]));
        
        // Remove from recently completed after animation
        setTimeout(() => {
          setRecentlyCompleted(prev => {
            const next = new Set(prev);
            next.delete(task.id);
            return next;
          });
        }, 2000);
      }
      
      await updateTask({
        id: task.id,
        data: { status: newStatus as any }
      }).unwrap();
      
      if (onRefresh) {
        onRefresh();
      }
    } catch (error) {
      console.error('Failed to update task:', error);
    }
  };

  const playCompletionSound = () => {
    // Create a simple beep sound using Web Audio API
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.value = 800;
      oscillator.type = 'sine';
      
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.1);
    } catch (e) {
      // Silent fail if audio not supported
      console.debug('Audio not available');
    }
  };

  const handleDelete = async (taskId: string) => {
    if (!window.confirm('Delete this task?')) {
      return;
    }
    
    try {
      await deleteTask(taskId).unwrap();
      if (onRefresh) {
        onRefresh();
      }
    } catch (error) {
      console.error('Failed to delete task:', error);
    }
  };

  const getPriorityEmoji = (priority: string) => {
    switch (priority) {
      case 'high':
      case 'urgent':
        return '🔴';
      case 'medium':
        return '🟡';
      case 'low':
        return '🟢';
      default:
        return '⚪';
    }
  };

  const getCategoryIcon = (category?: string) => {
    if (!category) return '📋';
    
    switch (category.toLowerCase()) {
      case 'required_action':
      case 'required_personal_action':
        return '⚡';
      case 'team_action':
        return '👥';
      case 'optional_action':
        return '💡';
      case 'job_listing':
        return '💼';
      case 'optional_event':
        return '🎪';
      case 'newsletter':
        return '📰';
      case 'fyi':
        return '📋';
      default:
        return '📝';
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return null;
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) return <span style={{ color: '#dc3545', fontWeight: 'bold' }}>Overdue</span>;
    if (diffDays === 0) return <span style={{ color: '#ffc107', fontWeight: 'bold' }}>Today</span>;
    if (diffDays === 1) return <span style={{ color: '#17a2b8' }}>Tomorrow</span>;
    if (diffDays <= 7) return <span style={{ color: '#6c757d' }}>In {diffDays} days</span>;
    
    return <span style={{ color: '#6c757d' }}>{date.toLocaleDateString()}</span>;
  };

  const extractLinks = (task: Task): string[] => {
    const links: string[] = [];
    
    // Check metadata
    if (task.metadata?.links && Array.isArray(task.metadata.links)) {
      links.push(...task.metadata.links);
    }
    
    // Extract from description
    if (task.description) {
      const urlRegex = /(https?:\/\/[^\s]+)/g;
      const matches = task.description.match(urlRegex);
      if (matches) {
        links.push(...matches);
      }
    }
    
    return [...new Set(links)]; // Remove duplicates
  };

  const groupedTasks = {
    'Required Personal Actions': tasks.filter(t => t.category?.includes('required') && !t.category?.includes('team')),
    'Team Actions': tasks.filter(t => t.category?.includes('team')),
    'Optional Actions': tasks.filter(t => t.category?.includes('optional') && !t.category?.includes('event') && !t.category?.includes('job')),
    'Job Listings': tasks.filter(t => t.category?.includes('job')),
    'Events': tasks.filter(t => t.category?.includes('event')),
    'Newsletters': tasks.filter(t => t.category === 'newsletter'),
    'FYI': tasks.filter(t => t.category === 'fyi'),
    'Other': tasks.filter(t => !t.category || (!t.category.includes('required') && !t.category.includes('team') && !t.category.includes('optional') && !t.category.includes('job') && !t.category.includes('event') && t.category !== 'newsletter' && t.category !== 'fyi'))
  };

  const renderTaskGroup = (groupName: string, groupTasks: Task[]) => {
    if (groupTasks.length === 0) return null;

    const completedCount = groupTasks.filter(t => t.status === 'done').length;
    const totalCount = groupTasks.length;

    return (
      <div key={groupName} style={{ marginBottom: '32px' }}>
        <h2 style={{ 
          fontSize: '20px', 
          fontWeight: 'bold', 
          marginBottom: '16px',
          color: '#333',
          borderBottom: '2px solid #007acc',
          paddingBottom: '8px'
        }}>
          {groupName} ({completedCount}/{totalCount} complete)
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {groupTasks.map(task => {
            const links = extractLinks(task);
            const isDone = task.status === 'done';
            
            return (
              <div
                key={task.id}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  padding: '12px 16px',
                  backgroundColor: recentlyCompleted.has(task.id) 
                    ? '#d4edda' 
                    : isDone ? '#f0f0f0' : '#fff',
                  border: recentlyCompleted.has(task.id)
                    ? '2px solid #28a745'
                    : `1px solid ${isDone ? '#d0d0d0' : '#e0e0e0'}`,
                  borderRadius: '6px',
                  transition: 'all 0.3s ease',
                  opacity: isDone && !recentlyCompleted.has(task.id) ? 0.7 : 1,
                  boxShadow: recentlyCompleted.has(task.id)
                    ? '0 0 20px rgba(40, 167, 69, 0.5)'
                    : isDone ? 'none' : '0 1px 3px rgba(0,0,0,0.1)',
                  transform: recentlyCompleted.has(task.id) ? 'scale(1.02)' : 'scale(1)'
                }}
              >
                {/* Checkbox */}
                <input
                  type="checkbox"
                  checked={isDone}
                  onChange={() => handleToggleComplete(task)}
                  style={{
                    width: '20px',
                    height: '20px',
                    marginRight: '12px',
                    marginTop: '2px',
                    cursor: 'pointer',
                    flexShrink: 0
                  }}
                />
                
                {/* Task Content */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  {/* Title Row */}
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '8px',
                    marginBottom: '4px',
                    flexWrap: 'wrap'
                  }}>
                    <span style={{ fontSize: '16px' }}>{getCategoryIcon(task.category)}</span>
                    <span style={{ fontSize: '16px' }}>{getPriorityEmoji(task.priority)}</span>
                    <span
                      style={{
                        fontSize: '15px',
                        fontWeight: '500',
                        color: isDone ? '#6c757d' : '#333',
                        textDecoration: isDone ? 'line-through' : 'none',
                        flex: 1,
                        wordBreak: 'break-word'
                      }}
                    >
                      {task.title}
                    </span>
                    {task.due_date && (
                      <span style={{ fontSize: '13px', whiteSpace: 'nowrap' }}>
                        {formatDate(task.due_date)}
                      </span>
                    )}
                  </div>

                  {/* Description */}
                  {task.description && (
                    <div
                      style={{
                        fontSize: '13px',
                        color: '#6c757d',
                        marginBottom: '8px',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word'
                      }}
                    >
                      {task.description}
                    </div>
                  )}

                  {/* Links - Prominently Displayed */}
                  {links.length > 0 && (
                    <div style={{ 
                      marginTop: '8px',
                      padding: '8px 12px',
                      backgroundColor: '#e7f3ff',
                      border: '1px solid #b3d9ff',
                      borderRadius: '4px'
                    }}>
                      <div style={{ 
                        fontSize: '12px', 
                        fontWeight: 'bold', 
                        color: '#0066cc',
                        marginBottom: '4px'
                      }}>
                        🔗 Important Links:
                      </div>
                      {links.map((link, idx) => (
                        <div key={idx} style={{ marginBottom: '2px' }}>
                          <a
                            href={link}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              fontSize: '13px',
                              color: '#0066cc',
                              textDecoration: 'underline',
                              wordBreak: 'break-all'
                            }}
                          >
                            {link}
                          </a>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tags */}
                  {task.tags && task.tags.length > 0 && (
                    <div style={{ 
                      display: 'flex', 
                      gap: '4px', 
                      marginTop: '8px',
                      flexWrap: 'wrap'
                    }}>
                      {task.tags.map((tag, idx) => (
                        <span
                          key={idx}
                          style={{
                            fontSize: '11px',
                            padding: '2px 8px',
                            backgroundColor: '#e0e0e0',
                            borderRadius: '12px',
                            color: '#555'
                          }}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Delete Button */}
                <button
                  onClick={() => handleDelete(task.id)}
                  style={{
                    marginLeft: '12px',
                    padding: '4px 8px',
                    backgroundColor: 'transparent',
                    border: '1px solid #dc3545',
                    borderRadius: '4px',
                    color: '#dc3545',
                    cursor: 'pointer',
                    fontSize: '12px',
                    flexShrink: 0
                  }}
                  title="Delete task"
                >
                  🗑️
                </button>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const getEncouragementMessage = () => {
    if (completionPercentage === 100 && totalCount > 0) {
      return "🏆 All done! You're a superstar!";
    }
    if (completionPercentage >= 75) {
      return ENCOURAGEMENTS[Math.floor(Math.random() * ENCOURAGEMENTS.length)];
    }
    if (completionPercentage >= 50) {
      return "💪 You're making great progress!";
    }
    if (completionPercentage >= 25) {
      return "🌟 Keep going, you've got this!";
    }
    return "🚀 Let's get started!";
  };

  return (
    <div style={{ padding: '8px' }}>
      {/* Celebration Animation */}
      {showCelebration && (
        <TaskCelebration onComplete={() => setShowCelebration(false)} />
      )}

      {/* Progress and Motivation Section */}
      {tasks.length > 0 && (
        <div style={{
          marginBottom: '24px',
          padding: '20px',
          backgroundColor: '#f0f8ff',
          borderRadius: '12px',
          border: '2px solid #007acc',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '12px'
          }}>
            <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#007acc' }}>
              {getEncouragementMessage()}
            </div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#28a745' }}>
              {completedCount}/{totalCount}
            </div>
          </div>
          
          {/* Progress Bar */}
          <div style={{
            width: '100%',
            height: '24px',
            backgroundColor: '#e0e0e0',
            borderRadius: '12px',
            overflow: 'hidden',
            position: 'relative'
          }}>
            <div style={{
              width: `${completionPercentage}%`,
              height: '100%',
              background: 'linear-gradient(90deg, #28a745 0%, #20c997 100%)',
              transition: 'width 0.5s ease',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontWeight: 'bold',
              fontSize: '13px'
            }}>
              {completionPercentage > 10 && `${completionPercentage}%`}
            </div>
            {completionPercentage <= 10 && (
              <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                fontSize: '13px',
                fontWeight: 'bold',
                color: '#6c757d'
              }}>
                {completionPercentage}%
              </div>
            )}
          </div>
        </div>
      )}

      {Object.entries(groupedTasks).map(([groupName, groupTasks]) => 
        renderTaskGroup(groupName, groupTasks)
      )}
      
      {tasks.length === 0 && (
        <div style={{
          textAlign: 'center',
          padding: '60px 20px',
          color: '#6c757d'
        }}>
          <div style={{ fontSize: '64px', marginBottom: '16px' }}>📋</div>
          <div style={{ fontSize: '18px' }}>No tasks yet</div>
          <div style={{ fontSize: '14px', marginTop: '8px' }}>
            Tasks will appear here after you extract them from emails
          </div>
        </div>
      )}
    </div>
  );
};
