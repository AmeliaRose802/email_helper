import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TaskForm } from './TaskForm';
import type { Task } from '@/types/task';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { api } from '@/services/api';

// Mock the API
const mockCreateTask = vi.fn();
const mockUpdateTask = vi.fn();

vi.mock('@/services/taskApi', () => ({
  useCreateTaskMutation: () => [mockCreateTask, { isLoading: false }],
  useUpdateTaskMutation: () => [mockUpdateTask, { isLoading: false }],
}));

// Create a minimal store for testing
const createTestStore = () => {
  return configureStore({
    reducer: {
      [api.reducerPath]: api.reducer,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(api.middleware),
  });
};

const renderWithProvider = (component: React.ReactElement) => {
  const store = createTestStore();
  return render(<Provider store={store}>{component}</Provider>);
};

describe('TaskForm', () => {
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockCreateTask.mockResolvedValue({ unwrap: () => Promise.resolve({}) });
    mockUpdateTask.mockResolvedValue({ unwrap: () => Promise.resolve({}) });
  });

  describe('Create Mode', () => {
    it('renders create form with empty fields', () => {
      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByText('Create New Task')).toBeInTheDocument();
      expect(screen.getByLabelText(/title/i)).toHaveValue('');
      expect(screen.getByLabelText(/description/i)).toHaveValue('');
    });

    it('renders with email ID prop', () => {
      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} emailId="email123" />
      );

      expect(screen.getByText('Create New Task')).toBeInTheDocument();
    });

    it('shows validation error when title is empty', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} />
      );

      const submitButton = screen.getByRole('button', { name: /create/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/title is required/i)).toBeInTheDocument();
      });
    });

    it('creates task with valid data', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} />
      );

      // Fill out form
      await user.type(screen.getByLabelText(/title/i), 'New Task');
      await user.type(screen.getByLabelText(/description/i), 'Task description');
      await user.selectOptions(screen.getByLabelText(/priority/i), 'high');

      // Submit form
      const submitButton = screen.getByRole('button', { name: /create/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockCreateTask).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'New Task',
            description: 'Task description',
            priority: 'high',
          })
        );
      });

      expect(mockOnClose).toHaveBeenCalled();
    });

    it('validates due date is not in the past', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} />
      );

      await user.type(screen.getByLabelText(/title/i), 'New Task');
      
      // Set a past date
      const pastDate = new Date();
      pastDate.setDate(pastDate.getDate() - 1);
      const dateInput = screen.getByLabelText(/due date/i);
      await user.type(dateInput, pastDate.toISOString().split('T')[0]);

      const submitButton = screen.getByRole('button', { name: /create/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/due date cannot be in the past/i)).toBeInTheDocument();
      });
    });

    it('adds tags when Enter is pressed', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} />
      );

      const tagInput = screen.getByPlaceholderText(/add tag/i);
      
      await user.type(tagInput, 'urgent{Enter}');
      expect(screen.getByText('urgent')).toBeInTheDocument();

      await user.type(tagInput, 'work{Enter}');
      expect(screen.getByText('work')).toBeInTheDocument();
    });

    it('prevents duplicate tags', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} />
      );

      const tagInput = screen.getByPlaceholderText(/add tag/i);
      
      await user.type(tagInput, 'urgent{Enter}');
      await user.type(tagInput, 'urgent{Enter}');

      const urgentTags = screen.getAllByText('urgent');
      expect(urgentTags).toHaveLength(1);
    });

    it('removes tags when delete button is clicked', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} />
      );

      const tagInput = screen.getByPlaceholderText(/add tag/i);
      await user.type(tagInput, 'urgent{Enter}');
      
      const tagElement = screen.getByText('urgent');
      expect(tagElement).toBeInTheDocument();

      const removeButton = screen.getByRole('button', { name: /×/ });
      await user.click(removeButton);

      expect(screen.queryByText('urgent')).not.toBeInTheDocument();
    });

    it('handles API error gracefully', async () => {
      mockCreateTask.mockResolvedValue({
        unwrap: () => Promise.reject(new Error('API Error'))
      });

      const user = userEvent.setup();
      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} />
      );

      await user.type(screen.getByLabelText(/title/i), 'New Task');
      const submitButton = screen.getByRole('button', { name: /create/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/failed to save task/i)).toBeInTheDocument();
      });

      expect(mockOnClose).not.toHaveBeenCalled();
    });
  });

  describe('Edit Mode', () => {
    const mockTask: Task = {
      id: 'task-1',
      title: 'Existing Task',
      description: 'Task description',
      status: 'todo',
      priority: 'medium',
      category: 'required_personal_action',
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
      tags: ['urgent', 'work'],
      progress: 50,
    };

    it('renders edit form with task data', () => {
      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} task={mockTask} />
      );

      expect(screen.getByText('Edit Task')).toBeInTheDocument();
      expect(screen.getByLabelText(/title/i)).toHaveValue('Existing Task');
      expect(screen.getByLabelText(/description/i)).toHaveValue('Task description');
      expect(screen.getByLabelText(/priority/i)).toHaveValue('medium');
    });

    it('displays existing tags', () => {
      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} task={mockTask} />
      );

      expect(screen.getByText('urgent')).toBeInTheDocument();
      expect(screen.getByText('work')).toBeInTheDocument();
    });

    it('updates task with modified data', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} task={mockTask} />
      );

      // Modify title
      const titleInput = screen.getByLabelText(/title/i);
      await user.clear(titleInput);
      await user.type(titleInput, 'Updated Task');

      // Change priority
      await user.selectOptions(screen.getByLabelText(/priority/i), 'high');

      // Submit form
      const submitButton = screen.getByRole('button', { name: /update/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockUpdateTask).toHaveBeenCalledWith({
          id: 'task-1',
          data: expect.objectContaining({
            title: 'Updated Task',
            priority: 'high',
          }),
        });
      });

      expect(mockOnClose).toHaveBeenCalled();
    });

    it('displays progress slider in edit mode', () => {
      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} task={mockTask} />
      );

      const progressSlider = screen.getByLabelText(/progress/i);
      expect(progressSlider).toBeInTheDocument();
      expect(progressSlider).toHaveValue('50');
    });

    it('updates progress value', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} task={mockTask} />
      );

      const progressSlider = screen.getByLabelText(/progress/i);
      await user.type(progressSlider, '75');

      expect(progressSlider).toHaveValue('75');
    });
  });

  describe('Form Interactions', () => {
    it('closes form when close button is clicked', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} />
      );

      const closeButton = screen.getByRole('button', { name: /×/ });
      await user.click(closeButton);

      expect(mockOnClose).toHaveBeenCalled();
    });

    it('closes form when overlay is clicked', () => {
      const { container } = renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} />
      );

      const overlay = container.querySelector('.task-form-overlay');
      fireEvent.click(overlay!);

      expect(mockOnClose).toHaveBeenCalled();
    });

    it('disables form inputs while loading', () => {
      vi.mock('@/services/taskApi', () => ({
        useCreateTaskMutation: () => [mockCreateTask, { isLoading: true }],
        useUpdateTaskMutation: () => [mockUpdateTask, { isLoading: false }],
      }));

      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByLabelText(/title/i)).toBeDisabled();
      expect(screen.getByLabelText(/description/i)).toBeDisabled();
      expect(screen.getByLabelText(/priority/i)).toBeDisabled();
    });

    it('resets form when reopened for creation', () => {
      const { rerender } = renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} />
      );

      const titleInput = screen.getByLabelText(/title/i) as HTMLInputElement;
      fireEvent.change(titleInput, { target: { value: 'Test Title' } });

      // Close and reopen
      rerender(
        <Provider store={createTestStore()}>
          <TaskForm isOpen={false} onClose={mockOnClose} />
        </Provider>
      );

      rerender(
        <Provider store={createTestStore()}>
          <TaskForm isOpen={true} onClose={mockOnClose} />
        </Provider>
      );

      expect(screen.getByLabelText(/title/i)).toHaveValue('');
    });
  });

  describe('Category Selection', () => {
    it('allows selecting different categories', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} />
      );

      const categorySelect = screen.getByLabelText(/category/i);
      await user.selectOptions(categorySelect, 'team_action');

      expect(categorySelect).toHaveValue('team_action');
    });

    it('defaults to required_action category', () => {
      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} />
      );

      const categorySelect = screen.getByLabelText(/category/i);
      expect(categorySelect).toHaveValue('required_action');
    });
  });

  describe('Accessibility', () => {
    it('has proper labels for all form inputs', () => {
      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/priority/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/category/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/due date/i)).toBeInTheDocument();
    });

    it('shows required indicator for title field', () => {
      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByText(/title \*/i)).toBeInTheDocument();
    });

    it('associates error messages with inputs', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <TaskForm isOpen={true} onClose={mockOnClose} />
      );

      const submitButton = screen.getByRole('button', { name: /create/i });
      await user.click(submitButton);

      await waitFor(() => {
        const titleInput = screen.getByLabelText(/title/i);
        expect(titleInput).toHaveClass('error');
      });
    });
  });
});
