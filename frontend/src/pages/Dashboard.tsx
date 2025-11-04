// Dashboard page component - Email classification enabled
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetEmailStatsQuery } from '@/services/emailApi';
import { useGetTaskStatsQuery } from '@/services/taskApi';

/**
 * AnimatedCounter component for smooth number animations
 * Provides a visually engaging way to display statistics with count-up animation
 */
const AnimatedCounter: React.FC<{ end: number; duration?: number; suffix?: string }> = ({ 
  end, 
  duration = 1000,
  suffix = '' 
}) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let startTime: number;
    let animationFrame: number;

    const animate = (currentTime: number) => {
      if (!startTime) startTime = currentTime;
      const progress = Math.min((currentTime - startTime) / duration, 1);
      
      // Easing function for smooth animation
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      setCount(Math.floor(easeOutQuart * end));

      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate);
      }
    };

    animationFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrame);
  }, [end, duration]);

  return <span>{count}{suffix}</span>;
};

/**
 * SkeletonLoader component for loading states
 * Provides visual feedback while data is being fetched
 */
const SkeletonLoader: React.FC<{ height?: string; width?: string }> = ({ 
  height = '20px', 
  width = '100%' 
}) => (
  <div 
    className="skeleton" 
    style={{ height, width }}
  />
);

/**
 * StatCard component for displaying individual statistics
 * Features hover animations and loading states
 */
const StatCard: React.FC<{
  title: string;
  stats: Array<{ label: string; value: number; suffix?: string }>;
  isLoading: boolean;
  icon?: string;
}> = ({ title, stats, isLoading, icon = '📊' }) => {
  return (
    <div className="stat-card">
      <h3>
        <span className="stat-card__icon">{icon}</span>
        {title}
      </h3>
      {isLoading ? (
        <div className="stat-card__loading">
          <SkeletonLoader height="30px" width="60%" />
          <div className="stat-card__loading-row">
            <SkeletonLoader height="20px" width="80%" />
          </div>
          <div className="stat-card__loading-row">
            <SkeletonLoader height="20px" width="70%" />
          </div>
        </div>
      ) : (
        <div>
          {stats.map((stat, index) => (
            <p key={index} className={index === 0 ? 'stat-card__stat-primary' : 'stat-card__stat-secondary'}>
              <strong>{stat.label}:</strong>{' '}
              <AnimatedCounter end={stat.value} suffix={stat.suffix || ''} />
            </p>
          ))}
        </div>
      )}
    </div>
  );
};

/**
 * Dashboard component - MINIMAL VERSION FOR DEBUGGING
 * Most features commented out to isolate rendering issues
 */
const Dashboard: React.FC = () => {
  console.log('🟢 Dashboard component rendering...');
  const navigate = useNavigate();
  
  // State for email processing limit
  const [emailLimit, setEmailLimit] = useState(100);

  // API calls - directly enabled
  const { data: emailStats, isLoading: emailStatsLoading, error: emailError } = useGetEmailStatsQuery(emailLimit);
  const { data: taskStats, isLoading: taskStatsLoading, error: taskError } = useGetTaskStatsQuery();

  console.log('📊 API State:', { emailStatsLoading, taskStatsLoading, emailError, taskError });

  const handleProcessEmails = () => {
    console.log('🎯 Process emails button clicked - navigating to email list');
    navigate('/emails');
  };

  const handleViewTasks = () => {
    console.log('🎯 View tasks button clicked - navigating to tasks');
    navigate('/tasks');
  };

  return (
    <div className="dashboard">
      <h1>📧 Email Helper Dashboard</h1>

      {/* Email Processing Settings */}
      <div className="settings-section">
        <h3>⚙️ Processing Settings</h3>
        <div className="settings-section__controls">
          <label htmlFor="email-limit" className="settings-section__label">
            📊 Number of emails to process:
          </label>
          <input
            id="email-limit"
            type="number"
            min="10"
            max="1000"
            step="10"
            value={emailLimit}
            onChange={(e) => setEmailLimit(Math.max(10, Math.min(1000, parseInt(e.target.value) || 100)))}
            className="settings-section__input"
          />
          <span className="settings-section__hint">
            (10-1000 emails)
          </span>
        </div>
        <p className="settings-section__description">
          💡 Lower numbers = faster processing. Higher numbers = more complete statistics.
        </p>
      </div>

      <div className="stats-grid">
        <StatCard
          title="Email Statistics"
          icon="📧"
          isLoading={emailStatsLoading}
          stats={
            emailStats
              ? [
                  { label: 'Total Emails', value: emailStats.total_emails || 0 },
                  { label: 'Unread Emails', value: emailStats.unread_emails || 0 },
                ]
              : []
          }
        />

        <StatCard
          title="Task Statistics"
          icon="✅"
          isLoading={taskStatsLoading}
          stats={
            taskStats
              ? [
                  { label: 'Total Tasks', value: taskStats.total_tasks || 0 },
                  { label: 'Pending', value: taskStats.pending_tasks || 0 },
                  { label: 'Completed', value: taskStats.completed_tasks || 0 },
                  { label: 'Overdue', value: taskStats.overdue_tasks || 0 },
                ]
              : []
          }
        />
      </div>

      {/* Error handling */}
      {(emailError || taskError) && (
        <div className="error-message">
          ⚠️ Failed to load some statistics. Please try refreshing the page.
        </div>
      )}

      <div className="quick-actions">
        <h3>⚡ Quick Actions</h3>
        <button 
          type="button"
          className="action-button action-button--electron"
          onClick={handleProcessEmails}
          data-testid="process-emails-button"
        >
          📥 Process New Emails
        </button>
        
        <button 
          type="button"
          className="action-button action-button--electron"
          onClick={handleViewTasks}
          data-testid="view-tasks-button"
        >
          📋 View Pending Tasks
        </button>
      </div>
    </div>
  );
};

export default Dashboard;
