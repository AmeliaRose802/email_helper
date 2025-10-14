// RTK Query API configuration for backend integration
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { BaseQueryApi, FetchArgs } from '@reduxjs/toolkit/query/react';
import type { RootState } from '@/store/store';
import { apiConfig, debugLog } from '@/config/api';

// Base query with authentication
const baseQuery = fetchBaseQuery({
  baseUrl: '/', // Proxy will handle routing to backend
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.token;
    if (token) {
      headers.set('authorization', `Bearer ${token}`);
    }
    headers.set('content-type', 'application/json');
    
    // Debug logging
    debugLog('API Request Headers', {
      hasToken: !!token,
      headers: Object.fromEntries(headers.entries()),
    });
    
    return headers;
  },
});

// Base query with token refresh logic
const baseQueryWithReauth = async (args: string | FetchArgs, api: BaseQueryApi, extraOptions: object) => {
  let result = await baseQuery(args, api, extraOptions);

  if (result.error && result.error.status === 401) {
    // Try to refresh token
    const refreshToken = (api.getState() as RootState).auth.refreshToken;
    if (refreshToken) {
      const refreshResult = await baseQuery(
        {
          url: '/auth/refresh',
          method: 'POST',
        },
        api,
        extraOptions
      );

      if (refreshResult.data) {
        // Retry original request with new token
        result = await baseQuery(args, api, extraOptions);
      } else {
        // Refresh failed, logout user
        api.dispatch({ type: 'auth/logout' });
      }
    }
  }

  return result;
};

// Main API slice
export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['User', 'Email', 'Task', 'AIClassification'],
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
