// Test for API configuration
import { describe, it, expect } from 'vitest';
import { apiConfig, apiEndpoints, buildApiUrl, debugLog } from '@/config/api';

describe('API Configuration', () => {
  it('should load environment variables correctly', () => {
    expect(apiConfig.baseURL).toBe('http://localhost:8000');
    expect(apiConfig.timeout).toBe(30000);
    expect(apiConfig.localhostMode).toBe(true);
    expect(apiConfig.debugLogging).toBe(true);
  });

  it('should have correct default headers', () => {
    expect(apiConfig.headers).toHaveProperty('Content-Type');
    expect(apiConfig.headers['Content-Type']).toBe('application/json');
  });

  it('should define all required endpoint paths', () => {
    expect(apiEndpoints.health).toBe('/health');
    expect(apiEndpoints.auth.login).toBe('/auth/login');
    expect(apiEndpoints.auth.register).toBe('/auth/register');
    expect(apiEndpoints.emails.list).toBe('/api/emails');
    expect(apiEndpoints.ai.classify).toBe('/api/ai/classify');
    expect(apiEndpoints.tasks.list).toBe('/api/tasks');
  });

  it('should build API URLs correctly', () => {
    const healthUrl = buildApiUrl('/health');
    expect(healthUrl).toBe('http://localhost:8000/health');

    const emailsUrl = buildApiUrl(apiEndpoints.emails.list);
    expect(emailsUrl).toBe('http://localhost:8000/api/emails');
  });

  it('should handle paths with and without leading slashes', () => {
    expect(buildApiUrl('/api/test')).toBe('http://localhost:8000/api/test');
    expect(buildApiUrl('api/test')).toBe('http://localhost:8000/api/test');
  });

  it('should handle base URL with and without trailing slashes', () => {
    const urlWithSlash = buildApiUrl('/health');
    expect(urlWithSlash).toBe('http://localhost:8000/health');
    expect(urlWithSlash).not.toContain('//health');
  });

  it('should generate dynamic endpoint paths', () => {
    const emailId = '123';
    expect(apiEndpoints.emails.byId(emailId)).toBe('/api/emails/123');

    const taskId = 'task-456';
    expect(apiEndpoints.tasks.byId(taskId)).toBe('/api/tasks/task-456');

    const pipelineId = 'pipeline-789';
    expect(apiEndpoints.processing.status(pipelineId)).toBe('/api/processing/status/pipeline-789');
  });

  it('should have debugLog function', () => {
    expect(typeof debugLog).toBe('function');
    // Should not throw
    expect(() => debugLog('Test message', { test: true })).not.toThrow();
  });
});
