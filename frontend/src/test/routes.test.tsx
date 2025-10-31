// Router tests
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import { apiSlice } from '../services/api';
import authReducer from '../store/authSlice';
import EmailList from '../pages/EmailList';
import TaskList from '../pages/TaskList';
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
  it('renders EmailList component with loading state', () => {
    renderWithProviders(<EmailList />);
    // Should show loading initially due to API call
    expect(screen.getByText('Loading Emails')).toBeInTheDocument();
  });

  it('renders TaskList component with loading state', () => {
    renderWithProviders(<TaskList />);
    // Should show loading initially due to API call
    expect(screen.getByText('Loading tasks...')).toBeInTheDocument();
  });

  it('renders Settings component with loading state', () => {
    renderWithProviders(<Settings />);
    // Settings component shows loading state initially due to API call
    expect(screen.getByText('Loading settings...')).toBeInTheDocument();
  });
});
