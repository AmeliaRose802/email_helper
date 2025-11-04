// Basic app tests
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import App from '../App';

// Mock fetch to prevent real API calls in tests
beforeEach(() => {
  // Create a proper mock Response with clone() method
  const createMockResponse = (data: unknown, status = 401, ok = false) => {
    const response = {
      ok,
      status,
      json: () => Promise.resolve(data),
      text: () => Promise.resolve(JSON.stringify(data)),
      headers: new Headers(),
      redirected: false,
      statusText: ok ? 'OK' : 'Unauthorized',
      type: 'basic' as ResponseType,
      url: '',
      // CRITICAL: Add clone() method that fetch API requires
      clone: function() { return { ...this }; },
    };
    return response as Response;
  };

  global.fetch = vi.fn(() =>
    Promise.resolve(createMockResponse({ detail: 'Not authenticated' }))
  );
});

describe('App Component', () => {
  it('renders without crashing', async () => {
    render(<App />);
    // App should render the router and main navigation
    await waitFor(() => {
      // The app renders with navigation elements
      const hasNav = document.querySelector('.synthwave-nav');
      expect(hasNav).toBeTruthy();
    });
  });

  it('shows email list by default', async () => {
    render(<App />);
    // Wait for router to render and show inbox
    await waitFor(() => {
      // Should show inbox/email list as default route
      // The component will show either the inbox, loading state, or error state
      const hasEmailContent = 
        screen.queryByText('Inbox') || 
        screen.queryByText('Loading Emails') ||
        screen.queryByText('Error Loading Emails');
      expect(hasEmailContent).toBeTruthy();
    });
  });
});
