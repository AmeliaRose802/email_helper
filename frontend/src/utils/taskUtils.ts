import { parseISO, isAfter, differenceInHours } from 'date-fns';
import type { Task, TaskFilter } from '@/types/task';

export const isTaskOverdue = (task: Task): boolean => {
  if (!task.due_date) return false;
  return isAfter(new Date(), parseISO(task.due_date));
};

export const getTaskUrgencyLevel = (task: Task): 'overdue' | 'urgent' | 'warning' | 'normal' => {
  if (!task.due_date) return 'normal';
  
  const deadline = parseISO(task.due_date);
  const now = new Date();
  
  if (isAfter(now, deadline)) return 'overdue';
  
  const hoursLeft = differenceInHours(deadline, now);
  if (hoursLeft <= 24) return 'urgent';
  if (hoursLeft <= 72) return 'warning';
  return 'normal';
};

export const sortTasksByPriority = (tasks: Task[]): Task[] => {
  const priorityOrder = { high: 3, medium: 2, low: 1 };
  return [...tasks].sort((a, b) => {
    // First sort by priority
    const priorityCompare = priorityOrder[b.priority] - priorityOrder[a.priority];
    if (priorityCompare !== 0) return priorityCompare;
    
    // Then by deadline (overdue first, then closest deadline)
    if (a.due_date && b.due_date) {
      const aDeadline = parseISO(a.due_date);
      const bDeadline = parseISO(b.due_date);
      return aDeadline.getTime() - bDeadline.getTime();
    }
    if (a.due_date && !b.due_date) return -1;
    if (!a.due_date && b.due_date) return 1;
    
    // Finally by creation date (newest first)
    return parseISO(b.created_at).getTime() - parseISO(a.created_at).getTime();
  });
};

export const filterTasks = (tasks: Task[], filters: TaskFilter): Task[] => {
  return tasks.filter(task => {
    // Status filter
    if (filters.status && task.status !== filters.status) {
      return false;
    }
    
    // Priority filter
    if (filters.priority && task.priority !== filters.priority) {
      return false;
    }
    
    // Category filter
    if (filters.category && task.category !== filters.category) {
      return false;
    }
    
    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      const matchesTitle = task.title.toLowerCase().includes(searchLower);
      const matchesDescription = task.description?.toLowerCase().includes(searchLower);
      const matchesTags = task.tags?.some(tag => tag.toLowerCase().includes(searchLower));
      
      if (!matchesTitle && !matchesDescription && !matchesTags) {
        return false;
      }
    }
    
    // Due date range filters
    if (filters.due_date_from && task.due_date) {
      if (parseISO(task.due_date) < parseISO(filters.due_date_from)) {
        return false;
      }
    }
    
    if (filters.due_date_to && task.due_date) {
      if (parseISO(task.due_date) > parseISO(filters.due_date_to)) {
        return false;
      }
    }
    
    // Overdue filter
    if (filters.overdue && !isTaskOverdue(task)) {
      return false;
    }
    
    // Email ID filter
    if (filters.email_id && task.email_id !== filters.email_id) {
      return false;
    }
    
    // Tags filter
    if (filters.tags && filters.tags.length > 0) {
      if (!task.tags || !filters.tags.some(tag => task.tags!.includes(tag))) {
        return false;
      }
    }
    
    return true;
  });
};

export const getTaskStats = (tasks: Task[]) => {
  const total = tasks.length;
  const completed = tasks.filter(t => t.status === 'done').length;
  const overdue = tasks.filter(isTaskOverdue).length;
  const highPriority = tasks.filter(t => t.priority === 'high').length;
  
  const byStatus = {
    todo: tasks.filter(t => t.status === 'todo').length,
    'in-progress': tasks.filter(t => t.status === 'in-progress').length,
    review: tasks.filter(t => t.status === 'review').length,
    done: completed,
  };
  
  const byPriority = {
    high: highPriority,
    medium: tasks.filter(t => t.priority === 'medium').length,
    low: tasks.filter(t => t.priority === 'low').length,
  };
  
  const completionRate = total > 0 ? (completed / total) * 100 : 0;
  
  return {
    total,
    completed,
    overdue,
    highPriority,
    byStatus,
    byPriority,
    completionRate,
  };
};

export const createTaskFromEmail = (emailId: string, emailSubject: string, emailBody?: string) => {
  // Extract potential task information from email
  const title = emailSubject.length > 100 ? 
    `${emailSubject.substring(0, 100)}...` : 
    emailSubject;
    
  const description = emailBody ? 
    (emailBody.length > 500 ? `${emailBody.substring(0, 500)}...` : emailBody) :
    undefined;
    
  // Determine priority based on keywords
  let priority: 'high' | 'medium' | 'low' = 'medium';
  const urgentKeywords = ['urgent', 'asap', 'immediate', 'critical', 'emergency'];
  const lowKeywords = ['fyi', 'info', 'update', 'newsletter'];
  
  const emailText = `${emailSubject} ${emailBody || ''}`.toLowerCase();
  
  if (urgentKeywords.some(keyword => emailText.includes(keyword))) {
    priority = 'high';
  } else if (lowKeywords.some(keyword => emailText.includes(keyword))) {
    priority = 'low';
  }
  
  return {
    title,
    description,
    priority,
    category: 'required_action' as const,
    email_id: emailId,
  };
};