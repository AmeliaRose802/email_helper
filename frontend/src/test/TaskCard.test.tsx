import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { TaskCard } from '@/components/Task/TaskCard';
import type { Task } from '@/types/task';

// Mock task data
const mockTask: Task = {
  id: '1',
  title: 'Test Task',
  description: 'This is a test task with a longer description that should be truncated',
  status: 'todo',
  priority: 'high',
  category: 'required_action',
  due_date: '2024-12-31T23:59:59Z',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  email_id: 'email-123',
  tags: ['urgent', 'frontend', 'testing'],
  progress: 75,
};

// Wrapper component for DnD
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <DndProvider backend={HTML5Backend}>
    {children}
  </DndProvider>
);

describe('TaskCard', () => {
  it('renders task information correctly', () => {
    const mockOnEdit = vi.fn();
    
    render(
      <TestWrapper>
        <TaskCard task={mockTask} onEdit={mockOnEdit} />
      </TestWrapper>
    );

    expect(screen.getByText('Test Task')).toBeInTheDocument();
    expect(screen.getByText(/This is a test task with a longer description/)).toBeInTheDocument();
    expect(screen.getByText('high')).toBeInTheDocument();
  });

  it('shows progress bar when progress is set', () => {
    const mockOnEdit = vi.fn();
    
    render(
      <TestWrapper>
        <TaskCard task={mockTask} onEdit={mockOnEdit} />
      </TestWrapper>
    );

    expect(screen.getByText('Progress')).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('displays tags correctly', () => {
    const mockOnEdit = vi.fn();
    
    render(
      <TestWrapper>
        <TaskCard task={mockTask} onEdit={mockOnEdit} />
      </TestWrapper>
    );

    expect(screen.getByText('urgent')).toBeInTheDocument();
    expect(screen.getByText('frontend')).toBeInTheDocument();
    expect(screen.getByText('testing')).toBeInTheDocument();
  });

  it('shows email indicator when task is created from email', () => {
    const mockOnEdit = vi.fn();
    
    render(
      <TestWrapper>
        <TaskCard task={mockTask} onEdit={mockOnEdit} />
      </TestWrapper>
    );

    expect(screen.getByTitle('Created from email')).toBeInTheDocument();
  });

  it('shows deadline indicator when due date is set', () => {
    const mockOnEdit = vi.fn();
    
    render(
      <TestWrapper>
        <TaskCard task={mockTask} onEdit={mockOnEdit} />
      </TestWrapper>
    );

    // The deadline indicator should be present
    expect(screen.getByText(/Dec 31, 2024/)).toBeInTheDocument();
  });

  it('calls onEdit when card is clicked', () => {
    const mockOnEdit = vi.fn();
    
    render(
      <TestWrapper>
        <TaskCard task={mockTask} onEdit={mockOnEdit} />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('Test Task'));
    expect(mockOnEdit).toHaveBeenCalledTimes(1);
  });

  it('shows delete button when onDelete is provided', () => {
    const mockOnEdit = vi.fn();
    const mockOnDelete = vi.fn();
    
    render(
      <TestWrapper>
        <TaskCard task={mockTask} onEdit={mockOnEdit} onDelete={mockOnDelete} />
      </TestWrapper>
    );

    const deleteButton = screen.getByLabelText('Delete task');
    expect(deleteButton).toBeInTheDocument();
    
    fireEvent.click(deleteButton);
    expect(mockOnDelete).toHaveBeenCalledTimes(1);
  });

  it('truncates long descriptions', () => {
    const taskWithLongDescription: Task = {
      ...mockTask,
      description: 'This is a very long description that should be truncated because it exceeds the maximum length allowed for display in the task card component',
    };
    
    const mockOnEdit = vi.fn();
    
    render(
      <TestWrapper>
        <TaskCard task={taskWithLongDescription} onEdit={mockOnEdit} />
      </TestWrapper>
    );

    // Should show truncated text with ellipsis
    expect(screen.getByText(/This is a very long description that should be truncated because it exceeds the maximum length.../)).toBeInTheDocument();
  });

  it('handles task without optional fields', () => {
    const minimalTask: Task = {
      id: '2',
      title: 'Minimal Task',
      status: 'todo',
      priority: 'low',
      category: 'fyi',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      tags: [],
    };
    
    const mockOnEdit = vi.fn();
    
    render(
      <TestWrapper>
        <TaskCard task={minimalTask} onEdit={mockOnEdit} />
      </TestWrapper>
    );

    expect(screen.getByText('Minimal Task')).toBeInTheDocument();
    expect(screen.getByText('low')).toBeInTheDocument();
    
    // Should not show progress bar, description, tags, etc.
    expect(screen.queryByText('Progress')).not.toBeInTheDocument();
    expect(screen.queryByTitle('Created from email')).not.toBeInTheDocument();
  });

  it('applies correct priority styling classes', () => {
    const mockOnEdit = vi.fn();
    
    render(
      <TestWrapper>
        <TaskCard task={mockTask} onEdit={mockOnEdit} />
      </TestWrapper>
    );

    const card = screen.getByText('Test Task').closest('.task-card');
    expect(card).toHaveClass('priority-high');
  });
});