/**
 * Processing API Client for Email Processing Pipeline
 * 
 * This module provides API client functions for managing email processing
 * pipelines including starting processing, monitoring status, and handling
 * real-time updates via WebSocket connections.
 */

export interface ProcessingJob {
  id: string;
  type: 'email_analysis' | 'task_extraction' | 'categorization';
  emailId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled' | 'retrying';
  progress: {
    step: string;
    percentage: number;
    message: string;
    startedAt?: string;
    updatedAt?: string;
  };
  result?: any;
  error?: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  retryCount: number;
  maxRetries: number;
}

export interface ProcessingPipeline {
  id: string;
  emailIds: string[];
  userId: string;
  jobs: ProcessingJob[];
  overallProgress: number;
  status: 'running' | 'completed' | 'failed' | 'cancelled' | 'paused';
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
}

export interface StartProcessingRequest {
  email_ids: string[];
  priority?: 'low' | 'medium' | 'high' | 'urgent';
}

export interface ProcessingStatusResponse {
  pipeline_id: string;
  status: string;
  overall_progress: number;
  email_count: number;
  jobs_completed: number;
  jobs_failed: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface JobStatusResponse {
  job_id: string;
  type: string;
  email_id: string;
  status: string;
  progress_percentage: number;
  progress_message: string;
  error?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface ProcessingStats {
  processing_stats: {
    total_pipelines: number;
    active_pipelines: number;
    completed_pipelines: number;
    worker_status: string;
  };
  websocket_stats: {
    websocket_manager: string;
    connections: {
      total_connections: number;
      connected_users: number;
      active_pipeline_subscriptions: number;
      users_with_pipeline_subscriptions: number;
    };
    features: {
      real_time_updates: boolean;
      pipeline_subscriptions: boolean;
      job_progress_tracking: boolean;
      error_notifications: boolean;
    };
  };
}

// Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WEBSOCKET_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

/**
 * Get authentication headers for API requests
 */
function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('auth_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
  };
}

/**
 * Handle API response and check for errors
 */
async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Processing API Client Class
 */
export class ProcessingApi {
  private baseUrl: string;
  private wsUrl: string;

  constructor(baseUrl: string = API_BASE_URL, wsUrl: string = WEBSOCKET_URL) {
    this.baseUrl = baseUrl;
    this.wsUrl = wsUrl;
  }

  /**
   * Start email processing pipeline
   */
  async startProcessing(request: StartProcessingRequest): Promise<{ 
    pipeline_id: string; 
    status: string; 
    email_count: number; 
    message: string; 
  }> {
    const response = await fetch(`${this.baseUrl}/api/processing/start`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });

    return handleApiResponse(response);
  }

