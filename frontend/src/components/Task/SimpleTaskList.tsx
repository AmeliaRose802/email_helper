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
    
    if (diffDays < 0) return <span className="simple-task-due-date overdue">Overdue</span>;
    if (diffDays === 0) return <span className="simple-task-due-date today">Today</span>;
    if (diffDays === 1) return <span className="simple-task-due-date tomorrow">Tomorrow</span>;
    if (diffDays <= 7) return <span className="simple-task-due-date upcoming">In {diffDays} days</span>;
    
    return <span className="simple-task-due-date upcoming">{date.toLocaleDateString()}</span>;
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
    'Required Personal Actions': tasks.filter(t => t.category?.includes('required') && !t.category?.includes('team') && t.category !== 'newsletter' && t.category !== 'fyi'),
    'Team Actions': tasks.filter(t => t.category?.includes('team') && t.category !== 'newsletter' && t.category !== 'fyi'),
    'Optional Actions': tasks.filter(t => t.category?.includes('optional') && !t.category?.includes('event') && !t.category?.includes('job') && t.category !== 'newsletter' && t.category !== 'fyi'),
    'Job Listings': tasks.filter(t => t.category?.includes('job') && t.category !== 'newsletter' && t.category !== 'fyi'),
    'Events': tasks.filter(t => t.category?.includes('event') && t.category !== 'newsletter' && t.category !== 'fyi'),
    'Other': tasks.filter(t => !t.category || (!t.category.includes('required') && !t.category.includes('team') && !t.category.includes('optional') && !t.category.includes('job') && !t.category.includes('event') && t.category !== 'newsletter' && t.category !== 'fyi'))
  };

  const renderTaskGroup = (groupName: string, groupTasks: Task[]) => {
    if (groupTasks.length === 0) return null;

    const completedCount = groupTasks.filter(t => t.status === 'done').length;
    const totalCount = groupTasks.length;

    return (
      <div key={groupName} className="task-group">
        <h2 className="task-group-header">
          {groupName} ({completedCount}/{totalCount} complete)
        </h2>
        <div className="task-group-items">
          {groupTasks.map(task => {
            const links = extractLinks(task);
            const isDone = task.status === 'done';
            
            const taskItemClasses = [
              'simple-task-item',
              isDone && !recentlyCompleted.has(task.id) ? 'completed' : '',
              recentlyCompleted.has(task.id) ? 'recently-completed' : ''
            ].filter(Boolean).join(' ');

            return (
              <div key={task.id} className={taskItemClasses}>
                {/* Checkbox */}
                <input
                  type="checkbox"
                  checked={isDone}
                  onChange={() => handleToggleComplete(task)}
                  className="simple-task-checkbox"
                />
                
                {/* Task Content */}
                <div className="simple-task-content">
                  {/* Title Row */}
                  <div className="simple-task-title-row">
                    <span className="simple-task-icon">{getCategoryIcon(task.category)}</span>
                    <span className="simple-task-icon">{getPriorityEmoji(task.priority)}</span>
                    <span className={`simple-task-title ${isDone ? 'completed' : ''}`}>
                      {task.title}
                    </span>
                    {task.due_date && (
                      <>{formatDate(task.due_date)}</>
                    )}
                  </div>

                  {/* Description - Show AI summary or shortened version */}
                  {task.description && (
                    <div className="simple-task-description">
                      {/* Show only first paragraph or first 200 chars for readability */}
                      {(() => {
                        const firstParagraph = task.description.split('\n\n')[0];
                        const shortDescription = firstParagraph.length > 200 
                          ? firstParagraph.substring(0, 200) + '...'
                          : firstParagraph;
                        return shortDescription;
                      })()}
                    </div>
                  )}

                  {/* Links - Prominently Displayed */}
                  {links.length > 0 && (
                    <div className="simple-task-links">
                      <div className="simple-task-links-header">
                        🔗 Important Links:
                      </div>
                      {links.map((link, idx) => (
                        <div key={idx} className="simple-task-link">
                          <a
                            href={link}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {link}
                          </a>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tags */}
                  {task.tags && task.tags.length > 0 && (
                    <div className="simple-task-tags">
                      {task.tags.map((tag, idx) => (
                        <span key={idx} className="simple-task-tag">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Delete Button */}
                <button
                  onClick={() => handleDelete(task.id)}
                  className="simple-task-delete-btn"
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
    <div className="simple-task-list">
      {/* Celebration Animation */}
      {showCelebration && (
        <TaskCelebration onComplete={() => setShowCelebration(false)} />
      )}

      {/* Progress and Motivation Section */}
      {tasks.length > 0 && (
        <div className="simple-task-progress-section">
          <div className="simple-task-progress-header">
            <div className="simple-task-encouragement">
              {getEncouragementMessage()}
            </div>
            <div className="simple-task-count">
              {completedCount}/{totalCount}
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="simple-task-progress-bar-container">
            <div className="simple-task-progress-bar" style={{ width: `${completionPercentage}%` }}>
              {completionPercentage > 10 && `${completionPercentage}%`}
            </div>
            {completionPercentage <= 10 && (
              <div className="simple-task-progress-text-overlay">
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
        <div className="simple-task-empty-state">
          <div className="simple-task-empty-icon">📋</div>
          <div className="simple-task-empty-title">No tasks yet</div>
          <div className="simple-task-empty-description">
            Tasks will appear here after you extract them from emails
          </div>
        </div>
      )}
    </div>
  );
};
