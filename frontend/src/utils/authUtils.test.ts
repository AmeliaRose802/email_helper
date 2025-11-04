import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  getUserFromToken,
  getTokenExpiration,
  willTokenExpireSoon,
  isValidEmail,
  validatePassword,
  getAuthErrorMessage,
  getRedirectPath,
} from './authUtils';

describe('authUtils', () => {
  describe('getUserFromToken', () => {
    it('extracts user information from valid JWT token', () => {
      // JWT with payload: { user_id: "123", sub: "testuser" }
      const token = 'header.' + btoa(JSON.stringify({
        user_id: '123',
        sub: 'testuser',
        exp: Math.floor(Date.now() / 1000) + 3600,
      })) + '.signature';

      const user = getUserFromToken(token);
      expect(user).toEqual({
        id: '123',
        username: 'testuser',
        email: 'testuser@example.com',
      });
    });

    it('returns null for invalid token format', () => {
      const invalidToken = 'not.a.valid.jwt';
      const user = getUserFromToken(invalidToken);
      expect(user).toBeNull();
    });

    it('returns null for malformed JWT payload', () => {
      const malformedToken = 'header.not-base64.signature';
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const user = getUserFromToken(malformedToken);
      expect(user).toBeNull();
      consoleWarnSpy.mockRestore();
    });

    it('returns null for token with missing parts', () => {
      const incompleteToken = 'header.payload'; // Missing signature
      const user = getUserFromToken(incompleteToken);
      expect(user).toBeNull();
    });

    it('handles token with special characters in username', () => {
      const token = 'header.' + btoa(JSON.stringify({
        user_id: '456',
        sub: 'user.name+test',
      })) + '.signature';

      const user = getUserFromToken(token);
      expect(user?.username).toBe('user.name+test');
    });
  });

  describe('getTokenExpiration', () => {
    it('returns expiration date from valid token', () => {
      const expTimestamp = Math.floor(Date.now() / 1000) + 3600; // 1 hour from now
      const token = 'header.' + btoa(JSON.stringify({
        sub: 'testuser',
        exp: expTimestamp,
      })) + '.signature';

      const expiration = getTokenExpiration(token);
      expect(expiration).toBeInstanceOf(Date);
      expect(expiration?.getTime()).toBe(expTimestamp * 1000);
    });

    it('returns null for token without expiration', () => {
      const token = 'header.' + btoa(JSON.stringify({
        sub: 'testuser',
      })) + '.signature';

      const expiration = getTokenExpiration(token);
      expect(expiration).toBeNull();
    });

    it('returns null for invalid token', () => {
      const invalidToken = 'not.a.valid.jwt';
      const expiration = getTokenExpiration(invalidToken);
      expect(expiration).toBeNull();
    });

    it('returns null for malformed token payload', () => {
      const malformedToken = 'header.not-base64.signature';
      const expiration = getTokenExpiration(malformedToken);
      expect(expiration).toBeNull();
    });

    it('handles timestamp in milliseconds gracefully', () => {
      const expTimestamp = Math.floor(Date.now() / 1000) + 3600;
      const token = 'header.' + btoa(JSON.stringify({
        sub: 'testuser',
        exp: expTimestamp,
      })) + '.signature';

      const expiration = getTokenExpiration(token);
      // Verify it's a reasonable date (not too far in the past or future)
      const now = Date.now();
      expect(expiration!.getTime()).toBeGreaterThan(now);
      expect(expiration!.getTime()).toBeLessThan(now + 7200000); // Within 2 hours
    });
  });

  describe('willTokenExpireSoon', () => {
    beforeEach(() => {
      vi.setSystemTime(new Date('2024-01-15T12:00:00Z'));
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('returns true for token expiring within specified minutes', () => {
      // Token expires in 3 minutes
      const expTimestamp = Math.floor(new Date('2024-01-15T12:03:00Z').getTime() / 1000);
      const token = 'header.' + btoa(JSON.stringify({
        sub: 'testuser',
        exp: expTimestamp,
      })) + '.signature';

      expect(willTokenExpireSoon(token, 5)).toBe(true);
    });

    it('returns false for token expiring beyond specified minutes', () => {
      // Token expires in 10 minutes
      const expTimestamp = Math.floor(new Date('2024-01-15T12:10:00Z').getTime() / 1000);
      const token = 'header.' + btoa(JSON.stringify({
        sub: 'testuser',
        exp: expTimestamp,
      })) + '.signature';

      expect(willTokenExpireSoon(token, 5)).toBe(false);
    });

    it('returns true for expired token', () => {
      // Token expired 1 minute ago
      const expTimestamp = Math.floor(new Date('2024-01-15T11:59:00Z').getTime() / 1000);
      const token = 'header.' + btoa(JSON.stringify({
        sub: 'testuser',
        exp: expTimestamp,
      })) + '.signature';

      expect(willTokenExpireSoon(token, 5)).toBe(true);
    });

    it('returns true for token without expiration', () => {
      const token = 'header.' + btoa(JSON.stringify({
        sub: 'testuser',
      })) + '.signature';

      expect(willTokenExpireSoon(token, 5)).toBe(true);
    });

    it('uses default of 5 minutes when not specified', () => {
      // Token expires in 4 minutes
      const expTimestamp = Math.floor(new Date('2024-01-15T12:04:00Z').getTime() / 1000);
      const token = 'header.' + btoa(JSON.stringify({
        sub: 'testuser',
        exp: expTimestamp,
      })) + '.signature';

      expect(willTokenExpireSoon(token)).toBe(true);
    });

    it('returns true for invalid token', () => {
      const invalidToken = 'not.a.valid.jwt';
      expect(willTokenExpireSoon(invalidToken, 5)).toBe(true);
    });
  });

  describe('isValidEmail', () => {
    it('returns true for valid email addresses', () => {
      expect(isValidEmail('user@example.com')).toBe(true);
      expect(isValidEmail('test.user@example.com')).toBe(true);
      expect(isValidEmail('user+tag@example.co.uk')).toBe(true);
      expect(isValidEmail('user_name@example-domain.com')).toBe(true);
    });

    it('returns false for invalid email addresses', () => {
      expect(isValidEmail('notanemail')).toBe(false);
      expect(isValidEmail('missing@domain')).toBe(false);
      expect(isValidEmail('@example.com')).toBe(false);
      expect(isValidEmail('user@')).toBe(false);
      expect(isValidEmail('user @example.com')).toBe(false); // Space
      expect(isValidEmail('')).toBe(false);
    });

    it('returns false for emails with multiple @ symbols', () => {
      expect(isValidEmail('user@@example.com')).toBe(false);
      expect(isValidEmail('user@domain@example.com')).toBe(false);
    });

    it('returns false for emails without TLD', () => {
      expect(isValidEmail('user@localhost')).toBe(false);
    });

    it('handles edge cases', () => {
      expect(isValidEmail('a@b.c')).toBe(true); // Minimal valid email
      expect(isValidEmail('user@domain.')).toBe(false); // TLD missing
      expect(isValidEmail('.user@example.com')).toBe(true); // Leading dot (technically valid)
    });
  });

  describe('validatePassword', () => {
    it('accepts strong passwords', () => {
      const result = validatePassword('StrongPass123');
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('rejects passwords shorter than 8 characters', () => {
      const result = validatePassword('Short1A');
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Password must be at least 8 characters long');
    });

    it('rejects passwords without uppercase letters', () => {
      const result = validatePassword('lowercase123');
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Password must contain at least one uppercase letter');
    });

    it('rejects passwords without lowercase letters', () => {
      const result = validatePassword('UPPERCASE123');
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Password must contain at least one lowercase letter');
    });

    it('rejects passwords without numbers', () => {
      const result = validatePassword('NoNumbersHere');
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Password must contain at least one number');
    });

    it('returns multiple errors for weak passwords', () => {
      const result = validatePassword('weak');
      expect(result.isValid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(1);
      expect(result.errors).toContain('Password must be at least 8 characters long');
      expect(result.errors).toContain('Password must contain at least one uppercase letter');
      expect(result.errors).toContain('Password must contain at least one number');
    });

    it('accepts passwords with special characters', () => {
      const result = validatePassword('Strong!Pass123');
      expect(result.isValid).toBe(true);
    });

    it('handles empty password', () => {
      const result = validatePassword('');
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Password must be at least 8 characters long');
    });

    it('accepts exactly 8 character passwords meeting requirements', () => {
      const result = validatePassword('Pass1234');
      expect(result.isValid).toBe(true);
    });
  });

  describe('getAuthErrorMessage', () => {
    it('returns string errors directly', () => {
      const error = 'Authentication failed';
      expect(getAuthErrorMessage(error)).toBe('Authentication failed');
    });

    it('extracts message from API error object with message field', () => {
      const error = {
        data: {
          message: 'Invalid credentials',
        },
      };
      expect(getAuthErrorMessage(error)).toBe('Invalid credentials');
    });

    it('extracts detail from API error object with detail field', () => {
      const error = {
        data: {
          detail: 'User not found',
        },
      };
      expect(getAuthErrorMessage(error)).toBe('User not found');
    });

    it('prefers message over detail when both exist', () => {
      const error = {
        data: {
          message: 'Custom message',
          detail: 'Generic detail',
        },
      };
      expect(getAuthErrorMessage(error)).toBe('Custom message');
    });

    it('returns default message for unknown error types', () => {
      expect(getAuthErrorMessage(null)).toBe('An unexpected error occurred. Please try again.');
      expect(getAuthErrorMessage(undefined)).toBe('An unexpected error occurred. Please try again.');
      expect(getAuthErrorMessage({})).toBe('An unexpected error occurred. Please try again.');
      expect(getAuthErrorMessage(123)).toBe('An unexpected error occurred. Please try again.');
    });

    it('handles nested error objects', () => {
      const error = {
        response: {
          data: {
            message: 'Nested error message',
          },
        },
      };
      // Current implementation doesn't extract from nested response
      expect(getAuthErrorMessage(error)).toBe('An unexpected error occurred. Please try again.');
    });

    it('returns default for error with empty data', () => {
      const error = {
        data: {},
      };
      expect(getAuthErrorMessage(error)).toBe('An unexpected error occurred. Please try again.');
    });
  });

  describe('getRedirectPath', () => {
    it('extracts redirect path from location state', () => {
      const locationState = {
        from: {
          pathname: '/protected-route',
        },
      };
      expect(getRedirectPath(locationState, '/')).toBe('/protected-route');
    });

    it('returns default path when location state is undefined', () => {
      expect(getRedirectPath(undefined, '/dashboard')).toBe('/dashboard');
    });

    it('returns default path when from is missing', () => {
      const locationState = {};
      expect(getRedirectPath(locationState, '/home')).toBe('/home');
    });

    it('returns default path when pathname is missing', () => {
      const locationState = {
        from: {},
      };
      expect(getRedirectPath(locationState, '/default')).toBe('/default');
    });

    it('uses "/" as default when no default provided', () => {
      expect(getRedirectPath(null)).toBe('/');
    });

    it('handles complex nested paths', () => {
      const locationState = {
        from: {
          pathname: '/admin/users/123/edit',
        },
      };
      expect(getRedirectPath(locationState, '/')).toBe('/admin/users/123/edit');
    });

    it('returns default for non-object location state', () => {
      expect(getRedirectPath('string', '/default')).toBe('/default');
      expect(getRedirectPath(123, '/default')).toBe('/default');
      expect(getRedirectPath(null, '/default')).toBe('/default');
    });

    it('preserves query parameters in path', () => {
      const locationState = {
        from: {
          pathname: '/search?q=test&filter=active',
        },
      };
      expect(getRedirectPath(locationState, '/')).toBe('/search?q=test&filter=active');
    });
  });
});
