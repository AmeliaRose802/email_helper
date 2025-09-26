// Basic app tests
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../App';

// Mock fetch to prevent real API calls in tests
beforeEach(() => {
  global.fetch = vi.fn(() =>
    Promise.resolve({
      ok: false,
      status: 404,
      json: () => Promise.resolve({}),
    } as Response)
  );
});

describe('App Component', () => {
  it('renders without crashing', () => {
    render(<App />);
    // App should render login form initially since no authentication
    expect(screen.getByText('Email Helper')).toBeInTheDocument();
  });

  it('shows login form when not authenticated', () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: 'Sign In' })).toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });
});
