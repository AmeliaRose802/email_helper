// Enhanced protected route component for authentication
import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAppSelector, useAppDispatch } from '@/hooks/redux';
import { initializeAuth } from '@/store/authSlice';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading, user } = useAppSelector((state) => state.auth);
  const dispatch = useAppDispatch();
  const location = useLocation();

  // Check if we're in localhost mode with auth disabled
  const skipAuth = import.meta.env.VITE_SKIP_AUTH === 'true';
  const localhostMode = import.meta.env.VITE_LOCALHOST_MODE === 'true';

  // If auth is disabled in localhost mode, bypass authentication
  if (skipAuth || localhostMode) {
    return <>{children}</>;
  }

  // Initialize auth on mount if not already done
  useEffect(() => {
    if (!isAuthenticated && !isLoading && !user) {
      dispatch(initializeAuth());
    }
  }, [dispatch, isAuthenticated, isLoading, user]);

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="protected-route-loading" role="status" aria-label="Checking authentication">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Checking authentication...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
