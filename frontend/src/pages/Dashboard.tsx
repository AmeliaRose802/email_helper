// Dashboard page component with modern animations and loading states
import React, { useState, useEffect } from 'react';
// import { useNavigate } from 'react-router-dom'; // Temporarily disabled for button testing
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
 * Dashboard component - Main dashboard view
 * Displays email and task statistics with modern, animated UI
 * Provides quick action buttons for common operations
 */
const Dashboard: React.FC = () => {
  // const navigate = useNavigate(); // Temporarily disabled for button testing
  const { data: emailStats, isLoading: emailStatsLoading, error: emailError } = useGetEmailStatsQuery();
  const { data: taskStats, isLoading: taskStatsLoading, error: taskError } = useGetTaskStatsQuery();

  const handleProcessEmails = (event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    console.log('🎯 Process emails button clicked!');
    console.trace('Click event trace');
    
    // Visual feedback
    if (event.currentTarget instanceof HTMLElement) {
      event.currentTarget.style.background = 'lime';
      setTimeout(() => {
        (event.currentTarget as HTMLElement).style.background = '';
      }, 2000);
    }
    
    alert('✅ SUCCESS! Process emails button is working! This will fetch new emails from Outlook.');
    // TODO: Implement email processing
  };

  const handleViewTasks = (event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    console.log('🎯 View tasks button clicked!');
    console.trace('Click event trace');
    
    // Visual feedback
    if (event.currentTarget instanceof HTMLElement) {
      event.currentTarget.style.background = 'lime';
      setTimeout(() => {
        (event.currentTarget as HTMLElement).style.background = '';
      }, 2000);
    }
    
    alert('✅ SUCCESS! View tasks button is working! Navigation will be implemented.');
    // navigate('/tasks');
  };

  const handleGenerateSummary = (event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    console.log('🎯 Generate summary button clicked!');
    console.trace('Click event trace');
    
    // Visual feedback
    if (event.currentTarget instanceof HTMLElement) {
      event.currentTarget.style.background = 'lime';
      setTimeout(() => {
        (event.currentTarget as HTMLElement).style.background = '';
      }, 2000);
    }
    
    alert('✅ SUCCESS! Generate summary button is working! This will create a summary of your emails.');
    // TODO: Implement summary generation
  };

  return (
    <div className="dashboard">
      <h1>📧 Email Helper Dashboard</h1>

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
        <button 
          type="button"
          className="action-button"
          onClick={handleGenerateSummary}
          style={{ pointerEvents: 'auto', zIndex: 100, WebkitAppRegion: 'no-drag' } as React.CSSProperties}
          data-testid="generate-summary-button"
        >
          📝 Generate Summary
        </button>
      </div>
    </div>
  );
};

export default Dashboard;
