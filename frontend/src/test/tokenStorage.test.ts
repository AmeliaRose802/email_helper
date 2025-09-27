// Tests for token storage service
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { tokenStorage } from '@/services/tokenStorage';

// Mock JWT tokens for testing
const mockAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6OTk5OTk5OTk5OX0.signature';
const mockRefreshToken = 'refresh_token_here';
const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTAwfQ.signature';

describe('TokenStorage', () => {
  beforeEach(() => {
    // Clear storage before each test
    localStorage.clear();
    sessionStorage.clear();
  });

  describe('setTokens', () => {
    it('should store tokens in sessionStorage by default', () => {
      tokenStorage.setTokens(mockAccessToken, mockRefreshToken);
      
      expect(sessionStorage.getItem('email_helper_access_token')).toBe(mockAccessToken);
      expect(sessionStorage.getItem('email_helper_refresh_token')).toBe(mockRefreshToken);
      expect(localStorage.getItem('email_helper_access_token')).toBeNull();
    });

    it('should store tokens in localStorage when remember is true', () => {
      tokenStorage.setTokens(mockAccessToken, mockRefreshToken, true);
      
      expect(localStorage.getItem('email_helper_access_token')).toBe(mockAccessToken);
      expect(localStorage.getItem('email_helper_refresh_token')).toBe(mockRefreshToken);
      expect(sessionStorage.getItem('email_helper_access_token')).toBeNull();
    });

    it('should clear existing tokens before setting new ones', () => {
      // Set tokens in both storages
      localStorage.setItem('email_helper_access_token', 'old_token');
      sessionStorage.setItem('email_helper_access_token', 'old_token');
      
      tokenStorage.setTokens(mockAccessToken, mockRefreshToken, true);
      
      expect(localStorage.getItem('email_helper_access_token')).toBe(mockAccessToken);
      expect(sessionStorage.getItem('email_helper_access_token')).toBeNull();
    });
  });

  describe('getTokens', () => {
    it('should return null when no tokens are stored', () => {
      expect(tokenStorage.getTokens()).toBeNull();
    });

    it('should return tokens from localStorage', () => {
      localStorage.setItem('email_helper_access_token', mockAccessToken);
      localStorage.setItem('email_helper_refresh_token', mockRefreshToken);
      
      const tokens = tokenStorage.getTokens();
      expect(tokens).toEqual({
        accessToken: mockAccessToken,
        refreshToken: mockRefreshToken,
      });
    });

    it('should return tokens from sessionStorage', () => {
      sessionStorage.setItem('email_helper_access_token', mockAccessToken);
      sessionStorage.setItem('email_helper_refresh_token', mockRefreshToken);
      
      const tokens = tokenStorage.getTokens();
      expect(tokens).toEqual({
        accessToken: mockAccessToken,
        refreshToken: mockRefreshToken,
      });
    });

    it('should prefer localStorage over sessionStorage', () => {
      localStorage.setItem('email_helper_access_token', 'local_token');
      sessionStorage.setItem('email_helper_access_token', 'session_token');
      localStorage.setItem('email_helper_refresh_token', mockRefreshToken);
      sessionStorage.setItem('email_helper_refresh_token', mockRefreshToken);
      
      const tokens = tokenStorage.getTokens();
      expect(tokens?.accessToken).toBe('local_token');
    });

    it('should return null when only one token is present', () => {
      localStorage.setItem('email_helper_access_token', mockAccessToken);
      // Missing refresh token
      
      expect(tokenStorage.getTokens()).toBeNull();
    });
  });

  describe('clearTokens', () => {
    it('should clear tokens from both storages', () => {
      localStorage.setItem('email_helper_access_token', mockAccessToken);
      sessionStorage.setItem('email_helper_access_token', mockAccessToken);
      localStorage.setItem('email_helper_refresh_token', mockRefreshToken);
      sessionStorage.setItem('email_helper_refresh_token', mockRefreshToken);
      
      tokenStorage.clearTokens();
      
      expect(localStorage.getItem('email_helper_access_token')).toBeNull();
      expect(sessionStorage.getItem('email_helper_access_token')).toBeNull();
      expect(localStorage.getItem('email_helper_refresh_token')).toBeNull();
      expect(sessionStorage.getItem('email_helper_refresh_token')).toBeNull();
    });
  });

  describe('isTokenExpired', () => {
    beforeEach(() => {
      // Mock Date.now to return a fixed timestamp
      vi.spyOn(Date, 'now').mockReturnValue(1000000000);
    });

    it('should return false for valid token', () => {
      expect(tokenStorage.isTokenExpired(mockAccessToken)).toBe(false);
    });

    it('should return true for expired token', () => {
      expect(tokenStorage.isTokenExpired(expiredToken)).toBe(true);
    });

    it('should return true for malformed token', () => {
      expect(tokenStorage.isTokenExpired('invalid.token')).toBe(true);
      expect(tokenStorage.isTokenExpired('not-a-jwt')).toBe(true);
      expect(tokenStorage.isTokenExpired('')).toBe(true);
    });
  });

  describe('getStorageType', () => {
    it('should return localStorage when tokens are in localStorage', () => {
      localStorage.setItem('email_helper_access_token', mockAccessToken);
      expect(tokenStorage.getStorageType()).toBe('localStorage');
    });

    it('should return sessionStorage when tokens are in sessionStorage', () => {
      sessionStorage.setItem('email_helper_access_token', mockAccessToken);
      expect(tokenStorage.getStorageType()).toBe('sessionStorage');
    });

    it('should return null when no tokens are stored', () => {
      expect(tokenStorage.getStorageType()).toBeNull();
    });

    it('should prefer localStorage over sessionStorage', () => {
      localStorage.setItem('email_helper_access_token', mockAccessToken);
      sessionStorage.setItem('email_helper_access_token', mockAccessToken);
      expect(tokenStorage.getStorageType()).toBe('localStorage');
    });
  });
});