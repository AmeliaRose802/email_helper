// Common API types and interfaces

export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: number;
}

export interface ApiError {
  error: boolean;
  message: string;
  status_code: number;
  details?: Record<string, unknown>;
}

export interface PaginationParams {
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  items: T[];
  total_count: number;
  page: number;
  per_page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface HealthCheck {
  status: string;
  service: string;
  version: string;
  database: string;
  debug: boolean;
}

export interface ApiEndpoints {
  // Auth endpoints (T1)
  login: '/auth/login';
  register: '/auth/register';
  refresh: '/auth/refresh';
  me: '/auth/me';

  // Email endpoints (T2)
  emails: '/api/emails';
  emailById: '/api/emails/{id}';
  emailStats: '/api/emails/stats';
  emailBatch: '/api/emails/batch';

  // AI endpoints (T3)
  aiClassify: '/api/ai/classify';
  aiAnalyzeBatch: '/api/ai/analyze-batch';
  aiActionItems: '/api/ai/action-items';

  // Task endpoints (T4)
  tasks: '/api/tasks';
  taskById: '/api/tasks/{id}';
  taskStats: '/api/tasks/stats';
  taskBatch: '/api/tasks/batch';

  // Health
  health: '/health';
}
