// Router tests
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import { apiSlice } from '../services/api';
import authReducer from '../store/authSlice';
import Dashboard from '../pages/Dashboard';
import EmailList from '../pages/EmailList';
import TaskList from '../pages/TaskList';
import Login from '../pages/Login';
import Settings from '../pages/Settings';

// Mock store for testing
const createMockStore = () =>
  configureStore({
    reducer: {
      [apiSlice.reducerPath]: apiSlice.reducer,
      auth: authReducer,
    },
    middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(apiSlice.middleware),
  });

const renderWithProviders = (component: React.ReactElement, initialEntries: string[] = ['/']) => {
  const mockStore = createMockStore();
  const router = createMemoryRouter([{ path: '/', element: component }], { initialEntries });

  return render(
    <Provider store={mockStore}>
      <RouterProvider router={router} />
    </Provider>
  );
};

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

describe('Route Components', () => {
  it('renders Dashboard component', () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByText('Email Helper Dashboard')).toBeInTheDocument();
  });

  it('renders EmailList component with loading state', () => {
    renderWithProviders(<EmailList />);
    // Should show loading initially due to API call
    expect(screen.getByText('Loading emails...')).toBeInTheDocument();
  });

  it('renders TaskList component with loading state', () => {
    renderWithProviders(<TaskList />);
    // Should show loading initially due to API call
    expect(screen.getByText('Loading tasks...')).toBeInTheDocument();
  });

  it('renders Login component', () => {
    renderWithProviders(<Login />);
    expect(screen.getByRole('heading', { name: 'Sign In' })).toBeInTheDocument();
  });

  it('renders Settings component', () => {
    renderWithProviders(<Settings />);
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });
});
