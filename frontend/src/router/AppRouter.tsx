// React Router configuration - Simple routes without auth for localhost
import React from 'react';
import { createHashRouter, RouterProvider } from 'react-router-dom';
import Dashboard from '@/pages/Dashboard';
import EmailList from '@/pages/EmailList';
import EmailDetail from '@/pages/EmailDetail';
import TaskList from '@/pages/TaskList';
import Newsletters from '@/pages/Newsletters';
import FYI from '@/pages/FYI';
import AccuracyDashboard from '@/pages/AccuracyDashboard';
import Settings from '@/pages/Settings';

console.log('✅ AppRouter.tsx loaded');

// Simple navigation component without auth
const SimpleNav: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="synthwave-container" style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <nav className="synthwave-nav">
        <a href="#/" className="synthwave-nav-link">
          📧 Emails
        </a>
        <a href="#/tasks" className="synthwave-nav-link">
          ✅ Tasks
        </a>
        <a href="#/newsletters" className="synthwave-nav-link">
          📰 Newsletters
        </a>
        <a href="#/fyi" className="synthwave-nav-link">
          ℹ️ FYI
        </a>
        <a href="#/accuracy" className="synthwave-nav-link">
          📊 Accuracy
        </a>
        <a href="#/settings" className="synthwave-nav-link">
          ⚙️ Settings
        </a>
      </nav>
      <div style={{ flex: 1, overflow: 'auto' }}>
        {children}
      </div>
    </div>
  );
};

const router = createHashRouter(
  [
    {
      path: '/',
      element: <SimpleNav><EmailList /></SimpleNav>,
      errorElement: <SimpleNav><div style={{ padding: '40px', textAlign: 'center' }}><h2>Page Error</h2><p>Something went wrong. <a href="#/">Go to Inbox</a></p></div></SimpleNav>,
    },
    {
      path: '/dashboard',
      element: <SimpleNav><Dashboard /></SimpleNav>,
    },
    {
      path: '/emails',
      element: <SimpleNav><EmailList /></SimpleNav>,
    },
    {
      path: '/emails/:id',
      element: <SimpleNav><EmailDetail /></SimpleNav>,
    },
    {
      path: '/tasks',
      element: <SimpleNav><TaskList /></SimpleNav>,
    },
    {
      path: '/newsletters',
      element: <SimpleNav><Newsletters /></SimpleNav>,
    },
    {
      path: '/fyi',
      element: <SimpleNav><FYI /></SimpleNav>,
    },
    {
      path: '/accuracy',
      element: <SimpleNav><AccuracyDashboard /></SimpleNav>,
    },
    {
      path: '/settings',
      element: <SimpleNav><Settings /></SimpleNav>,
    },
    {
      path: '*',
      element: <SimpleNav><div style={{ padding: '40px', textAlign: 'center' }}><h2>404 - Page Not Found</h2><p>The page you're looking for doesn't exist. <a href="#/">Go to Inbox</a></p></div></SimpleNav>,
    },
  ],
  {
    future: {
      v7_startTransition: true,
      v7_relativeSplatPath: true,
    },
  }
);

const AppRouter: React.FC = () => {
  try {
    return <RouterProvider router={router} />;
  } catch (error) {
    console.error('❌ Error in RouterProvider:', error);
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <h1 style={{ color: 'red' }}>Router Error</h1>
        <p>{error instanceof Error ? error.message : String(error)}</p>
      </div>
    );
  }
};

export default AppRouter;
