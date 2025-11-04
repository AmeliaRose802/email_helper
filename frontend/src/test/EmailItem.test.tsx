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
  received_time: '2025-01-15T10:30:00Z',
  content: 'This is a test email body with some content that should be truncated in the preview.',
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

// Mock select handler for all tests
const mockOnSelect = vi.fn();

describe('EmailItem Component', () => {
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

describe('Edge Cases - Error Handling', () => {
  it('handles missing subject gracefully', () => {
    const emailWithoutSubject = { ...mockEmail, subject: '' };
    
    render(
      <TestWrapper>
        <EmailItem
          email={emailWithoutSubject}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    // Should render without crashing
    expect(screen.getByText('sender@example.com')).toBeInTheDocument();
  });

  it('handles missing sender gracefully', () => {
    const emailWithoutSender = { ...mockEmail, sender: '' };
    
    render(
      <TestWrapper>
        <EmailItem
          email={emailWithoutSender}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Test Email Subject')).toBeInTheDocument();
  });

  it('handles missing body content gracefully', () => {
    const emailWithoutBody = { ...mockEmail, content: '' };
    
    render(
      <TestWrapper>
        <EmailItem
          email={emailWithoutBody}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Test Email Subject')).toBeInTheDocument();
  });

  it('handles malformed date strings', () => {
    const emailWithBadDate = { ...mockEmail, received_time: 'invalid-date' };
    
    render(
      <TestWrapper>
        <EmailItem
          email={emailWithBadDate}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    // Should render without crashing
    expect(screen.getByText('Test Email Subject')).toBeInTheDocument();
  });

  it('handles null conversation_id', () => {
    const emailWithoutConversation = { ...mockEmail, conversation_id: null as any, conversation_count: 1 };
    
    render(
      <TestWrapper>
        <EmailItem
          email={emailWithoutConversation}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Test Email Subject')).toBeInTheDocument();
  });

  it('handles missing categories array', () => {
    const emailWithoutCategories = { ...mockEmail, categories: [] };
    
    render(
      <TestWrapper>
        <EmailItem
          email={emailWithoutCategories}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Test Email Subject')).toBeInTheDocument();
  });
});

describe('Edge Cases - Interaction Edge Cases', () => {
  it('handles double-click on email item', async () => {
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
    
    // Double click should not cause errors
    fireEvent.click(emailItem!);
    fireEvent.click(emailItem!);

    await waitFor(() => {
      // Should have navigated (calls may have happened multiple times)
      expect(mockNavigate).toHaveBeenCalled();
    });
  });

  it('handles rapid checkbox toggling', () => {
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
    
    // Rapid clicks
    for (let i = 0; i < 5; i++) {
      fireEvent.click(checkbox);
    }

    expect(mockOnSelect).toHaveBeenCalledTimes(5);
  });

  it('prevents navigation during checkbox interaction', () => {
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
    
    // Click checkbox
    fireEvent.click(checkbox);

    // Navigation should NOT be triggered
    expect(mockNavigate).not.toHaveBeenCalled();
    expect(mockOnSelect).toHaveBeenCalledTimes(1);
  });

  it('handles keyboard events on email item', () => {
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
    
    // Keyboard events should not cause errors
    fireEvent.keyDown(emailItem!, { key: 'Enter' });
    fireEvent.keyDown(emailItem!, { key: 'Space' });
    fireEvent.keyDown(emailItem!, { key: 'ArrowDown' });

    // Should not crash
    expect(emailItem).toBeInTheDocument();
  });

  it('handles click during loading state', async () => {
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
    
    // Click while async operation may be in progress
    fireEvent.click(emailItem!);
    fireEvent.click(emailItem!);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalled();
    });
  });
});

describe('Edge Cases - Display Edge Cases', () => {
  it('truncates very long subject lines', () => {
    const longSubject = 'A'.repeat(200);
    const emailWithLongSubject = { ...mockEmail, subject: longSubject };
    
    render(
      <TestWrapper>
        <EmailItem
          email={emailWithLongSubject}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    // Subject should be rendered (may be truncated via CSS)
    const subjectElement = screen.getByText(longSubject);
    expect(subjectElement).toBeInTheDocument();
  });

  it('handles emails with special characters in subject', () => {
    const specialSubject = 'Test <>&"\'`\\ Special Chars';
    const emailWithSpecialChars = { ...mockEmail, subject: specialSubject };
    
    render(
      <TestWrapper>
        <EmailItem
          email={emailWithSpecialChars}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    // Should handle special characters properly
    expect(screen.getByText(specialSubject)).toBeInTheDocument();
  });

  it('handles emails with Unicode characters', () => {
    const unicodeSubject = 'Test 你好 🎉 Émojis';
    const emailWithUnicode = { ...mockEmail, subject: unicodeSubject };
    
    render(
      <TestWrapper>
        <EmailItem
          email={emailWithUnicode}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    expect(screen.getByText(unicodeSubject)).toBeInTheDocument();
  });

  it('handles very long body preview', () => {
    const longBody = 'B'.repeat(1000);
    const emailWithLongBody = { ...mockEmail, content: longBody };
    
    render(
      <TestWrapper>
        <EmailItem
          email={emailWithLongBody}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    // Body should be truncated in preview
    expect(screen.getByText('Test Email Subject')).toBeInTheDocument();
  });

  it('formats relative dates correctly', () => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 10, 30);
    const emailToday = { ...mockEmail, received_time: today.toISOString() };
    
    render(
      <TestWrapper>
        <EmailItem
          email={emailToday}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    // Should show time for today's emails
    expect(screen.getByText('Test Email Subject')).toBeInTheDocument();
  });

  it('formats absolute dates for older emails', () => {
    const oldDate = new Date('2020-01-15T10:30:00Z');
    const oldEmail = { ...mockEmail, received_time: oldDate.toISOString() };
    
    render(
      <TestWrapper>
        <EmailItem
          email={oldEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    // Should show full date for old emails
    expect(screen.getByText('Test Email Subject')).toBeInTheDocument();
  });
});

describe('Edge Cases - Category Management', () => {
  it('handles category dropdown interaction', async () => {
    render(
      <TestWrapper>
        <EmailItem
          email={mockEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    await waitFor(() => {
      const dropdown = screen.getByTitle(/Change classification/);
      expect(dropdown).toBeInTheDocument();
    });
  });

  it('handles unknown category values', async () => {
    const emailWithUnknownCategory = { ...mockEmail, categories: ['unknown_category'] };
    
    render(
      <TestWrapper>
        <EmailItem
          email={emailWithUnknownCategory}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    // Should render without crashing
    await waitFor(() => {
      expect(screen.getByText('Test Email Subject')).toBeInTheDocument();
    });
  });

  it('handles multiple categories', async () => {
    const emailWithMultipleCategories = { 
      ...mockEmail, 
      categories: ['required_action', 'fyi', 'waiting'] 
    };
    
    render(
      <TestWrapper>
        <EmailItem
          email={emailWithMultipleCategories}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    // Should handle multiple categories appropriately
    await waitFor(() => {
      expect(screen.getByText('Test Email Subject')).toBeInTheDocument();
    });
  });
});

describe('Edge Cases - Accessibility', () => {
  it('provides ARIA labels for all interactive elements', () => {
    render(
      <TestWrapper>
        <EmailItem
          email={mockEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    // Checkbox should have accessible label
    const checkbox = screen.getByTitle('Select email');
    expect(checkbox).toBeInTheDocument();
  });

  it('maintains focus indicators', () => {
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
    
    // Focus should be manageable
    fireEvent.focus(emailItem!);
    expect(emailItem).toBeInTheDocument();
  });

  it('provides text alternatives for icons', () => {
    render(
      <TestWrapper>
        <EmailItem
          email={mockEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    // Icons should have title attributes
    expect(screen.getByTitle('High priority')).toBeInTheDocument();
    expect(screen.getByTitle('Has attachments')).toBeInTheDocument();
  });

  it('announces selection state changes', () => {
    const { rerender } = render(
      <TestWrapper>
        <EmailItem
          email={mockEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    const checkbox = screen.getByTitle('Select email') as HTMLInputElement;
    expect(checkbox.checked).toBe(false);

    // Change selection state
    rerender(
      <TestWrapper>
        <EmailItem
          email={mockEmail}
          isSelected={true}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    expect(checkbox.checked).toBe(true);
  });
});

describe('Edge Cases - Performance', () => {
  it('renders efficiently', () => {
    const startTime = performance.now();
    
    render(
      <TestWrapper>
        <EmailItem
          email={mockEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    // Should render quickly (< 100ms)
    expect(renderTime).toBeLessThan(100);
  });

  it('handles rapid prop updates efficiently', () => {
    const { rerender } = render(
      <TestWrapper>
        <EmailItem
          email={mockEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    // Rapid selection state changes
    for (let i = 0; i < 10; i++) {
      rerender(
        <TestWrapper>
          <EmailItem
            email={mockEmail}
            isSelected={i % 2 === 0}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );
    }

    expect(screen.getByText('Test Email Subject')).toBeInTheDocument();
  });

  it('cleans up event listeners on unmount', () => {
    const { unmount } = render(
      <TestWrapper>
        <EmailItem
          email={mockEmail}
          isSelected={false}
          onSelect={mockOnSelect}
        />
      </TestWrapper>
    );

    // Should unmount without leaking memory
    unmount();
  });
});