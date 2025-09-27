// Tests for LoginForm component
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import LoginForm from '@/components/LoginForm';
import authReducer from '@/store/authSlice';
import { apiSlice } from '@/services/api';

// Mock the auth API
const mockLoginMutation = vi.fn();
vi.mock('@/services/authApi', () => ({
  useLoginMutation: () => [mockLoginMutation, { isLoading: false }],
}));

// Mock the router hooks
const mockNavigate = vi.fn();
const mockLocation = { state: null };
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => mockLocation,
  };
});

// Create a test wrapper with Redux store and router
const createTestStore = () => {
  return configureStore({
    reducer: {
      auth: authReducer,
      api: apiSlice.reducer,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(apiSlice.middleware),
  });
};

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

describe('LoginForm', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
    mockLoginMutation.mockReturnValue({
      unwrap: vi.fn().mockResolvedValue({
        access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6OTk5OTk5OTk5OSwidXNlcl9pZCI6MX0.signature',
        refresh_token: 'test_refresh_token',
        token_type: 'bearer',
        expires_in: 3600,
      }),
    });
  });

  it('renders login form with all required fields', () => {
    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    );

    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/remember me/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('shows validation errors for empty fields', async () => {
    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    );

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Username is required')).toBeInTheDocument();
      expect(screen.getByText('Password is required')).toBeInTheDocument();
    });
  });

  it('shows validation errors for short username and password', async () => {
    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    );

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    await user.type(usernameInput, 'ab'); // Too short
    await user.type(passwordInput, '123'); // Too short
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Username must be at least 3 characters')).toBeInTheDocument();
      expect(screen.getByText('Password must be at least 6 characters')).toBeInTheDocument();
    });
  });

  it('submits form with valid data', async () => {
    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    );

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockLoginMutation).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
      });
    });
  });

  it('handles remember me checkbox', async () => {
    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    );

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const rememberCheckbox = screen.getByLabelText(/remember me/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    await user.click(rememberCheckbox);
    
    expect(rememberCheckbox).toBeChecked();
    
    await user.click(submitButton);

    // The form should submit successfully
    await waitFor(() => {
      expect(mockLoginMutation).toHaveBeenCalled();
    });
  });

  it('shows loading state during submission', async () => {
    // Mock a delayed login response
    mockLoginMutation.mockReturnValue({
      unwrap: vi.fn().mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100))),
    });

    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    );

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);

    // Should show loading state
    expect(screen.getByText('Signing in...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled();
  });

  it('handles login errors', async () => {
    const errorMessage = 'Invalid credentials';
    mockLoginMutation.mockReturnValue({
      unwrap: vi.fn().mockRejectedValue({
        data: { message: errorMessage }
      }),
    });

    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    );

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'wrongpassword');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    // Password field should be cleared on error
    expect(passwordInput).toHaveValue('');
    // Username should be preserved
    expect(usernameInput).toHaveValue('testuser');
  });

  it('disables form fields during submission', async () => {
    // Mock a delayed login response
    let resolveLogin: (value: any) => void = () => {};
    const loginPromise = new Promise(resolve => {
      resolveLogin = resolve;
    });
    
    mockLoginMutation.mockReturnValue({
      unwrap: vi.fn().mockReturnValue(loginPromise),
    });

    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    );

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const rememberCheckbox = screen.getByLabelText(/remember me/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);

    // All form fields should be disabled during submission
    expect(usernameInput).toBeDisabled();
    expect(passwordInput).toBeDisabled();
    expect(rememberCheckbox).toBeDisabled();
    expect(submitButton).toBeDisabled();

    // Resolve the login to cleanup
    resolveLogin({
      access_token: 'test_token',
      refresh_token: 'test_refresh',
      token_type: 'bearer',
      expires_in: 3600,
    });
  });

  it('has proper accessibility attributes', () => {
    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    );

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);

    expect(usernameInput).toHaveAttribute('aria-invalid', 'false');
    expect(passwordInput).toHaveAttribute('aria-invalid', 'false');
    expect(usernameInput).toHaveAttribute('autoComplete', 'username');
    expect(passwordInput).toHaveAttribute('autoComplete', 'current-password');
    
    // Required fields should be marked
    expect(screen.getAllByText('*', { selector: '.required' })).toHaveLength(2);
  });
});