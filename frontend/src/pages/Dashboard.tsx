// Dashboard page component - Email classification enabled
import React, { useState, useEffect } from 'react';
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
    style={{ height, width, display: 'inline-block' }}
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
        <span style={{ marginRight: '0.5rem' }}>{icon}</span>
        {title}
      </h3>
      {isLoading ? (
        <div style={{ padding: '1rem 0' }}>
          <SkeletonLoader height="30px" width="60%" />
          <div style={{ marginTop: '0.5rem' }}>
            <SkeletonLoader height="20px" width="80%" />
          </div>
          <div style={{ marginTop: '0.5rem' }}>
            <SkeletonLoader height="20px" width="70%" />
          </div>
        </div>
      ) : (
        <div>
          {stats.map((stat, index) => (
            <p key={index} style={{ fontSize: index === 0 ? '1.5rem' : '1rem' }}>
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
  
  // State for email processing limit
  const [emailLimit, setEmailLimit] = useState(100);

  // API calls - directly enabled
  const { data: emailStats, isLoading: emailStatsLoading, error: emailError } = useGetEmailStatsQuery(emailLimit);
  const { data: taskStats, isLoading: taskStatsLoading, error: taskError } = useGetTaskStatsQuery();

  console.log('📊 API State:', { emailStatsLoading, taskStatsLoading, emailError, taskError });

  const handleProcessEmails = () => {
    console.log('🎯 Process emails button clicked - navigating to email list');
    window.location.hash = '#/emails';
  };

  const handleViewTasks = () => {
    console.log('🎯 View tasks button clicked - navigating to tasks');
    window.location.hash = '#/tasks';
  };

  return (
    <div className="dashboard">
      <h1>📧 Email Helper Dashboard</h1>

      {/* Email Processing Settings */}
      <div className="settings-section" style={{
        background: 'var(--color-card-bg)',
        padding: '1rem',
        borderRadius: '8px',
        marginBottom: '1.5rem',
        border: '1px solid var(--color-border)'
      }}>
        <h3 style={{ marginTop: 0 }}>⚙️ Processing Settings</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <label htmlFor="email-limit" style={{ fontWeight: 500 }}>
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
            style={{
              padding: '0.5rem',
              borderRadius: '4px',
              border: '1px solid var(--color-border)',
              width: '100px',
              fontSize: '1rem'
            }}
          />
          <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>
            (10-1000 emails)
          </span>
        </div>
        <p style={{ 
          marginTop: '0.5rem', 
          marginBottom: 0, 
          fontSize: '0.85rem', 
          color: 'var(--color-text-secondary)' 
        }}>
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
        <div className="error-message" style={{ marginTop: '1rem' }}>
          ⚠️ Failed to load some statistics. Please try refreshing the page.
        </div>
      )}

      <div className="quick-actions">
        <h3>⚡ Quick Actions</h3>
        <button 
          type="button"
          className="action-button"
          onClick={handleProcessEmails}
          style={{ pointerEvents: 'auto', zIndex: 100, WebkitAppRegion: 'no-drag' } as React.CSSProperties}
          data-testid="process-emails-button"
        >
          📥 Process New Emails
        </button>
        
        <button 
          type="button"
          className="action-button"
          onClick={handleViewTasks}
          style={{ pointerEvents: 'auto', zIndex: 100, WebkitAppRegion: 'no-drag' } as React.CSSProperties}
          data-testid="view-tasks-button"
        >
          📋 View Pending Tasks
        </button>
      </div>
    </div>
  );
};

export default Dashboard;
