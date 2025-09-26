// Task management types for T4 backend integration

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority: 'high' | 'medium' | 'low';
  category: 'required_action' | 'team_action' | 'job_listing' | 'optional_event' | 'fyi';
  due_date?: string;
  created_at: string;
  updated_at: string;
  email_id?: string;
  metadata?: Record<string, unknown>;
  tags?: string[];
}

export interface TaskCreate {
  title: string;
  description?: string;
  priority: 'high' | 'medium' | 'low';
  category: 'required_action' | 'team_action' | 'job_listing' | 'optional_event' | 'fyi';
  due_date?: string;
  email_id?: string;
  metadata?: Record<string, unknown>;
  tags?: string[];
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  status?: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority?: 'high' | 'medium' | 'low';
  due_date?: string;
  metadata?: Record<string, unknown>;
  tags?: string[];
}

export interface TaskFilter {
  status?: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority?: 'high' | 'medium' | 'low';
  category?: 'required_action' | 'team_action' | 'job_listing' | 'optional_event' | 'fyi';
  due_date_from?: string;
  due_date_to?: string;
  email_id?: string;
  tags?: string[];
}

export interface TaskListResponse {
  tasks: Task[];
  total_count: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export interface TaskStats {
  total_tasks: number;
  pending_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
  tasks_by_priority: Record<string, number>;
  tasks_by_category: Record<string, number>;
}

export interface TaskState {
  tasks: Task[];
  currentTask: Task | null;
  isLoading: boolean;
  error: string | null;
  filters: TaskFilter;
  stats: TaskStats | null;
}
