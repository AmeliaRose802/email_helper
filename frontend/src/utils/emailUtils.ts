// Email utility functions
import { format, isToday, isYesterday } from 'date-fns';
import type { Email, EmailFilter } from '@/types/email';

export const formatEmailDate = (dateString: string): string => {
  const date = new Date(dateString);
  
  if (isToday(date)) {
    return format(date, 'HH:mm');
  } else if (isYesterday(date)) {
    return 'Yesterday';
  } else {
    return format(date, 'MMM d');
  }
};

export const getEmailPreview = (body: string, maxLength: number = 150): string => {
  // Strip HTML tags and normalize whitespace
  const plainText = body.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
  
  if (plainText.length <= maxLength) {
    return plainText;
  }
  
  return plainText.substring(0, maxLength) + '...';
};

export const getCategoryColor = (category: string): string => {
  const colors: Record<string, string> = {
    required_action: '#dc3545', // Red - urgent
    team_action: '#fd7e14',     // Orange - important
    job_listing: '#6f42c1',     // Purple - opportunities
    optional_event: '#20c997',  // Teal - optional
    fyi: '#6c757d',            // Gray - informational
    newsletter: '#0dcaf0',      // Light blue - newsletters
  };
  
  return colors[category] || '#6c757d';
};

export const getCategoryLabel = (category: string): string => {
  const labels: Record<string, string> = {
    required_action: 'Action Required',
    team_action: 'Team Action',
    job_listing: 'Job Listing',
    optional_event: 'Optional Event',
    fyi: 'FYI',
    newsletter: 'Newsletter',
  };
  
  return labels[category] || category;
};

export const getPriorityIcon = (priority: string): string => {
  const icons: Record<string, string> = {
    high: '🔴',
    medium: '🟡',
    low: '🟢',
  };
  
  return icons[priority] || '';
};

export const filterEmails = (emails: Email[], filters: EmailFilter): Email[] => {
  return emails.filter((email) => {
    // Filter by read status
    if (filters.is_read !== undefined && email.is_read !== filters.is_read) {
      return false;
    }
    
    // Filter by sender
    if (filters.sender && !email.sender.toLowerCase().includes(filters.sender.toLowerCase())) {
      return false;
    }
    
    // Filter by subject
    if (filters.subject && !email.subject.toLowerCase().includes(filters.subject.toLowerCase())) {
      return false;
    }
    
    // Filter by importance
    if (filters.importance && email.importance !== filters.importance) {
      return false;
    }
    
    // Filter by attachments
    if (filters.has_attachments !== undefined && email.has_attachments !== filters.has_attachments) {
      return false;
    }
    
    // Filter by folder
    if (filters.folder && email.folder_name !== filters.folder) {
      return false;
    }
    
    // Filter by date range
    if (filters.date_from || filters.date_to) {
      const emailDate = new Date(email.date);
      
      if (filters.date_from && emailDate < new Date(filters.date_from)) {
        return false;
      }
      
      if (filters.date_to && emailDate > new Date(filters.date_to)) {
        return false;
      }
    }
    
    return true;
  });
};

export const sortEmails = (emails: Email[], sortBy: 'date' | 'sender' | 'subject' = 'date', sortOrder: 'asc' | 'desc' = 'desc'): Email[] => {
  return [...emails].sort((a, b) => {
    let comparison = 0;
    
    switch (sortBy) {
      case 'date':
        comparison = new Date(a.date).getTime() - new Date(b.date).getTime();
        break;
      case 'sender':
        comparison = a.sender.localeCompare(b.sender);
        break;
      case 'subject':
        comparison = a.subject.localeCompare(b.subject);
        break;
    }
    
    return sortOrder === 'desc' ? -comparison : comparison;
  });
};

export const getEmailSearchScore = (email: Email, query: string): number => {
  if (!query.trim()) {
    return 0;
  }
  
  const normalizedQuery = query.toLowerCase();
  let score = 0;
  
  // Subject match (highest weight)
  if (email.subject.toLowerCase().includes(normalizedQuery)) {
    score += 10;
  }
  
  // Sender match
  if (email.sender.toLowerCase().includes(normalizedQuery)) {
    score += 5;
  }
  
  // Body match
  if (email.body.toLowerCase().includes(normalizedQuery)) {
    score += 3;
  }
  
  return score;
};

export const searchEmails = (emails: Email[], query: string): Email[] => {
  if (!query.trim()) {
    return emails;
  }
  
  return emails
    .map(email => ({
      email,
      score: getEmailSearchScore(email, query)
    }))
    .filter(item => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .map(item => item.email);
};