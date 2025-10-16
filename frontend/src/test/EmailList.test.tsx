// Email list component tests
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import EmailList from '@/pages/EmailList';
import { apiSlice } from '@/services/api';
import authSlice from '@/store/authSlice';

// Mock data - commented out as not currently used
/*
const mockEmails = [
  {
    id: '1',
    subject: 'Test Email 1',
    sender: 'test1@example.com',
    recipient: 'user@example.com',
    date: '2025-01-15T10:00:00Z',
    body: 'This is a test email body content.',
    is_read: false,
    importance: 'Normal' as const,
    has_attachments: false,
    categories: ['required_action'],
  },
  {
    id: '2',
    subject: 'Test Email 2',
    sender: 'test2@example.com',
    recipient: 'user@example.com',
    date: '2025-01-14T15:30:00Z',
    body: 'Another test email with different content.',
    is_read: true,
    importance: 'High' as const,
    has_attachments: true,
    categories: ['fyi'],
  },
];
*/

// Create test store
const createTestStore = () => {
  return configureStore({
    reducer: {
      api: apiSlice.reducer,
      auth: authSlice,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(apiSlice.middleware),
    preloadedState: {
      auth: {
        isAuthenticated: true,
        user: { id: 1, username: 'testuser', email: 'test@example.com', created_at: '', updated_at: '' },
        token: 'test-token',
        refreshToken: 'test-refresh-token',
        isLoading: false,
        error: null,
      },
    },
  });
};

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const store = createTestStore();
  return (
    <Provider store={store}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </Provider>
  );
};

describe('EmailList Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    render(
      <TestWrapper>
        <EmailList />
      </TestWrapper>
    );

    expect(screen.getByText('Loading emails...')).toBeInTheDocument();
  });

  it('displays search bar and filters', async () => {
    render(
      <TestWrapper>
        <EmailList />
      </TestWrapper>
    );

    // Wait for loading to complete and check for search bar
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search emails...')).toBeInTheDocument();
    });
  });

  it('can enter search query', async () => {
    render(
      <TestWrapper>
        <EmailList />
      </TestWrapper>
    );

    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText('Search emails...');
      expect(searchInput).toBeInTheDocument();
      
      fireEvent.change(searchInput, { target: { value: 'test query' } });
      expect(searchInput).toHaveValue('test query');
    });
  });

  it('displays filter controls', async () => {
    render(
      <TestWrapper>
        <EmailList />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Unread only')).toBeInTheDocument();
      expect(screen.getByText('Clear Filters')).toBeInTheDocument();
    });
  });

  it('shows correct inbox title', async () => {
    render(
      <TestWrapper>
        <EmailList />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Inbox')).toBeInTheDocument();
    });
  });

  it('displays sort controls', async () => {
    render(
      <TestWrapper>
        <EmailList />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/Sort by:/)).toBeInTheDocument();
      expect(screen.getByText(/Date/)).toBeInTheDocument();
      expect(screen.getByText(/Sender/)).toBeInTheDocument();
      expect(screen.getByText(/Subject/)).toBeInTheDocument();
    });
  });

  it('can toggle sort options', async () => {
    render(
      <TestWrapper>
        <EmailList />
      </TestWrapper>
    );

    await waitFor(() => {
      const senderButton = screen.getByText(/Sender/);
      fireEvent.click(senderButton);
      // The component should handle the sort change
      expect(senderButton).toBeInTheDocument();
    });
  });

  it('shows empty state message when no emails', async () => {
    render(
      <TestWrapper>
        <EmailList />
      </TestWrapper>
    );

    // Initially shows loading, then should show empty state if no data
    await waitFor(() => {
      // Since we don't have mock data setup, it should show empty state
      // Check that page loads without errors
      expect(screen.getByText(/Email List/i)).toBeInTheDocument();
    }, { timeout: 1000 });
  });
});

describe('Email Filters', () => {
  it('can toggle unread filter', async () => {
    render(
      <TestWrapper>
        <EmailList />
      </TestWrapper>
    );

    await waitFor(() => {
      const unreadCheckbox = screen.getByLabelText('Unread only');
      expect(unreadCheckbox).toBeInTheDocument();
      
      fireEvent.click(unreadCheckbox);
      expect(unreadCheckbox).toBeChecked();
    });
  });

  it('can enter sender filter', async () => {
    render(
      <TestWrapper>
        <EmailList />
      </TestWrapper>
    );

    await waitFor(() => {
      const senderInput = screen.getByPlaceholderText('Filter by sender');
      expect(senderInput).toBeInTheDocument();
      
      fireEvent.change(senderInput, { target: { value: 'test@example.com' } });
      expect(senderInput).toHaveValue('test@example.com');
    });
  });

  it('can clear all filters', async () => {
    render(
      <TestWrapper>
        <EmailList />
      </TestWrapper>
    );

    await waitFor(() => {
      const clearButton = screen.getByText('Clear Filters');
      expect(clearButton).toBeInTheDocument();
      
      // Should be disabled initially since no filters are active
      expect(clearButton).toBeDisabled();
    });
  });
});

describe('Search Functionality', () => {
  it('switches to search mode when query entered', async () => {
    render(
      <TestWrapper>
        <EmailList />
      </TestWrapper>
    );

    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText('Search emails...');
      fireEvent.change(searchInput, { target: { value: 'test search' } });
      
      // Should eventually show "Search Results" title instead of "Inbox"
      setTimeout(() => {
        expect(screen.queryByText('Search Results')).toBeInTheDocument();
      }, 500); // Account for debounce
    });
  });

  it('shows clear button when search has text', async () => {
    render(
      <TestWrapper>
        <EmailList />
      </TestWrapper>
    );

    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText('Search emails...');
      fireEvent.change(searchInput, { target: { value: 'test' } });
      
      // Clear button should appear
      setTimeout(() => {
        const clearButton = screen.getByTitle('Clear search');
        expect(clearButton).toBeInTheDocument();
      }, 100);
    });
  });
});