// Authentication API service for T1 backend integration
import { apiSlice } from './api';
import type { User, UserCreate, UserLogin, Token } from '@/types/auth';

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

    // User login
    login: builder.mutation<Token, UserLogin>({
      query: (credentials) => ({
        url: '/auth/login',
        method: 'POST',
        body: credentials,
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
  useLoginMutation,
  useRefreshTokenMutation,
  useGetCurrentUserQuery,
  useLogoutMutation,
} = authApi;
