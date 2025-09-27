// Basic app tests
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import App from '../App';

// Mock fetch to prevent real API calls in tests
beforeEach(() => {
  global.fetch = vi.fn(() =>
    Promise.resolve({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: 'Not authenticated' }),
    } as Response)
  );
});

describe('App Component', () => {
  it('renders without crashing', async () => {
    render(<App />);
    // App may show loading state initially, then login form
    await waitFor(() => {
      // Should show either loading state or login form
      const hasLoadingState = screen.queryByText('Checking authentication...');
      const hasLoginForm = screen.queryByText('Email Helper');
      expect(hasLoadingState || hasLoginForm).toBeTruthy();
    });
  });

  it('shows login form when not authenticated', async () => {
    render(<App />);
    // Wait for auth initialization to complete and show login form
    await waitFor(() => {
      expect(screen.getByText('Email Helper')).toBeInTheDocument();
    });
    expect(screen.getByRole('heading', { name: 'Sign In' })).toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });
});
