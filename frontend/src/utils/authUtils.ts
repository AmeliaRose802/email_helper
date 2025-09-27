// Authentication utility functions
import { isAfter, addMinutes } from 'date-fns';
import type { User } from '@/types/auth';

/**
 * Extract user information from JWT token payload
 */
export const getUserFromToken = (token: string): Partial<User> | null => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    
    return {
      id: payload.user_id,
      username: payload.sub,
      email: `${payload.sub}@example.com`, // Fallback email
    };
  } catch (error) {
    console.warn('Failed to extract user from token:', error);
    return null;
  }
};

/**
 * Get token expiration date
 */
export const getTokenExpiration = (token: string): Date | null => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    if (payload.exp) {
      return new Date(payload.exp * 1000);
    }
    return null;
  } catch (error) {
    return null;
  }
};

/**
 * Check if token will expire soon (within specified minutes)
 */
export const willTokenExpireSoon = (token: string, withinMinutes: number = 5): boolean => {
  const expiration = getTokenExpiration(token);
  if (!expiration) return true;
  
  const soon = addMinutes(new Date(), withinMinutes);
  return isAfter(soon, expiration);
};

/**
 * Validate email format
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Validate password strength
 */
export const validatePassword = (password: string): { isValid: boolean; errors: string[] } => {
  const errors: string[] = [];
  
  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long');
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }
  
  if (!/\d/.test(password)) {
    errors.push('Password must contain at least one number');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
};

/**
 * Create user-friendly error messages from API errors
 */
export const getAuthErrorMessage = (error: unknown): string => {
  if (typeof error === 'string') {
    return error;
  }
  
  if (error && typeof error === 'object') {
    const apiError = error as { data?: { message?: string; detail?: string } };
    if (apiError.data?.message) {
      return apiError.data.message;
    }
    if (apiError.data?.detail) {
      return apiError.data.detail;
    }
  }
  
  return 'An unexpected error occurred. Please try again.';
};

/**
 * Get redirect path from location state or default
 */
export const getRedirectPath = (locationState: unknown, defaultPath: string = '/'): string => {
  if (locationState && typeof locationState === 'object') {
    const state = locationState as { from?: { pathname?: string } };
    return state.from?.pathname || defaultPath;
  }
  return defaultPath;
};