// Authentication API service for T1 backend integration
import { apiSlice } from './api';
import type { User, UserCreate, Token } from '@/types/auth';

export const authApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    // User registration
    register: builder.mutation<User, UserCreate>({
      query: (userData) => ({
        url: '/auth/register',
        method: 'POST',
        body: userData,
      }),
      invalidatesTags: ['User'],
    }),

    // Initiate OAuth login
    initiateLogin: builder.query<{ auth_url: string; state: string }, void>({
      query: () => '/auth/login',
    }),

    // User login with Azure token
    login: builder.mutation<Token, { access_token: string }>({
      query: (tokenData) => ({
        url: '/auth/login',
        method: 'POST',
        body: tokenData,
      }),
      invalidatesTags: ['User'],
    }),

    // Token refresh
    refreshToken: builder.mutation<{ access_token: string }, void>({
      query: () => ({
        url: '/auth/refresh',
        method: 'POST',
      }),
    }),

    // Get current user
    getCurrentUser: builder.query<User, void>({
      query: () => '/auth/me',
      providesTags: ['User'],
    }),

    // Logout (invalidate session)
    logout: builder.mutation<void, void>({
      query: () => ({
        url: '/auth/logout',
        method: 'POST',
      }),
      invalidatesTags: ['User'],
    }),
  }),
});

export const {
  useRegisterMutation,
  useInitiateLoginQuery,
  useLoginMutation,
  useRefreshTokenMutation,
  useGetCurrentUserQuery,
  useLogoutMutation,
} = authApi;
