/**
 * Test suite for Processing API Client
 */

import { ProcessingApi, OfflineProcessingQueue, ProcessingUtils } from '../src/services/processingApi';

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock as any;

describe('ProcessingApi', () => {
  let api: ProcessingApi;

  beforeEach(() => {
    api = new ProcessingApi('http://test-api.com', 'ws://test-ws.com');
    mockFetch.mockClear();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
  });

  describe('startProcessing', () => {
    it('should start processing successfully', async () => {
      const mockResponse = {
        pipeline_id: 'pipeline_123',
        status: 'started',
        email_count: 2,
        message: 'Processing started for 2 emails',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response);

      const request = {
        email_ids: ['email_1', 'email_2'],
        priority: 'medium' as const,
      };

      const result = await api.startProcessing(request);

      expect(mockFetch).toHaveBeenCalledWith('http://test-api.com/api/processing/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
      expect(result).toEqual(mockResponse);
    });

    it('should handle API errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: () => Promise.resolve({ message: 'Invalid request' }),
      } as Response);

      const request = { email_ids: [] };

      await expect(api.startProcessing(request)).rejects.toThrow('Invalid request');
    });

    it('should include auth token when available', async () => {
      localStorageMock.getItem.mockReturnValueOnce('test_token');

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ pipeline_id: 'test' }),
      } as Response);

      await api.startProcessing({ email_ids: ['email_1'] });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test_token',
          },
        })
      );
    });
  });

  describe('getProcessingStatus', () => {
    it('should get processing status successfully', async () => {
      const mockStatus = {
        pipeline_id: 'pipeline_123',
        status: 'running',
        overall_progress: 50,
        email_count: 2,
        jobs_completed: 1,
        jobs_failed: 0,
        created_at: '2024-01-15T10:00:00Z',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockStatus),
      } as Response);

      const result = await api.getProcessingStatus('pipeline_123');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api.com/api/processing/pipeline_123/status',
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        }
      );
      expect(result).toEqual(mockStatus);
    });
  });

  describe('getPipelineJobs', () => {
    it('should get pipeline jobs successfully', async () => {
      const mockJobs = [
        {
          job_id: 'job_1',
          type: 'email_analysis',
          email_id: 'email_1',
          status: 'completed',
          progress_percentage: 100,
          progress_message: 'Analysis completed',
          created_at: '2024-01-15T10:00:00Z',
        },
        {
          job_id: 'job_2',
          type: 'task_extraction',
          email_id: 'email_1',
          status: 'processing',
          progress_percentage: 50,
          progress_message: 'Extracting tasks...',
          created_at: '2024-01-15T10:01:00Z',
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockJobs),
      } as Response);

      const result = await api.getPipelineJobs('pipeline_123');

      expect(result).toEqual(mockJobs);
    });
  });

  describe('cancelProcessing', () => {
    it('should cancel processing successfully', async () => {
      const mockResponse = { message: 'Pipeline cancelled successfully' };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response);

      const result = await api.cancelProcessing('pipeline_123');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api.com/api/processing/pipeline_123/cancel',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        }
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getProcessingStats', () => {
    it('should get processing stats successfully', async () => {
      const mockStats = {
        processing_stats: {
          total_pipelines: 5,
          active_pipelines: 2,
          completed_pipelines: 3,
          worker_status: 'running',
        },
        websocket_stats: {
          websocket_manager: 'active',
          connections: {
            total_connections: 3,
            connected_users: 2,
            active_pipeline_subscriptions: 1,
            users_with_pipeline_subscriptions: 1,
          },
          features: {
            real_time_updates: true,
            pipeline_subscriptions: true,
            job_progress_tracking: true,
            error_notifications: true,
          },
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockStats),
      } as Response);

      const result = await api.getProcessingStats();

      expect(result).toEqual(mockStats);
    });
  });

  describe('WebSocket URLs', () => {
    it('should generate correct WebSocket URL for pipeline', () => {
      const url = api.getWebSocketUrl('pipeline_123', 'user_456');
      expect(url).toBe('ws://test-ws.com/api/processing/ws/pipeline_123?user_id=user_456');
    });

    it('should generate correct general WebSocket URL', () => {
      const url = api.getGeneralWebSocketUrl('user_456');
      expect(url).toBe('ws://test-ws.com/api/processing/ws?user_id=user_456');
    });
  });
});

