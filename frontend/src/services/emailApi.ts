// Email API service for T2 backend integration
import { apiSlice } from './api';
import type {
  Email,
  EmailListResponse,
  EmailFilter,
  EmailBatchOperation,
  EmailStats,
  PaginationParams,
} from '@/types';

export const emailApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    // Get paginated list of emails
    getEmails: builder.query<EmailListResponse, PaginationParams & EmailFilter>({
      query: (params) => ({
        url: '/api/emails',
        params,
      }),
      providesTags: (result) =>
        result?.emails
          ? [
              ...result.emails.map(({ id }) => ({ type: 'Email' as const, id })),
              { type: 'Email', id: 'LIST' },
            ]
          : [{ type: 'Email', id: 'LIST' }],
    }),

    // Get individual email by ID
    getEmailById: builder.query<Email, string>({
      query: (id) => `/api/emails/${id}`,
      providesTags: (_result, _error, id) => [{ type: 'Email', id }],
    }),

    // Get email statistics
    getEmailStats: builder.query<EmailStats, void>({
      query: () => '/api/emails/stats',
      providesTags: [{ type: 'Email', id: 'STATS' }],
    }),

    // Batch operations on emails
    batchEmailOperation: builder.mutation<
      { success: boolean; processed_count: number; message: string },
      EmailBatchOperation
    >({
      query: (operation) => ({
        url: '/api/emails/batch',
        method: 'POST',
        body: operation,
      }),
      invalidatesTags: [
        { type: 'Email', id: 'LIST' },
        { type: 'Email', id: 'STATS' },
      ],
    }),

    // Mark email as read
    markEmailRead: builder.mutation<void, { id: string; read: boolean }>({
      query: ({ id, read }) => ({
        url: `/api/emails/${id}/read`,
        method: 'PUT',
        body: { is_read: read },
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: 'Email', id },
        { type: 'Email', id: 'LIST' },
        { type: 'Email', id: 'STATS' },
      ],
    }),

    // Delete email
    deleteEmail: builder.mutation<void, string>({
      query: (id) => ({
        url: `/api/emails/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, id) => [
        { type: 'Email', id },
        { type: 'Email', id: 'LIST' },
        { type: 'Email', id: 'STATS' },
      ],
    }),

    // Move email to folder
    moveEmail: builder.mutation<void, { id: string; folder: string }>({
      query: ({ id, folder }) => ({
        url: `/api/emails/${id}/move`,
        method: 'PUT',
        body: { folder_name: folder },
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: 'Email', id },
        { type: 'Email', id: 'LIST' },
      ],
    }),
  }),
});

export const {
  useGetEmailsQuery,
  useGetEmailByIdQuery,
  useGetEmailStatsQuery,
  useBatchEmailOperationMutation,
  useMarkEmailReadMutation,
  useDeleteEmailMutation,
  useMoveEmailMutation,
} = emailApi;
