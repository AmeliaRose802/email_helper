import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  formatEmailDate,
  getEmailPreview,
  getCategoryColor,
  getCategoryLabel,
  getPriorityIcon,
  filterEmails,
  sortEmails,
  getEmailSearchScore,
  searchEmails,
} from './emailUtils';
import type { Email, EmailFilter } from '@/types/email';

describe('emailUtils', () => {
  describe('formatEmailDate', () => {
    beforeEach(() => {
      // Mock the current date to a fixed value for consistent testing
      vi.setSystemTime(new Date('2024-01-15T14:00:00Z'));
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('returns "No date" for empty string', () => {
      expect(formatEmailDate('')).toBe('No date');
    });

    it('returns "Invalid date" for invalid date string', () => {
      expect(formatEmailDate('not-a-date')).toBe('Invalid date');
    });

    it('formats today\'s date with time in PST', () => {
      // Create a date for today at specific time
      const todayDate = new Date('2024-01-15T10:00:00-08:00'); // 10 AM PST
      const result = formatEmailDate(todayDate.toISOString());
      expect(result).toMatch(/\d{1,2}:\d{2} (AM|PM)/);
    });

    it('returns "Yesterday" for yesterday\'s date', () => {
      const yesterdayDate = new Date('2024-01-14T10:00:00-08:00');
      expect(formatEmailDate(yesterdayDate.toISOString())).toBe('Yesterday');
    });

    it('formats older dates as "MMM d"', () => {
      const olderDate = new Date('2024-01-10T10:00:00-08:00');
      expect(formatEmailDate(olderDate.toISOString())).toBe('Jan 10');
    });

    it('handles timezone conversion to PST', () => {
      // UTC date that converts to PST
      const utcDate = new Date('2024-01-15T18:00:00Z'); // 6 PM UTC
      const result = formatEmailDate(utcDate.toISOString());
      // Should be formatted as PST time (10 AM PST)
      expect(result).toMatch(/\d{1,2}:\d{2} (AM|PM)/);
    });

    it('handles invalid date gracefully', () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const result = formatEmailDate('2024-13-45'); // Invalid month/day
      expect(result).toBe('Invalid date');
      consoleWarnSpy.mockRestore();
    });
  });

  describe('getEmailPreview', () => {
    it('strips HTML tags from email body', () => {
      const html = '<p>Hello <strong>world</strong></p>';
      expect(getEmailPreview(html)).toBe('Hello world');
    });

    it('normalizes whitespace', () => {
      const text = 'Multiple    spaces\n\nand\n\nnewlines';
      expect(getEmailPreview(text)).toBe('Multiple spaces and newlines');
    });

    it('returns full text if shorter than maxLength', () => {
      const text = 'Short email';
      expect(getEmailPreview(text, 50)).toBe('Short email');
    });

    it('truncates text longer than maxLength', () => {
      const longText = 'A'.repeat(200);
      const result = getEmailPreview(longText, 150);
      expect(result).toHaveLength(154); // 150 + '...'
      expect(result.endsWith('...')).toBe(true);
    });

    it('uses default maxLength of 150', () => {
      const longText = 'A'.repeat(200);
      const result = getEmailPreview(longText);
      expect(result).toHaveLength(154);
    });

    it('handles empty string', () => {
      expect(getEmailPreview('')).toBe('');
    });

    it('handles complex HTML with nested tags', () => {
      const html = '<div><p>Paragraph 1</p><ul><li>Item 1</li><li>Item 2</li></ul></div>';
      expect(getEmailPreview(html)).toBe('Paragraph 1 Item 1 Item 2');
    });
  });

  describe('getCategoryColor', () => {
    it('returns red for required_personal_action', () => {
      expect(getCategoryColor('required_personal_action')).toBe('#dc3545');
    });

    it('returns orange for team_action', () => {
      expect(getCategoryColor('team_action')).toBe('#fd7e14');
    });

    it('returns yellow for optional_action', () => {
      expect(getCategoryColor('optional_action')).toBe('#ffc107');
    });

    it('returns purple for job_listing', () => {
      expect(getCategoryColor('job_listing')).toBe('#6f42c1');
    });

    it('returns teal for optional_event', () => {
      expect(getCategoryColor('optional_event')).toBe('#20c997');
    });

    it('returns blue for work_relevant', () => {
      expect(getCategoryColor('work_relevant')).toBe('#0d6efd');
    });

    it('returns gray for fyi', () => {
      expect(getCategoryColor('fyi')).toBe('#6c757d');
    });

    it('returns light blue for newsletter', () => {
      expect(getCategoryColor('newsletter')).toBe('#0dcaf0');
    });

    it('returns red for spam_to_delete', () => {
      expect(getCategoryColor('spam_to_delete')).toBe('#dc3545');
    });

    it('returns gray for unknown category', () => {
      expect(getCategoryColor('unknown_category')).toBe('#6c757d');
    });

    it('handles required_action alias', () => {
      expect(getCategoryColor('required_action')).toBe('#dc3545');
    });
  });

  describe('getCategoryLabel', () => {
    it('returns correct label for required_personal_action', () => {
      expect(getCategoryLabel('required_personal_action')).toBe('🔴 Action Required');
    });

    it('returns correct label for team_action', () => {
      expect(getCategoryLabel('team_action')).toBe('👥 Team Action');
    });

    it('returns correct label for optional_action', () => {
      expect(getCategoryLabel('optional_action')).toBe('📋 Optional');
    });

    it('returns correct label for job_listing', () => {
      expect(getCategoryLabel('job_listing')).toBe('💼 Job Listing');
    });

    it('formats unknown categories with title case', () => {
      expect(getCategoryLabel('custom_category')).toBe('Custom Category');
    });

    it('handles single word categories', () => {
      expect(getCategoryLabel('urgent')).toBe('Urgent');
    });
  });

  describe('getPriorityIcon', () => {
    it('returns red circle for high priority', () => {
      expect(getPriorityIcon('high')).toBe('🔴');
    });

    it('returns yellow circle for medium priority', () => {
      expect(getPriorityIcon('medium')).toBe('🟡');
    });

    it('returns green circle for low priority', () => {
      expect(getPriorityIcon('low')).toBe('🟢');
    });

    it('returns empty string for unknown priority', () => {
      expect(getPriorityIcon('unknown')).toBe('');
    });
  });

  describe('filterEmails', () => {
    const mockEmails: Email[] = [
      {
        id: '1',
        subject: 'Test Email 1',
        sender: 'alice@example.com',
        recipient: 'me@example.com',
        date: '2024-01-15T10:00:00Z',
        body: 'Body 1',
        is_read: false,
        importance: 'High',
        has_attachments: true,
        folder_name: 'Inbox',
      },
      {
        id: '2',
        subject: 'Test Email 2',
        sender: 'bob@example.com',
        recipient: 'me@example.com',
        date: '2024-01-14T10:00:00Z',
        body: 'Body 2',
        is_read: true,
        importance: 'Normal',
        has_attachments: false,
        folder_name: 'Sent',
      },
      {
        id: '3',
        subject: 'Important Meeting',
        sender: 'charlie@example.com',
        recipient: 'me@example.com',
        date: '2024-01-13T10:00:00Z',
        body: 'Body 3',
        is_read: false,
        importance: 'Low',
        has_attachments: true,
        folder_name: 'Inbox',
      },
    ] as Email[];

    it('filters by read status', () => {
      const filters: EmailFilter = { is_read: true };
      const result = filterEmails(mockEmails, filters);
      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('2');
    });

    it('filters by sender (case-insensitive)', () => {
      const filters: EmailFilter = { sender: 'ALICE' };
      const result = filterEmails(mockEmails, filters);
      expect(result).toHaveLength(1);
      expect(result[0].sender).toBe('alice@example.com');
    });

    it('filters by subject (case-insensitive)', () => {
      const filters: EmailFilter = { subject: 'meeting' };
      const result = filterEmails(mockEmails, filters);
      expect(result).toHaveLength(1);
      expect(result[0].subject).toBe('Important Meeting');
    });

    it('filters by importance', () => {
      const filters: EmailFilter = { importance: 'High' };
      const result = filterEmails(mockEmails, filters);
      expect(result).toHaveLength(1);
      expect(result[0].importance).toBe('High');
    });

    it('filters by attachments', () => {
      const filters: EmailFilter = { has_attachments: true };
      const result = filterEmails(mockEmails, filters);
      expect(result).toHaveLength(2);
    });

    it('filters by folder', () => {
      const filters: EmailFilter = { folder: 'Inbox' };
      const result = filterEmails(mockEmails, filters);
      expect(result).toHaveLength(2);
    });

    it('filters by date range', () => {
      const filters: EmailFilter = {
        date_from: '2024-01-14T00:00:00Z',
        date_to: '2024-01-16T00:00:00Z',
      };
      const result = filterEmails(mockEmails, filters);
      expect(result).toHaveLength(2);
    });

    it('applies multiple filters together', () => {
      const filters: EmailFilter = {
        is_read: false,
        has_attachments: true,
        folder: 'Inbox',
      };
      const result = filterEmails(mockEmails, filters);
      expect(result).toHaveLength(2);
    });

    it('returns all emails with empty filter', () => {
      const result = filterEmails(mockEmails, {});
      expect(result).toHaveLength(3);
    });
  });

  describe('sortEmails', () => {
    const mockEmails: Email[] = [
      {
        id: '1',
        subject: 'Zebra',
        sender: 'charlie@example.com',
        recipient: 'me@example.com',
        date: '2024-01-15T10:00:00Z',
        body: 'Body 1',
        is_read: false,
        importance: 'Normal',
        has_attachments: false,
      },
      {
        id: '2',
        subject: 'Apple',
        sender: 'alice@example.com',
        recipient: 'me@example.com',
        date: '2024-01-14T10:00:00Z',
        body: 'Body 2',
        is_read: false,
        importance: 'Normal',
        has_attachments: false,
      },
      {
        id: '3',
        subject: 'Banana',
        sender: 'bob@example.com',
        recipient: 'me@example.com',
        date: '2024-01-16T10:00:00Z',
        body: 'Body 3',
        is_read: false,
        importance: 'Normal',
        has_attachments: false,
      },
    ] as Email[];

    it('sorts by date descending (default)', () => {
      const result = sortEmails(mockEmails);
      expect(result[0].id).toBe('3'); // Latest date
      expect(result[2].id).toBe('2'); // Earliest date
    });

    it('sorts by date ascending', () => {
      const result = sortEmails(mockEmails, 'date', 'asc');
      expect(result[0].id).toBe('2'); // Earliest date
      expect(result[2].id).toBe('3'); // Latest date
    });

    it('sorts by sender ascending', () => {
      const result = sortEmails(mockEmails, 'sender', 'asc');
      expect(result[0].sender).toBe('alice@example.com');
      expect(result[2].sender).toBe('charlie@example.com');
    });

    it('sorts by sender descending', () => {
      const result = sortEmails(mockEmails, 'sender', 'desc');
      expect(result[0].sender).toBe('charlie@example.com');
      expect(result[2].sender).toBe('alice@example.com');
    });

    it('sorts by subject ascending', () => {
      const result = sortEmails(mockEmails, 'subject', 'asc');
      expect(result[0].subject).toBe('Apple');
      expect(result[2].subject).toBe('Zebra');
    });

    it('sorts by subject descending', () => {
      const result = sortEmails(mockEmails, 'subject', 'desc');
      expect(result[0].subject).toBe('Zebra');
      expect(result[2].subject).toBe('Apple');
    });

    it('does not mutate original array', () => {
      const original = [...mockEmails];
      sortEmails(mockEmails, 'subject', 'asc');
      expect(mockEmails).toEqual(original);
    });
  });

  describe('getEmailSearchScore', () => {
    const mockEmail: Email = {
      id: '1',
      subject: 'Important Meeting Tomorrow',
      sender: 'alice@example.com',
      recipient: 'me@example.com',
      body: 'Please review the meeting agenda',
      date: '2024-01-15T10:00:00Z',
      is_read: false,
      importance: 'Normal',
      has_attachments: false,
    } as Email;

    it('returns 0 for empty query', () => {
      expect(getEmailSearchScore(mockEmail, '')).toBe(0);
    });

    it('returns 10 for subject match', () => {
      expect(getEmailSearchScore(mockEmail, 'meeting')).toBe(13); // 10 (subject) + 3 (body)
    });

    it('returns 5 for sender match', () => {
      expect(getEmailSearchScore(mockEmail, 'alice')).toBe(5);
    });

    it('returns 3 for body match', () => {
      expect(getEmailSearchScore(mockEmail, 'agenda')).toBe(3);
    });

    it('accumulates scores for multiple matches', () => {
      const score = getEmailSearchScore(mockEmail, 'meeting');
      expect(score).toBeGreaterThanOrEqual(10); // At least subject match
    });

    it('is case-insensitive', () => {
      expect(getEmailSearchScore(mockEmail, 'MEETING')).toBe(13);
    });
  });

  describe('searchEmails', () => {
    const mockEmails: Email[] = [
      {
        id: '1',
        subject: 'Project Update',
        sender: 'alice@example.com',
        recipient: 'me@example.com',
        body: 'Latest project status',
        date: '2024-01-15T10:00:00Z',
        is_read: false,
        importance: 'Normal',
        has_attachments: false,
      },
      {
        id: '2',
        subject: 'Meeting Notes',
        sender: 'bob@example.com',
        recipient: 'me@example.com',
        body: 'Discussion about the project',
        date: '2024-01-14T10:00:00Z',
        is_read: false,
        importance: 'Normal',
        has_attachments: false,
      },
      {
        id: '3',
        subject: 'Lunch Plans',
        sender: 'charlie@example.com',
        recipient: 'me@example.com',
        body: 'Where should we go?',
        date: '2024-01-13T10:00:00Z',
        is_read: false,
        importance: 'Normal',
        has_attachments: false,
      },
    ] as Email[];

    it('returns all emails for empty query', () => {
      const result = searchEmails(mockEmails, '');
      expect(result).toHaveLength(3);
    });

    it('filters emails based on query', () => {
      const result = searchEmails(mockEmails, 'project');
      expect(result).toHaveLength(2);
    });

    it('sorts results by relevance score', () => {
      const result = searchEmails(mockEmails, 'project');
      // Email with 'project' in subject should rank higher than body match
      expect(result[0].id).toBe('1'); // Subject match
      expect(result[1].id).toBe('2'); // Body match
    });

    it('returns empty array when no matches', () => {
      const result = searchEmails(mockEmails, 'nonexistent');
      expect(result).toHaveLength(0);
    });

    it('is case-insensitive', () => {
      const result = searchEmails(mockEmails, 'PROJECT');
      expect(result).toHaveLength(2);
    });

    it('handles whitespace in query', () => {
      const result = searchEmails(mockEmails, '  project  ');
      expect(result).toHaveLength(2);
    });
  });
});