describe('OfflineProcessingQueue', () => {
  let queue: OfflineProcessingQueue;

  beforeEach(() => {
    queue = new OfflineProcessingQueue();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
  });

  describe('addToQueue', () => {
    it('should add request to queue', () => {
      const request = { email_ids: ['email_1', 'email_2'] };
      
      queue.addToQueue(request);
      
      expect(queue.getQueueSize()).toBe(1);
      expect(queue.hasPendingRequests()).toBe(true);
      expect(localStorageMock.setItem).toHaveBeenCalled();
    });
  });

  describe('removeFromQueue', () => {
    it('should remove request from queue', () => {
      const request1 = { email_ids: ['email_1'] };
      const request2 = { email_ids: ['email_2'] };
      
      queue.addToQueue(request1);
      queue.addToQueue(request2);
      
      expect(queue.getQueueSize()).toBe(2);
      
      queue.removeFromQueue(0);
      
      expect(queue.getQueueSize()).toBe(1);
      expect(localStorageMock.setItem).toHaveBeenCalled();
    });
  });

  describe('clearQueue', () => {
    it('should clear entire queue', () => {
      queue.addToQueue({ email_ids: ['email_1'] });
      queue.addToQueue({ email_ids: ['email_2'] });
      
      expect(queue.getQueueSize()).toBe(2);
      
      queue.clearQueue();
      
      expect(queue.getQueueSize()).toBe(0);
      expect(queue.hasPendingRequests()).toBe(false);
    });
  });

  describe('processQueue', () => {
    it('should process all queued requests successfully', async () => {
      const mockApi = {
        startProcessing: jest.fn().mockResolvedValue({ pipeline_id: 'test' }),
      } as any;

      queue.addToQueue({ email_ids: ['email_1'] });
      queue.addToQueue({ email_ids: ['email_2'] });

      const result = await queue.processQueue(mockApi);

      expect(result.successful).toBe(2);
      expect(result.failed).toHaveLength(0);
      expect(mockApi.startProcessing).toHaveBeenCalledTimes(2);
      expect(queue.getQueueSize()).toBe(0);
    });

    it('should handle failed requests', async () => {
      const mockApi = {
        startProcessing: jest.fn()
          .mockResolvedValueOnce({ pipeline_id: 'test' })
          .mockRejectedValueOnce(new Error('API Error')),
      } as any;

      queue.addToQueue({ email_ids: ['email_1'] });
      queue.addToQueue({ email_ids: ['email_2'] });

      const result = await queue.processQueue(mockApi);

      expect(result.successful).toBe(1);
      expect(result.failed).toHaveLength(1);
      expect(result.failed[0].error).toBe('API Error');
      expect(queue.getQueueSize()).toBe(1); // Failed request remains
    });
  });

  describe('persistence', () => {
    it('should load queue from localStorage on initialization', () => {
      const savedQueue = [{ email_ids: ['email_1'] }];
      localStorageMock.getItem.mockReturnValueOnce(JSON.stringify(savedQueue));

      const newQueue = new OfflineProcessingQueue();

      expect(newQueue.getQueueSize()).toBe(1);
      expect(newQueue.getQueue()).toEqual(savedQueue);
    });

    it('should handle corrupted localStorage data', () => {
      localStorageMock.getItem.mockReturnValueOnce('invalid json');

      const newQueue = new OfflineProcessingQueue();

      expect(newQueue.getQueueSize()).toBe(0);
    });
  });
});

