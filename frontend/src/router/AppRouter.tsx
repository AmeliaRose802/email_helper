// React Router configuration
import React from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import Layout from '@/components/Layout';
import ProtectedRoute from '@/components/ProtectedRoute';
import Dashboard from '@/pages/Dashboard';
import EmailList from '@/pages/EmailList';
import EmailDetail from '@/pages/EmailDetail';
import TaskList from '@/pages/TaskList';
import Login from '@/pages/Login';
import Settings from '@/pages/Settings';

const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: 'emails',
        element: <EmailList />,
      },
      {
        path: 'emails/:id',
        element: <EmailDetail />,
      },
      {
        path: 'tasks',
        element: <TaskList />,
      },
      {
        path: 'tasks/:id',
        element: <div>Task Detail (T8)</div>, // Placeholder for T8
      },
      {
        path: 'settings',
        element: <Settings />,
      },
    ],
  },
  {
    path: '*',
    element: (
      <div
        style={{
          padding: '2rem',
          textAlign: 'center',
        }}
      >
        <h1>404 - Page Not Found</h1>
        <p>The page you're looking for doesn't exist.</p>
        <a href="/">Go back to Dashboard</a>
      </div>
    ),
  },
]);

const AppRouter: React.FC = () => {
  return <RouterProvider router={router} />;
};

export default AppRouter;