  /**
   * Get processing pipeline status
   */
  async getProcessingStatus(pipelineId: string): Promise<ProcessingStatusResponse> {
    const response = await fetch(`${this.baseUrl}/api/processing/${pipelineId}/status`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    return handleApiResponse(response);
  }

  /**
   * Get all jobs in a pipeline
   */
  async getPipelineJobs(pipelineId: string): Promise<JobStatusResponse[]> {
    const response = await fetch(`${this.baseUrl}/api/processing/${pipelineId}/jobs`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    return handleApiResponse(response);
  }

  /**
   * Cancel processing pipeline
   */
  async cancelProcessing(pipelineId: string): Promise<{ message: string }> {
    const response = await fetch(`${this.baseUrl}/api/processing/${pipelineId}/cancel`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });

    return handleApiResponse(response);
  }

  /**
   * Get processing system statistics
   */
  async getProcessingStats(): Promise<ProcessingStats> {
    const response = await fetch(`${this.baseUrl}/api/processing/stats`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    return handleApiResponse(response);
  }

  /**
   * Create WebSocket URL for pipeline-specific updates
   */
  getWebSocketUrl(pipelineId: string, userId: string): string {
    return `${this.wsUrl}/api/processing/ws/${pipelineId}?user_id=${userId}`;
  }

  /**
   * Create WebSocket URL for general processing updates
   */
  getGeneralWebSocketUrl(userId: string): string {
    return `${this.wsUrl}/api/processing/ws?user_id=${userId}`;
  }
}

/**
 * Offline Queue Manager for processing requests
 */
export class OfflineProcessingQueue {
  private queue: StartProcessingRequest[] = [];
  private storageKey = 'processing_offline_queue';

  constructor() {
    this.loadQueue();
  }

  /**
   * Add processing request to offline queue
   */
  addToQueue(request: StartProcessingRequest): void {
    this.queue.push({
      ...request,
      // Add timestamp for ordering
      timestamp: Date.now(),
    } as any);
    this.saveQueue();
  }

  /**
   * Get all queued requests
   */
  getQueue(): StartProcessingRequest[] {
    return [...this.queue];
  }

  /**
   * Remove request from queue
   */
  removeFromQueue(index: number): void {
    this.queue.splice(index, 1);
    this.saveQueue();
  }

  /**
   * Clear entire queue
   */
  clearQueue(): void {
    this.queue = [];
    this.saveQueue();
  }

  /**
   * Process all queued requests when online
   */
  async processQueue(api: ProcessingApi): Promise<{
    successful: number;
    failed: { request: StartProcessingRequest; error: string }[];
  }> {
    const results = {
      successful: 0,
      failed: [] as { request: StartProcessingRequest; error: string }[],
    };

    for (const request of this.queue) {
      try {
        await api.startProcessing(request);
        results.successful++;
      } catch (error) {
        results.failed.push({
          request,
          error: error instanceof Error ? error.message : 'Unknown error',
        });
      }
    }

    // Clear successfully processed requests
    this.queue = this.queue.filter((_, index) => 
      results.failed.some(failed => failed.request === this.queue[index])
    );
    this.saveQueue();

    return results;
  }

  /**
   * Check if queue has pending requests
   */
  hasPendingRequests(): boolean {
    return this.queue.length > 0;
  }

  /**
   * Get queue size
   */
  getQueueSize(): number {
    return this.queue.length;
  }

  private saveQueue(): void {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.queue));
    } catch (error) {
      console.error('Failed to save offline queue:', error);
    }
  }

  private loadQueue(): void {
    try {
      const saved = localStorage.getItem(this.storageKey);
      if (saved) {
        this.queue = JSON.parse(saved);
      }
    } catch (error) {
      console.error('Failed to load offline queue:', error);
      this.queue = [];
    }
  }
}

// Create singleton instances
export const processingApi = new ProcessingApi();
export const offlineProcessingQueue = new OfflineProcessingQueue();

// Helper functions for common operations
export const ProcessingUtils = {
  /**
   * Format processing status for display
   */
  formatStatus(status: string): string {
    return status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ');
  },

  /**
   * Get status color for UI
   */
  getStatusColor(status: string): string {
    switch (status) {
      case 'running':
      case 'processing':
        return '#007AFF';
      case 'completed':
        return '#34C759';
      case 'failed':
        return '#FF3B30';
      case 'cancelled':
        return '#8E8E93';
      case 'paused':
        return '#FF9500';
      default:
        return '#8E8E93';
    }
  },

  /**
   * Calculate estimated completion time
   */
  estimateCompletionTime(pipeline: ProcessingStatusResponse): string | null {
    if (pipeline.status === 'completed' || pipeline.status === 'failed') {
      return null;
    }

    if (pipeline.overall_progress === 0) {
      return 'Calculating...';
    }

    // Simple estimation based on progress
    const timeElapsed = pipeline.started_at 
      ? Date.now() - new Date(pipeline.started_at).getTime()
      : 0;
    
    if (timeElapsed === 0) {
      return 'Calculating...';
    }

    const estimatedTotal = (timeElapsed / pipeline.overall_progress) * 100;
    const remaining = estimatedTotal - timeElapsed;

    if (remaining <= 0) {
      return 'Almost done...';
    }

    const minutes = Math.ceil(remaining / (1000 * 60));
    return minutes === 1 ? '1 minute' : `${minutes} minutes`;
  },

  /**
   * Check if processing can be cancelled
   */
  canCancel(status: string): boolean {
    return ['running', 'queued', 'processing'].includes(status);
  },

  /**
   * Check if processing can be retried
   */
  canRetry(status: string): boolean {
    return ['failed', 'cancelled'].includes(status);
  },
};