describe('ProcessingUtils', () => {
  describe('formatStatus', () => {
    it('should format status strings correctly', () => {
      expect(ProcessingUtils.formatStatus('running')).toBe('Running');
      expect(ProcessingUtils.formatStatus('email_analysis')).toBe('Email analysis');
      expect(ProcessingUtils.formatStatus('task_extraction')).toBe('Task extraction');
    });
  });

  describe('getStatusColor', () => {
    it('should return correct colors for statuses', () => {
      expect(ProcessingUtils.getStatusColor('running')).toBe('#007AFF');
      expect(ProcessingUtils.getStatusColor('completed')).toBe('#34C759');
      expect(ProcessingUtils.getStatusColor('failed')).toBe('#FF3B30');
      expect(ProcessingUtils.getStatusColor('cancelled')).toBe('#8E8E93');
      expect(ProcessingUtils.getStatusColor('unknown')).toBe('#8E8E93');
    });
  });

  describe('estimateCompletionTime', () => {
    it('should return null for completed pipelines', () => {
      const pipeline = {
        status: 'completed',
        overall_progress: 100,
      } as any;

      const result = ProcessingUtils.estimateCompletionTime(pipeline);
      expect(result).toBeNull();
    });

    it('should return "Calculating..." for zero progress', () => {
      const pipeline = {
        status: 'running',
        overall_progress: 0,
      } as any;

      const result = ProcessingUtils.estimateCompletionTime(pipeline);
      expect(result).toBe('Calculating...');
    });

    it('should calculate estimated time based on progress', () => {
      const now = Date.now();
      const pipeline = {
        status: 'running',
        overall_progress: 50,
        started_at: new Date(now - 60000).toISOString(), // Started 1 minute ago
      } as any;

      const result = ProcessingUtils.estimateCompletionTime(pipeline);
      expect(result).toBe('1 minute');
    });

    it('should handle edge case of almost done', () => {
      const now = Date.now();
      const pipeline = {
        status: 'running',
        overall_progress: 99,
        started_at: new Date(now - 60000).toISOString(),
      } as any;

      const result = ProcessingUtils.estimateCompletionTime(pipeline);
      expect(result).toBe('Almost done...');
    });
  });

  describe('canCancel', () => {
    it('should return true for cancellable statuses', () => {
      expect(ProcessingUtils.canCancel('running')).toBe(true);
      expect(ProcessingUtils.canCancel('queued')).toBe(true);
      expect(ProcessingUtils.canCancel('processing')).toBe(true);
    });

    it('should return false for non-cancellable statuses', () => {
      expect(ProcessingUtils.canCancel('completed')).toBe(false);
      expect(ProcessingUtils.canCancel('failed')).toBe(false);
      expect(ProcessingUtils.canCancel('cancelled')).toBe(false);
    });
  });

  describe('canRetry', () => {
    it('should return true for retryable statuses', () => {
      expect(ProcessingUtils.canRetry('failed')).toBe(true);
      expect(ProcessingUtils.canRetry('cancelled')).toBe(true);
    });

    it('should return false for non-retryable statuses', () => {
      expect(ProcessingUtils.canRetry('running')).toBe(false);
      expect(ProcessingUtils.canRetry('completed')).toBe(false);
      expect(ProcessingUtils.canRetry('processing')).toBe(false);
    });
  });
});

// Integration tests
describe('Processing API Integration', () => {
  it('should handle complete processing workflow', async () => {
    const api = new ProcessingApi();
    
    // Mock successful API responses
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          pipeline_id: 'pipeline_123',
          status: 'started',
          email_count: 2,
          message: 'Processing started',
        }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          pipeline_id: 'pipeline_123',
          status: 'running',
          overall_progress: 50,
          email_count: 2,
          jobs_completed: 3,
          jobs_failed: 0,
          created_at: '2024-01-15T10:00:00Z',
        }),
      } as Response);

    // Start processing
    const startResult = await api.startProcessing({
      email_ids: ['email_1', 'email_2'],
    });

    expect(startResult.pipeline_id).toBe('pipeline_123');

    // Get status
    const status = await api.getProcessingStatus('pipeline_123');
    expect(status.overall_progress).toBe(50);
  });

  it('should handle offline queue with API integration', async () => {
    const api = new ProcessingApi();
    const queue = new OfflineProcessingQueue();

    // Add requests to offline queue
    queue.addToQueue({ email_ids: ['email_1'] });
    queue.addToQueue({ email_ids: ['email_2'] });

    // Mock API responses
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ pipeline_id: 'test' }),
    } as Response);

    // Process queue
    const result = await queue.processQueue(api);

    expect(result.successful).toBe(2);
    expect(result.failed).toHaveLength(0);
    expect(queue.getQueueSize()).toBe(0);
  });
});

// Error handling tests
describe('Error Handling', () => {
  let api: ProcessingApi;

  beforeEach(() => {
    api = new ProcessingApi();
    mockFetch.mockClear();
  });

  it('should handle network errors', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    await expect(api.startProcessing({ email_ids: ['email_1'] }))
      .rejects.toThrow('Network error');
  });

  it('should handle HTTP errors with custom messages', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: () => Promise.resolve({ message: 'Custom error message' }),
    } as Response);

    await expect(api.getProcessingStatus('pipeline_123'))
      .rejects.toThrow('Custom error message');
  });

  it('should handle malformed JSON responses', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: () => Promise.reject(new Error('Invalid JSON')),
    } as Response);

    await expect(api.startProcessing({ email_ids: ['email_1'] }))
      .rejects.toThrow('HTTP 400: Bad Request');
  });
});