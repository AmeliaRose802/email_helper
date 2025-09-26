// Settings page component
import React from 'react';
import { useHealthCheckQuery } from '@/services/api';
import { useAppSelector } from '@/hooks/redux';

const Settings: React.FC = () => {
  const { user } = useAppSelector((state) => state.auth);
  const { data: healthData, isLoading: healthLoading } = useHealthCheckQuery();

  return (
    <div className="settings">
      <h1>Settings</h1>

      <div className="settings-section">
        <h2>User Profile</h2>
        {user ? (
          <div className="user-info">
            <p>
              <strong>Username:</strong> {user.username}
            </p>
            <p>
              <strong>Email:</strong> {user.email}
            </p>
            <p>
              <strong>Account created:</strong> {new Date(user.created_at).toLocaleDateString()}
            </p>
          </div>
        ) : (
          <p>No user information available</p>
        )}
      </div>

      <div className="settings-section">
        <h2>System Status</h2>
        {healthLoading ? (
          <p>Checking system status...</p>
        ) : healthData ? (
          <div className="system-status">
            <p>
              <strong>Service:</strong> {healthData.service}
            </p>
            <p>
              <strong>Version:</strong> {healthData.version}
            </p>
            <p>
              <strong>Status:</strong> {healthData.status}
            </p>
            <p>
              <strong>Database:</strong> {healthData.database}
            </p>
            <p>
              <strong>Debug Mode:</strong> {healthData.debug ? 'Enabled' : 'Disabled'}
            </p>
          </div>
        ) : (
          <p>Unable to retrieve system status</p>
        )}
      </div>

      <div className="settings-section">
        <h2>API Configuration</h2>
        <div className="api-info">
          <p>
            <strong>Backend URL:</strong> http://localhost:8000
          </p>
          <p>
            <strong>Frontend URL:</strong> http://localhost:3000
          </p>
          <p>
            <strong>Available APIs:</strong>
          </p>
          <ul>
            <li>✅ Authentication API (T1): /auth/*</li>
            <li>✅ Email API (T2): /api/emails/*</li>
            <li>✅ AI Processing API (T3): /api/ai/*</li>
            <li>✅ Task Management API (T4): /api/tasks/*</li>
          </ul>
        </div>
      </div>

      <div className="settings-section">
        <h2>Preferences</h2>
        <div className="preferences">
          <label>
            <input type="checkbox" /> Enable notifications
          </label>
          <label>
            <input type="checkbox" /> Auto-process new emails
          </label>
          <label>
            <input type="checkbox" /> Dark mode
          </label>
          <p>
            <em>Note: Preference management will be expanded in future updates</em>
          </p>
        </div>
      </div>

      <div className="settings-section">
        <h2>About</h2>
        <div className="about-info">
          <p>Email Helper Web Application</p>
          <p>Version: 1.0.0 (T5 - React Web App Setup)</p>
          <p>Built with React, TypeScript, Redux Toolkit, and React Router</p>
          <p>Backend integration with FastAPI (T1-T4 complete)</p>
        </div>
      </div>
    </div>
  );
};

export default Settings;
