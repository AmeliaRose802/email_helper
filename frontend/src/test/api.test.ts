// API integration tests
import { describe, it, expect, beforeAll } from 'vitest';
import { store } from '../store/store';
import { apiSlice } from '../services/api';

describe('API Integration', () => {
  beforeAll(() => {
    // Setup for API tests
  });

  it('should have api slice configured', () => {
    expect(apiSlice).toBeDefined();
    expect(apiSlice.reducerPath).toBe('api');
  });

  it('should have correct base query configuration', () => {
    // Test that the base query is configured correctly
    const state = store.getState();
    expect(state.api).toBeDefined();
  });

  it('should have auth slice configured', () => {
    const state = store.getState();
    expect(state.auth).toBeDefined();
    expect(state.auth.isAuthenticated).toBe(false); // Initial state
    expect(state.auth.user).toBe(null); // Initial state
  });

  // Note: Integration tests with actual backend will be added
  // when backend is running during testing
});
