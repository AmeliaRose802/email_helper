// Integration tests for backend API connectivity
// These tests require the backend server to be running on localhost:8000
import { describe, it, expect, beforeAll, afterAll } from 'vitest';

const BACKEND_URL = 'http://localhost:8000';
const API_TIMEOUT = 5000;

// Helper function to check if backend is available
async function isBackendAvailable(): Promise<boolean> {
  try {
    const response = await fetch(`${BACKEND_URL}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(API_TIMEOUT),
    });
    return response.ok;
  } catch {
    return false;
  }
}

describe('Backend API Integration Tests', () => {
  let backendAvailable = false;

  beforeAll(async () => {
    backendAvailable = await isBackendAvailable();
    if (!backendAvailable) {
      console.warn(
        '⚠️  Backend server not available at http://localhost:8000. Integration tests will be skipped.'
      );
      console.warn('   To run these tests, start the backend server: python run_backend.py');
    }
  });

  afterAll(() => {
    if (backendAvailable) {
      console.log('✅ Backend integration tests completed successfully');
    }
  });

  describe('Health Check (T1-T4 Backend Status)', () => {
    it('should connect to backend health endpoint', { skip: !backendAvailable }, async () => {
      const response = await fetch(`${BACKEND_URL}/health`);
      expect(response.ok).toBe(true);

      const data = await response.json();
      expect(data).toHaveProperty('status');
      expect(data).toHaveProperty('service');
      expect(data).toHaveProperty('version');
      expect(data.status).toBe('healthy');
    });
  });

  describe('Authentication API (T1)', () => {
    it('should have auth endpoints available', { skip: !backendAvailable }, async () => {
      // Test registration endpoint exists (should return 422 for empty body)
      const registerResponse = await fetch(`${BACKEND_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      expect([400, 422]).toContain(registerResponse.status);

      // Test login endpoint exists (should return 422 for empty body)
      const loginResponse = await fetch(`${BACKEND_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      expect([400, 422]).toContain(loginResponse.status);
    });
  });

  describe('Email API (T2)', () => {
    it('should have email endpoints available', { skip: !backendAvailable }, async () => {
      // Test emails endpoint exists (should return 403/401 without auth)
      const emailsResponse = await fetch(`${BACKEND_URL}/api/emails`);
      expect([401, 403]).toContain(emailsResponse.status);
    });
  });

  describe('AI Processing API (T3)', () => {
    it('should have AI endpoints available', { skip: !backendAvailable }, async () => {
      // Test AI classify endpoint exists (should return 403/401 without auth)
      const classifyResponse = await fetch(`${BACKEND_URL}/api/ai/classify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      expect([401, 403, 422]).toContain(classifyResponse.status);
    });
  });

  describe('Task Management API (T4)', () => {
    it('should have task endpoints available', { skip: !backendAvailable }, async () => {
      // Test tasks endpoint exists (should return 403/401 without auth)
      const tasksResponse = await fetch(`${BACKEND_URL}/api/tasks`);
      expect([401, 403]).toContain(tasksResponse.status);
    });
  });

  describe('API Documentation', () => {
    it('should have OpenAPI docs available', { skip: !backendAvailable }, async () => {
      const docsResponse = await fetch(`${BACKEND_URL}/docs`);
      expect(docsResponse.ok).toBe(true);

      const redocResponse = await fetch(`${BACKEND_URL}/redoc`);
      expect(redocResponse.ok).toBe(true);
    });
  });
});

// Export helper for use in other tests
export { isBackendAvailable, BACKEND_URL };