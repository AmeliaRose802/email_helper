// Enhanced login page component for T6
import React from 'react';
import { Navigate, Link } from 'react-router-dom';
import { useAppSelector } from '@/hooks/redux';
import LoginForm from '@/components/LoginForm';

const Login: React.FC = () => {
  const { isAuthenticated, isLoading } = useAppSelector((state) => state.auth);

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  // Show loading state during auth initialization
  if (isLoading) {
    return (
      <div className="login-page">
        <div className="login-container">
          <div className="login-loading">
            <div className="spinner"></div>
            <p>Checking authentication...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="login-page">
      <div className="login-container">
        <h1>Email Helper</h1>
        <h2>Sign In</h2>

        <LoginForm />

        <div className="login-links">
          <p>
            Don't have an account? <Link to="/register">Sign up</Link>
          </p>
        </div>

        <div className="demo-info">
          <h3>Demo Information</h3>
          <p>This is a development setup connecting to backend APIs (T1-T4).</p>
          <p>Complete authentication flow with secure token storage implemented in T6.</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
