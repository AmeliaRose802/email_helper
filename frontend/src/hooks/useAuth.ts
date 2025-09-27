// Custom hook for authentication state and actions
import { useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from './redux';
import { useLogoutMutation } from '@/services/authApi';
import { logout, initializeAuth } from '@/store/authSlice';
import { getAuthErrorMessage } from '@/utils/authUtils';

export const useAuth = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const authState = useAppSelector((state) => state.auth);
  const [logoutMutation] = useLogoutMutation();

  // Initialize authentication on mount
  useEffect(() => {
    if (!authState.isAuthenticated && !authState.isLoading) {
      dispatch(initializeAuth());
    }
  }, [dispatch, authState.isAuthenticated, authState.isLoading]);

  // Logout with proper cleanup
  const handleLogout = useCallback(async () => {
    try {
      // Call logout API to invalidate server session
      await logoutMutation().unwrap();
    } catch (error) {
      console.warn('Logout API call failed:', error);
      // Continue with local logout even if API fails
    } finally {
      // Always clear local state and redirect
      dispatch(logout());
      navigate('/login', { replace: true });
    }
  }, [dispatch, navigate, logoutMutation]);

  // Check if user has specific permission
  const hasPermission = useCallback((_permission: string): boolean => {
    // For now, return true for authenticated users
    // This can be extended to check actual user permissions
    return authState.isAuthenticated;
  }, [authState.isAuthenticated]);

  // Get user-friendly error message
  const getErrorMessage = useCallback((error: unknown): string => {
    return getAuthErrorMessage(error);
  }, []);

  return {
    // Auth state
    user: authState.user,
    isAuthenticated: authState.isAuthenticated,
    isLoading: authState.isLoading,
    error: authState.error,
    token: authState.token,
    
    // Actions
    logout: handleLogout,
    hasPermission,
    getErrorMessage,
    
    // Helper methods
    initialize: () => dispatch(initializeAuth()),
    clearError: () => dispatch({ type: 'auth/clearError' }),
  };
};