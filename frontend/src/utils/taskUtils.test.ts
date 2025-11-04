import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  isTaskOverdue,
  getTaskUrgencyLevel,
  sortTasksByPriority,
  filterTasks,
  getTaskStats,
  createTaskFromEmail,
} from './taskUtils';
import type { Task, TaskFilter } from '@/types/task';

describe('taskUtils', () => {
  describe('isTaskOverdue', () => {
    beforeEach(() => {
      // Set fixed current time: January 15, 2024, 12:00 PM
      vi.setSystemTime(new Date('2024-01-15T12:00:00Z'));
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('returns false for tasks without due date', () => {
      const task: Task = {
        id: '1',
        title: 'Test Task',
        status: 'todo',
        priority: 'medium',
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
      };
      expect(isTaskOverdue(task)).toBe(false);
    });

    it('returns true for overdue tasks', () => {
      const task: Task = {
        id: '1',
        title: 'Test Task',
        status: 'todo',
        priority: 'medium',
        due_date: '2024-01-14T12:00:00Z', // Yesterday
        created_at: '2024-01-10T10:00:00Z',
        updated_at: '2024-01-10T10:00:00Z',
      };
      expect(isTaskOverdue(task)).toBe(true);
    });

    it('returns false for future tasks', () => {
      const task: Task = {
        id: '1',
        title: 'Test Task',
        status: 'todo',
        priority: 'medium',
        due_date: '2024-01-16T12:00:00Z', // Tomorrow
        created_at: '2024-01-10T10:00:00Z',
        updated_at: '2024-01-10T10:00:00Z',
      };
      expect(isTaskOverdue(task)).toBe(false);
    });

    it('handles edge case of due date exactly now', () => {
      const task: Task = {
        id: '1',
        title: 'Test Task',
        status: 'todo',
        priority: 'medium',
        due_date: '2024-01-15T12:00:00Z', // Right now
        created_at: '2024-01-10T10:00:00Z',
        updated_at: '2024-01-10T10:00:00Z',
      };
      expect(isTaskOverdue(task)).toBe(false);
    });
  });

  describe('getTaskUrgencyLevel', () => {
    beforeEach(() => {
      vi.setSystemTime(new Date('2024-01-15T12:00:00Z'));
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('returns "normal" for tasks without due date', () => {
      const task: Task = {
        id: '1',
        title: 'Test Task',
        status: 'todo',
        priority: 'medium',
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
      };
      expect(getTaskUrgencyLevel(task)).toBe('normal');
    });

    it('returns "overdue" for past due dates', () => {
      const task: Task = {
        id: '1',
        title: 'Test Task',
        status: 'todo',
        priority: 'medium',
        due_date: '2024-01-14T12:00:00Z', // Yesterday
        created_at: '2024-01-10T10:00:00Z',
        updated_at: '2024-01-10T10:00:00Z',
      };
      expect(getTaskUrgencyLevel(task)).toBe('overdue');
    });

    it('returns "urgent" for tasks due within 24 hours', () => {
      const task: Task = {
        id: '1',
        title: 'Test Task',
        status: 'todo',
        priority: 'medium',
        due_date: '2024-01-16T10:00:00Z', // 22 hours from now
        created_at: '2024-01-10T10:00:00Z',
        updated_at: '2024-01-10T10:00:00Z',
      };
      expect(getTaskUrgencyLevel(task)).toBe('urgent');
    });

    it('returns "warning" for tasks due within 72 hours', () => {
      const task: Task = {
        id: '1',
        title: 'Test Task',
        status: 'todo',
        priority: 'medium',
        due_date: '2024-01-17T12:00:00Z', // 48 hours from now
        created_at: '2024-01-10T10:00:00Z',
        updated_at: '2024-01-10T10:00:00Z',
      };
      expect(getTaskUrgencyLevel(task)).toBe('warning');
    });

    it('returns "normal" for tasks due beyond 72 hours', () => {
      const task: Task = {
        id: '1',
        title: 'Test Task',
        status: 'todo',
        priority: 'medium',
        due_date: '2024-01-20T12:00:00Z', // 5 days from now
        created_at: '2024-01-10T10:00:00Z',
        updated_at: '2024-01-10T10:00:00Z',
      };
      expect(getTaskUrgencyLevel(task)).toBe('normal');
    });
  });

  describe('sortTasksByPriority', () => {
    const mockTasks: Task[] = [
      {
        id: '1',
        title: 'Low priority, no deadline',
        status: 'todo',
        priority: 'low',
        created_at: '2024-01-10T10:00:00Z',
        updated_at: '2024-01-10T10:00:00Z',
      },
      {
        id: '2',
        title: 'High priority, far deadline',
        status: 'todo',
        priority: 'high',
        due_date: '2024-01-25T12:00:00Z',
        created_at: '2024-01-12T10:00:00Z',
        updated_at: '2024-01-12T10:00:00Z',
      },
      {
        id: '3',
        title: 'High priority, close deadline',
        status: 'todo',
        priority: 'high',
        due_date: '2024-01-16T12:00:00Z',
        created_at: '2024-01-11T10:00:00Z',
        updated_at: '2024-01-11T10:00:00Z',
      },
      {
        id: '4',
        title: 'Medium priority, no deadline',
        status: 'todo',
        priority: 'medium',
        created_at: '2024-01-13T10:00:00Z',
        updated_at: '2024-01-13T10:00:00Z',
      },
    ];

    it('sorts by priority first (high > medium > low)', () => {
      const sorted = sortTasksByPriority(mockTasks);
      expect(sorted[0].priority).toBe('high');
      expect(sorted[1].priority).toBe('high');
      expect(sorted[2].priority).toBe('medium');
      expect(sorted[3].priority).toBe('low');
    });

    it('within same priority, sorts by closest deadline first', () => {
      const sorted = sortTasksByPriority(mockTasks);
      const highPriorityTasks = sorted.filter(t => t.priority === 'high');
      expect(highPriorityTasks[0].id).toBe('3'); // Closer deadline
      expect(highPriorityTasks[1].id).toBe('2'); // Farther deadline
    });

    it('places tasks with deadlines before tasks without deadlines', () => {
      const tasksWithSamePriority: Task[] = [
        {
          id: '1',
          title: 'No deadline',
          status: 'todo',
          priority: 'medium',
          created_at: '2024-01-10T10:00:00Z',
          updated_at: '2024-01-10T10:00:00Z',
        },
        {
          id: '2',
          title: 'Has deadline',
          status: 'todo',
          priority: 'medium',
          due_date: '2024-01-20T12:00:00Z',
          created_at: '2024-01-10T10:00:00Z',
          updated_at: '2024-01-10T10:00:00Z',
        },
      ];
      const sorted = sortTasksByPriority(tasksWithSamePriority);
      expect(sorted[0].id).toBe('2'); // Has deadline
    });

    it('does not mutate original array', () => {
      const original = [...mockTasks];
      sortTasksByPriority(mockTasks);
      expect(mockTasks).toEqual(original);
    });

    it('sorts by creation date when priority and deadline are equal', () => {
      const tasksWithSamePriorityAndNoDeadline: Task[] = [
        {
          id: '1',
          title: 'Older task',
          status: 'todo',
          priority: 'medium',
          created_at: '2024-01-10T10:00:00Z',
          updated_at: '2024-01-10T10:00:00Z',
        },
        {
          id: '2',
          title: 'Newer task',
          status: 'todo',
          priority: 'medium',
          created_at: '2024-01-12T10:00:00Z',
          updated_at: '2024-01-12T10:00:00Z',
        },
      ];
      const sorted = sortTasksByPriority(tasksWithSamePriorityAndNoDeadline);
      expect(sorted[0].id).toBe('2'); // Newer first
    });
  });

  describe('filterTasks', () => {
    const mockTasks: Task[] = [
      {
        id: '1',
        title: 'High priority todo task',
        description: 'Important work',
        status: 'todo',
        priority: 'high',
        category: 'required_personal_action',
        due_date: '2024-01-20T12:00:00Z',
        created_at: '2024-01-10T10:00:00Z',
        updated_at: '2024-01-10T10:00:00Z',
        email_id: 'email1',
        tags: ['urgent', 'work'],
      },
      {
        id: '2',
        title: 'Medium priority in-progress task',
        description: 'Ongoing project',
        status: 'in-progress',
        priority: 'medium',
        category: 'team_action',
        due_date: '2024-01-25T12:00:00Z',
        created_at: '2024-01-12T10:00:00Z',
        updated_at: '2024-01-13T10:00:00Z',
        email_id: 'email2',
        tags: ['project'],
      },
      {
        id: '3',
        title: 'Low priority done task',
        description: 'Completed task',
        status: 'done',
        priority: 'low',
        category: 'fyi',
        due_date: '2024-01-14T12:00:00Z', // Past due (overdue)
        created_at: '2024-01-11T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
        tags: ['info'],
      },
    ];

    it('filters by status', () => {
      const filters: TaskFilter = { status: 'todo' };
      const result = filterTasks(mockTasks, filters);
      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('1');
    });

    it('filters by priority', () => {
      const filters: TaskFilter = { priority: 'high' };
      const result = filterTasks(mockTasks, filters);
      expect(result).toHaveLength(1);
      expect(result[0].priority).toBe('high');
    });

    it('filters by category', () => {
      const filters: TaskFilter = { category: 'team_action' };
      const result = filterTasks(mockTasks, filters);
      expect(result).toHaveLength(1);
      expect(result[0].category).toBe('team_action');
    });

    it('filters by search in title', () => {
      const filters: TaskFilter = { search: 'high' };
      const result = filterTasks(mockTasks, filters);
      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('1');
    });

    it('filters by search in description', () => {
      const filters: TaskFilter = { search: 'project' };
      const result = filterTasks(mockTasks, filters);
      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('2');
    });

    it('filters by search in tags', () => {
      const filters: TaskFilter = { search: 'urgent' };
      const result = filterTasks(mockTasks, filters);
      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('1');
    });

    it('filters by due date range', () => {
      const filters: TaskFilter = {
        due_date_from: '2024-01-19T00:00:00Z',
        due_date_to: '2024-01-26T00:00:00Z',
      };
      const result = filterTasks(mockTasks, filters);
      expect(result).toHaveLength(2); // Tasks 1 and 2
    });

    it('filters by overdue status', () => {
      vi.setSystemTime(new Date('2024-01-15T12:00:00Z'));
      const filters: TaskFilter = { overdue: true };
      const result = filterTasks(mockTasks, filters);
      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('3'); // Past due date
      vi.useRealTimers();
    });

    it('filters by email_id', () => {
      const filters: TaskFilter = { email_id: 'email1' };
      const result = filterTasks(mockTasks, filters);
      expect(result).toHaveLength(1);
      expect(result[0].email_id).toBe('email1');
    });

    it('filters by tags', () => {
      const filters: TaskFilter = { tags: ['work'] };
      const result = filterTasks(mockTasks, filters);
      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('1');
    });

    it('applies multiple filters together', () => {
      const filters: TaskFilter = {
        status: 'todo',
        priority: 'high',
        category: 'required_personal_action',
      };
      const result = filterTasks(mockTasks, filters);
      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('1');
    });

    it('returns all tasks with empty filter', () => {
      const result = filterTasks(mockTasks, {});
      expect(result).toHaveLength(3);
    });

    it('returns empty array when no matches', () => {
      const filters: TaskFilter = { status: 'review' };
      const result = filterTasks(mockTasks, filters);
      expect(result).toHaveLength(0);
    });
  });

  describe('getTaskStats', () => {
    beforeEach(() => {
      vi.setSystemTime(new Date('2024-01-15T12:00:00Z'));
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    const mockTasks: Task[] = [
      {
        id: '1',
        title: 'Task 1',
        status: 'todo',
        priority: 'high',
        created_at: '2024-01-10T10:00:00Z',
        updated_at: '2024-01-10T10:00:00Z',
      },
      {
        id: '2',
        title: 'Task 2',
        status: 'in-progress',
        priority: 'high',
        due_date: '2024-01-14T12:00:00Z', // Overdue
        created_at: '2024-01-11T10:00:00Z',
        updated_at: '2024-01-11T10:00:00Z',
      },
      {
        id: '3',
        title: 'Task 3',
        status: 'done',
        priority: 'medium',
        created_at: '2024-01-12T10:00:00Z',
        updated_at: '2024-01-13T10:00:00Z',
      },
      {
        id: '4',
        title: 'Task 4',
        status: 'done',
        priority: 'low',
        created_at: '2024-01-13T10:00:00Z',
        updated_at: '2024-01-14T10:00:00Z',
      },
      {
        id: '5',
        title: 'Task 5',
        status: 'review',
        priority: 'medium',
        created_at: '2024-01-14T10:00:00Z',
        updated_at: '2024-01-14T10:00:00Z',
      },
    ];

    it('calculates total tasks correctly', () => {
      const stats = getTaskStats(mockTasks);
      expect(stats.total).toBe(5);
    });

    it('calculates completed tasks correctly', () => {
      const stats = getTaskStats(mockTasks);
      expect(stats.completed).toBe(2);
    });

    it('calculates overdue tasks correctly', () => {
      const stats = getTaskStats(mockTasks);
      expect(stats.overdue).toBe(1);
    });

    it('calculates high priority tasks correctly', () => {
      const stats = getTaskStats(mockTasks);
      expect(stats.highPriority).toBe(2);
    });

    it('calculates tasks by status correctly', () => {
      const stats = getTaskStats(mockTasks);
      expect(stats.byStatus.todo).toBe(1);
      expect(stats.byStatus['in-progress']).toBe(1);
      expect(stats.byStatus.review).toBe(1);
      expect(stats.byStatus.done).toBe(2);
    });

    it('calculates tasks by priority correctly', () => {
      const stats = getTaskStats(mockTasks);
      expect(stats.byPriority.high).toBe(2);
      expect(stats.byPriority.medium).toBe(2);
      expect(stats.byPriority.low).toBe(1);
    });

    it('calculates completion rate correctly', () => {
      const stats = getTaskStats(mockTasks);
      expect(stats.completionRate).toBe(40); // 2/5 = 40%
    });

    it('handles empty task list', () => {
      const stats = getTaskStats([]);
      expect(stats.total).toBe(0);
      expect(stats.completed).toBe(0);
      expect(stats.completionRate).toBe(0);
    });

    it('handles 100% completion', () => {
      const allCompletedTasks: Task[] = [
        {
          id: '1',
          title: 'Task 1',
          status: 'done',
          priority: 'high',
          created_at: '2024-01-10T10:00:00Z',
          updated_at: '2024-01-10T10:00:00Z',
        },
        {
          id: '2',
          title: 'Task 2',
          status: 'done',
          priority: 'medium',
          created_at: '2024-01-11T10:00:00Z',
          updated_at: '2024-01-11T10:00:00Z',
        },
      ];
      const stats = getTaskStats(allCompletedTasks);
      expect(stats.completionRate).toBe(100);
    });
  });

  describe('createTaskFromEmail', () => {
    it('creates task with basic information', () => {
      const result = createTaskFromEmail('email123', 'Test Email Subject');
      expect(result.title).toBe('Test Email Subject');
      expect(result.email_id).toBe('email123');
      expect(result.category).toBe('required_action');
    });

    it('truncates long subject to 100 characters', () => {
      const longSubject = 'A'.repeat(150);
      const result = createTaskFromEmail('email123', longSubject);
      expect(result.title).toHaveLength(104); // 100 + '...'
      expect(result.title.endsWith('...')).toBe(true);
    });

    it('includes email body in description', () => {
      const result = createTaskFromEmail('email123', 'Subject', 'Email body content');
      expect(result.description).toBe('Email body content');
    });

    it('truncates long body to 500 characters', () => {
      const longBody = 'B'.repeat(600);
      const result = createTaskFromEmail('email123', 'Subject', longBody);
      expect(result.description).toHaveLength(504); // 500 + '...'
      expect(result.description!.endsWith('...')).toBe(true);
    });

    it('sets high priority for urgent keywords', () => {
      const result1 = createTaskFromEmail('email123', 'URGENT: Action Required');
      expect(result1.priority).toBe('high');

      const result2 = createTaskFromEmail('email123', 'Subject', 'This is ASAP critical');
      expect(result2.priority).toBe('high');

      const result3 = createTaskFromEmail('email123', 'EMERGENCY situation');
      expect(result3.priority).toBe('high');
    });

    it('sets low priority for FYI keywords', () => {
      const result1 = createTaskFromEmail('email123', 'FYI: Update');
      expect(result1.priority).toBe('low');

      const result2 = createTaskFromEmail('email123', 'Newsletter: Latest Info');
      expect(result2.priority).toBe('low');
    });

    it('sets medium priority by default', () => {
      const result = createTaskFromEmail('email123', 'Normal Email Subject');
      expect(result.priority).toBe('medium');
    });

    it('is case-insensitive for keyword detection', () => {
      const result1 = createTaskFromEmail('email123', 'urgent notification');
      expect(result1.priority).toBe('high');

      const result2 = createTaskFromEmail('email123', 'FYI update');
      expect(result2.priority).toBe('low');
    });

    it('checks both subject and body for keywords', () => {
      const result = createTaskFromEmail('email123', 'Normal Subject', 'URGENT action needed');
      expect(result.priority).toBe('high');
    });

    it('handles undefined body gracefully', () => {
      const result = createTaskFromEmail('email123', 'Subject');
      expect(result.description).toBeUndefined();
      expect(result.priority).toBe('medium');
    });
  });
});
