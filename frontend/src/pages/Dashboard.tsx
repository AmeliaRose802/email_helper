// Dashboard page component
import React from 'react';
import { useGetEmailStatsQuery } from '@/services/emailApi';
import { useGetTaskStatsQuery } from '@/services/taskApi';

const Dashboard: React.FC = () => {
  const { data: emailStats, isLoading: emailStatsLoading } = useGetEmailStatsQuery();
  const { data: taskStats, isLoading: taskStatsLoading } = useGetTaskStatsQuery();

  return (
    <div className="dashboard">
      <h1>Email Helper Dashboard</h1>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Email Statistics</h3>
          {emailStatsLoading ? (
            <p>Loading email stats...</p>
          ) : emailStats ? (
            <div>
              <p>Total Emails: {emailStats.total_emails}</p>
              <p>Unread Emails: {emailStats.unread_emails}</p>
            </div>
          ) : (
            <p>Failed to load email statistics</p>
          )}
        </div>

        <div className="stat-card">
          <h3>Task Statistics</h3>
          {taskStatsLoading ? (
            <p>Loading task stats...</p>
          ) : taskStats ? (
            <div>
              <p>Total Tasks: {taskStats.total_tasks}</p>
              <p>Pending Tasks: {taskStats.pending_tasks}</p>
              <p>Completed Tasks: {taskStats.completed_tasks}</p>
              <p>Overdue Tasks: {taskStats.overdue_tasks}</p>
            </div>
          ) : (
            <p>Failed to load task statistics</p>
          )}
        </div>
      </div>

      <div className="quick-actions">
        <h3>Quick Actions</h3>
        <button>Process New Emails</button>
        <button>View Pending Tasks</button>
        <button>Generate Summary</button>
      </div>
    </div>
  );
};

export default Dashboard;
