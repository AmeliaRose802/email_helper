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
      const hasEmailContent = screen.queryByText('Inbox') || screen.queryByText('Loading Emails');
      expect(hasEmailContent).toBeTruthy();
    });
  });
});
