// Login page component - placeholder for T6
import React, { useState } from 'react';
import { Navigate, Link } from 'react-router-dom';
import { useLoginMutation } from '@/services/authApi';
import { useAppSelector, useAppDispatch } from '@/hooks/redux';
import { loginStart, loginSuccess, loginFailure } from '@/store/authSlice';
import type { UserLogin } from '@/types/auth';

const Login: React.FC = () => {
  const [formData, setFormData] = useState<UserLogin>({
    username: '',
    password: '',
  });

  const { isAuthenticated, isLoading, error } = useAppSelector((state) => state.auth);
  const dispatch = useAppDispatch();
  const [login] = useLoginMutation();

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    dispatch(loginStart());

    try {
      const result = await login(formData).unwrap();

      // For now, we'll create a mock user since the login only returns tokens
      const mockUser = {
        id: 1,
        username: formData.username,
        email: `${formData.username}@example.com`,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      dispatch(
        loginSuccess({
          user: mockUser,
          tokens: result,
        })
      );
    } catch (err: unknown) {
      const error = err as { data?: { message?: string } };
      dispatch(loginFailure(error.data?.message || 'Login failed'));
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <h1>Email Helper</h1>
        <h2>Sign In</h2>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="username">Username:</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password:</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              disabled={isLoading}
            />
          </div>

          <button type="submit" disabled={isLoading} className="login-button">
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="login-links">
          <p>
            Don't have an account? <Link to="/register">Sign up</Link>
          </p>
          <p>
            <em>Note: Full authentication flow will be implemented in T6</em>
          </p>
        </div>

        <div className="demo-info">
          <h3>Demo Information</h3>
          <p>This is a development setup connecting to backend APIs (T1-T4).</p>
          <p>Authentication is functional but user management features are limited.</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
