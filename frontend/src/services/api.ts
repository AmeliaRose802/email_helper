// RTK Query API configuration for backend integration
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { apiConfig, debugLog } from '@/config/api';

// Base query with authentication (disabled for desktop app)
const baseQuery = fetchBaseQuery({
  baseUrl: apiConfig.baseURL, // Use configured backend URL
  prepareHeaders: (headers) => {
    // Skip authentication for desktop app - always allow requests
    headers.set('content-type', 'application/json');
    
    // Debug logging
    debugLog('API Request Headers', {
      desktopMode: true,
      authDisabled: true,
      headers: Object.fromEntries(headers.entries()),
    });
    
    return headers;
  },
});

// Base query without token refresh (not needed for desktop app)
const baseQueryWithReauth = baseQuery;

// Main API slice
export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['User', 'Email', 'Task', 'AIClassification'],
  // Keep cached data for 5 minutes after component unmounts
  keepUnusedDataFor: 300, // 5 minutes in seconds
  // Prevent automatic refetching on component remount
  refetchOnMountOrArgChange: false,
  // Prevent automatic refetching on window focus
  refetchOnFocus: false,
  // Prevent automatic refetching when network reconnects
  refetchOnReconnect: false,
  endpoints: (builder) => ({
    // Health check endpoint
    healthCheck: builder.query<
      { status: string; service: string; version: string; database: string; debug: boolean },
      void
    >({
      query: () => '/health',
    }),
  }),
});

export const { useHealthCheckQuery } = apiSlice;

// Log API configuration on initialization
debugLog('API Slice initialized', {
  baseUrl: apiConfig.baseURL,
  localhostMode: apiConfig.localhostMode,
});
