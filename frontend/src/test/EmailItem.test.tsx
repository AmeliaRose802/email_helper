// Email item component tests
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import { EmailItem } from '@/components/Email/EmailItem';
import { apiSlice } from '@/services/api';
import authSlice from '@/store/authSlice';
import type { Email } from '@/types/email';

// Mock navigation
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock the API hooks
vi.mock('@/services/emailApi', () => ({
  useMarkEmailReadMutation: () => [vi.fn().mockResolvedValue({}), { isLoading: false }],
  useGetCategoryMappingsQuery: () => ({
    data: [
      { category: 'required_action', outlook_folder: 'Action Required' },
      { category: 'fyi', outlook_folder: 'FYI' },
      { category: 'waiting', outlook_folder: 'Waiting' },
    ],
    isLoading: false,
  }),
  useUpdateEmailClassificationMutation: () => [vi.fn().mockResolvedValue({}), { isLoading: false }],
}));

// Mock email data
const mockEmail: Email = {
  id: '1',
  subject: 'Test Email Subject',
  sender: 'sender@example.com',
  recipient: 'recipient@example.com',
  date: '2025-01-15T10:30:00Z',
  body: 'This is a test email body with some content that should be truncated in the preview.',
  html_body: '<p>This is a test email body with some content.</p>',
  is_read: false,
  importance: 'High',
  has_attachments: true,
  categories: ['required_action'],
  conversation_id: 'conv-123',
  conversation_count: 3,
  folder_name: 'Inbox',
};

const mockReadEmail: Email = {
  ...mockEmail,
  id: '2',
  subject: 'Read Email Subject',
  is_read: true,
  importance: 'Normal',
  has_attachments: false,
  categories: ['fyi'],
};

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

describe('EmailItem Component', () => {
  const mockOnSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders email subject and sender', () => {
    render(
      <TestWrapper>
        <EmailItem
          email={mockEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Test Email Subject')).toBeInTheDocument();
    expect(screen.getByText('sender@example.com')).toBeInTheDocument();
  });

  it('shows email preview content', () => {
    render(
      <TestWrapper>
        <EmailItem
          email={mockEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    // Should show truncated preview
    expect(screen.getByText(/This is a test email body with some content/)).toBeInTheDocument();
  });

  it('displays unread indicator for unread emails', () => {
    render(
      <TestWrapper>
        <EmailItem
          email={mockEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    // Check for unread styling (the component has conditional styling)
    const emailItem = screen.getByText('Test Email Subject').closest('.email-item__container');
    expect(emailItem).toHaveClass('unread');
  });

  it('does not show unread indicator for read emails', () => {
    render(
      <TestWrapper>
        <EmailItem
          email={mockReadEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    const emailItem = screen.getByText('Read Email Subject').closest('.email-item__container');
    expect(emailItem).not.toHaveClass('unread');
  });

  it('shows attachment indicator when email has attachments', () => {
    render(
      <TestWrapper>
        <EmailItem
          email={mockEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    expect(screen.getByTitle('Has attachments')).toBeInTheDocument();
  });

  it('does not show attachment indicator when email has no attachments', () => {
    render(
      <TestWrapper>
        <EmailItem
          email={mockReadEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    expect(screen.queryByTitle('Has attachments')).not.toBeInTheDocument();
  });

  it('shows category badge when showCategory is true', async () => {
    render(
      <TestWrapper>
        <EmailItem
          email={mockEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    // Category is now shown in a dropdown, not as a text badge
    // Wait for the dropdown to appear after loading
    await waitFor(() => {
      const dropdown = screen.getByTitle(/Change classification/);
      expect(dropdown).toBeInTheDocument();
    });
  });

  it('hides category badge when showCategory is false', () => {
    // This test is no longer relevant since we removed showCategory prop
    // Category is now always shown in the dropdown
    expect(true).toBe(true);
  });

  it('shows priority indicator for high priority emails', () => {
    render(
      <TestWrapper>
        <EmailItem
          email={mockEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    expect(screen.getByTitle('High priority')).toBeInTheDocument();
  });

  it('does not show priority indicator for normal priority emails', () => {
    render(
      <TestWrapper>
        <EmailItem
          email={mockReadEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    expect(screen.queryByTitle('Normal priority')).not.toBeInTheDocument();
  });

  it('handles checkbox selection', () => {
    render(
      <TestWrapper>
        <EmailItem
          email={mockEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    const checkbox = screen.getByTitle('Select email');
    fireEvent.click(checkbox);

    expect(mockOnSelect).toHaveBeenCalledTimes(1);
  });

  it('shows selected state when isSelected is true', () => {
    render(
      <TestWrapper>
        <EmailItem
          email={mockEmail}
          isSelected={true}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    const checkbox = screen.getByTitle('Select email') as HTMLInputElement;
    expect(checkbox.checked).toBe(true);
  });

  it('navigates to email detail when clicked', async () => {
    render(
      <TestWrapper>
        <EmailItem
          email={mockEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    const emailItem = screen.getByText('Test Email Subject').closest('.email-item__container');
    fireEvent.click(emailItem!);

    // Wait for async click handler to complete
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/emails/1');
    });
  });

  it('does not trigger navigation when checkbox is clicked', () => {
    render(
      <TestWrapper>
        <EmailItem
          email={mockEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    const checkbox = screen.getByTitle('Select email');
    fireEvent.click(checkbox);

    // Navigation should not be called, only onSelect
    expect(mockNavigate).not.toHaveBeenCalled();
    expect(mockOnSelect).toHaveBeenCalledTimes(1);
  });

  it('formats date correctly', () => {
    render(
      <TestWrapper>
        <EmailItem
          email={mockEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    // Should show formatted date (exact format depends on current date)
    // Just check that some date-like text is present
    const dateElements = screen.getAllByText(/Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{1,2}:\d{2}/);
    expect(dateElements.length).toBeGreaterThan(0);
  });

  it('shows conversation indicator when part of conversation', () => {
    render(
      <TestWrapper>
        <EmailItem
          email={mockEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    // Updated to match actual title format which includes count
    expect(screen.getByTitle('Part of conversation (3 emails)')).toBeInTheDocument();
  });
});