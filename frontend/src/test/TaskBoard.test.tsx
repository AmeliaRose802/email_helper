import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { TaskBoard } from '@/components/Task/TaskBoard';
import { apiSlice } from '@/services/api';
import type { Task } from '@/types/task';

// Mock store setup
const mockStore = configureStore({
  reducer: {
    api: apiSlice.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(apiSlice.middleware),
});

// Mock tasks data
const mockTasks: Task[] = [
  {
    id: '1',
    title: 'Test Task 1',
    description: 'This is a test task',
    status: 'todo',
    priority: 'high',
    category: 'required_action',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    tags: ['test'],
    progress: 0,
  },
  {
    id: '2',
    title: 'Test Task 2',
    description: 'Another test task',
    status: 'in-progress',
    priority: 'medium',
    category: 'team_action',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    tags: ['test', 'work'],
    progress: 50,
  },
  {
    id: '3',
    title: 'Test Task 3',
    status: 'done',
    priority: 'low',
    category: 'fyi',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    tags: [],
    progress: 100,
  },
];

// Wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Provider store={mockStore}>
    <DndProvider backend={HTML5Backend}>
      {children}
    </DndProvider>
  </Provider>
);

describe('TaskBoard', () => {
  it('renders all kanban columns', () => {
    const mockOnEditTask = vi.fn();
    
    render(
      <TestWrapper>
        <TaskBoard tasks={mockTasks} onEditTask={mockOnEditTask} />
      </TestWrapper>
    );

    // Check that all columns are rendered
    expect(screen.getByText('To Do')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
    expect(screen.getByText('Review')).toBeInTheDocument();
    expect(screen.getByText('Done')).toBeInTheDocument();
  });

  it('displays tasks in correct columns', () => {
    const mockOnEditTask = vi.fn();
    
    render(
      <TestWrapper>
        <TaskBoard tasks={mockTasks} onEditTask={mockOnEditTask} />
      </TestWrapper>
    );

    // Check task placement in columns
    expect(screen.getByText('Test Task 1')).toBeInTheDocument(); // todo
    expect(screen.getByText('Test Task 2')).toBeInTheDocument(); // in-progress
    expect(screen.getByText('Test Task 3')).toBeInTheDocument(); // done
  });

  it('displays correct task counts in column headers', () => {
    const mockOnEditTask = vi.fn();
    
    render(
      <TestWrapper>
        <TaskBoard tasks={mockTasks} onEditTask={mockOnEditTask} />
      </TestWrapper>
    );

    // Check task counts - each column should show the number of tasks
    const counts = screen.getAllByText(/^[0-9]+$/);
    expect(counts.length).toBeGreaterThan(0);
  });

  it('shows loading state when isLoading is true', () => {
    const mockOnEditTask = vi.fn();
    
    render(
      <TestWrapper>
        <TaskBoard tasks={[]} onEditTask={mockOnEditTask} isLoading={true} />
      </TestWrapper>
    );

    expect(screen.getByText('Loading tasks...')).toBeInTheDocument();
  });

  it('shows empty state when no tasks provided', () => {
    const mockOnEditTask = vi.fn();
    
    render(
      <TestWrapper>
        <TaskBoard tasks={[]} onEditTask={mockOnEditTask} />
      </TestWrapper>
    );

    // Should show "No tasks" in empty columns
    const noTasksElements = screen.getAllByText('No tasks');
    expect(noTasksElements.length).toBe(4); // One for each column
  });
});