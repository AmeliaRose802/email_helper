/**
 * API Configuration for Email Helper Frontend
 * 
 * Centralizes API endpoint configuration and environment-based settings.
 * Uses Vite environment variables to configure the backend connection.
 */

// Get environment variables with fallback defaults
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT = Number(import.meta.env.VITE_API_TIMEOUT) || 30000;
const LOCALHOST_MODE = import.meta.env.VITE_LOCALHOST_MODE === 'true';
const DEBUG_LOGGING = import.meta.env.VITE_DEBUG_LOGGING === 'true';

/**
 * API configuration object
 */
export const apiConfig = {
  /**
   * Base URL for the backend API
   * In development, this points to the local FastAPI server
   */
  baseURL: API_BASE_URL,

  /**
   * Request timeout in milliseconds
   */
  timeout: API_TIMEOUT,

  /**
   * Default headers for all API requests
   */
  headers: {
    'Content-Type': 'application/json',
  },

  /**
   * Whether the application is running in localhost development mode
   */
  localhostMode: LOCALHOST_MODE,

  /**
   * Whether to enable debug logging
   */
  debugLogging: DEBUG_LOGGING,
};

/**
 * API endpoint paths
 * These are relative paths that will be combined with the baseURL
 */
export const apiEndpoints = {
  // Health check
  health: '/health',

  // Authentication endpoints (T1)
  auth: {
    login: '/auth/login',
    register: '/auth/register',
    refresh: '/auth/refresh',
    logout: '/auth/logout',
    me: '/auth/me',
    callback: '/auth/callback',
  },

  // Email endpoints (T2)
  emails: {
    list: '/api/emails',
    byId: (id: string) => `/api/emails/${id}`,
    stats: '/api/emails/stats',
    batch: '/api/emails/batch',
  },

  // AI Processing endpoints (T3)
  ai: {
    classify: '/api/ai/classify',
    analyzeBatch: '/api/ai/analyze-batch',
    actionItems: '/api/ai/action-items',
  },

  // Task Management endpoints (T4)
  tasks: {
    list: '/api/tasks',
    byId: (id: string) => `/api/tasks/${id}`,
    stats: '/api/tasks/stats',
    batch: '/api/tasks/batch',
  },

  // Processing Pipeline endpoints (T9)
  processing: {
    start: '/api/processing/start',
    status: (pipelineId: string) => `/api/processing/status/${pipelineId}`,
    jobs: (pipelineId: string) => `/api/processing/jobs/${pipelineId}`,
    stats: '/api/processing/stats',
  },
};

/**
 * Build a full URL from a path
 * @param path - API endpoint path
 * @returns Full URL to the API endpoint
 */
export function buildApiUrl(path: string): string {
  // Remove leading slash from path if present to avoid double slashes
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  const baseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
  return `${baseUrl}/${cleanPath}`;
}

/**
 * Log debug information if debug logging is enabled
 * @param message - Debug message
 * @param data - Optional data to log
 */
export function debugLog(message: string, data?: unknown): void {
  if (DEBUG_LOGGING) {
    console.log(`[API Debug] ${message}`, data ?? '');
  }
}

/**
 * Check if the backend is available
 * @returns Promise that resolves to true if backend is reachable
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(buildApiUrl(apiEndpoints.health), {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    });
    return response.ok;
  } catch (error) {
    debugLog('Backend health check failed', error);
    return false;
  }
}

// Log configuration in development mode
if (DEBUG_LOGGING) {
  console.log('[API Config] Configuration loaded:', {
    baseURL: API_BASE_URL,
    timeout: API_TIMEOUT,
    localhostMode: LOCALHOST_MODE,
    debugLogging: DEBUG_LOGGING,
  });
}

export default apiConfig;
