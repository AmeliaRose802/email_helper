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

    // Search emails
    searchEmails: builder.query<EmailListResponse, { query: string; page?: number; per_page?: number }>({
      query: ({ query, page = 1, per_page = 20 }) => ({
        url: '/api/emails/search',
        params: { q: query, page, per_page },
      }),
      providesTags: (result) =>
        result?.emails
          ? [
              ...result.emails.map(({ id }) => ({ type: 'Email' as const, id })),
              { type: 'Email', id: 'SEARCH' },
            ]
          : [{ type: 'Email', id: 'SEARCH' }],
    }),

    // Get individual email by ID
    getEmailById: builder.query<Email, string>({
      query: (id) => `/api/emails/${id}`,
      providesTags: (_result, _error, id) => [{ type: 'Email', id }],
    }),

    // Get email statistics
    getEmailStats: builder.query<EmailStats, number>({
      query: (limit = 100) => `/api/emails/stats?limit=${limit}`,
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

    // Get category to folder mappings
    getCategoryMappings: builder.query<
      Array<{ category: string; folder_name: string; stays_in_inbox: boolean }>,
      void
    >({
      query: () => '/api/emails/category-mappings',
    }),

    // Update email classification
    updateEmailClassification: builder.mutation<
      { success: boolean; message: string; email_id?: string },
      { emailId: string; category: string; applyToOutlook: boolean }
    >({
      query: ({ emailId, category, applyToOutlook }) => ({
        url: `/api/emails/${emailId}/classification`,
        method: 'PUT',
        body: {
          category,
          apply_to_outlook: applyToOutlook,
        },
      }),
      // Optimistic update for better UX
      async onQueryStarted({ emailId, category }, { dispatch, queryFulfilled }) {
        // Optimistically update the individual email cache
        const patchResult = dispatch(
          emailApi.util.updateQueryData('getEmailById', emailId, (draft) => {
            draft.ai_category = category as any;
            draft.categories = [category];
          })
        );
        try {
          await queryFulfilled;
        } catch {
          // Revert on error
          patchResult.undo();
        }
      },
      invalidatesTags: (_result, _error, { emailId }) => [
        { type: 'Email', id: emailId },
        { type: 'Email', id: 'LIST' },
      ],
    }),

    // Bulk apply classifications to Outlook
    bulkApplyToOutlook: builder.mutation<
      { success: boolean; processed: number; successful: number; failed: number; errors: string[] },
      { emailIds: string[]; applyToOutlook?: boolean }
    >({
      query: ({ emailIds, applyToOutlook = true }) => ({
        url: '/api/emails/bulk-apply-to-outlook',
        method: 'POST',
        body: {
          email_ids: emailIds,
          apply_to_outlook: applyToOutlook,
        },
      }),
      invalidatesTags: [
        { type: 'Email', id: 'LIST' },
        { type: 'Email', id: 'STATS' },
      ],
    }),

    // Sync classified emails to database
    syncEmailsToDatabase: builder.mutation<
      { success: boolean; synced_count: number; message: string },
      { emails: any[] }
    >({
      query: (data) => ({
        url: '/api/emails/sync-to-database',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: [
        { type: 'Email', id: 'LIST' },
        { type: 'Email', id: 'STATS' },
      ],
    }),

    // Extract tasks from emails
    extractTasksFromEmails: builder.mutation<
      { status: string; message: string; email_count: number },
      { email_ids: string[] }
    >({
      query: (data) => ({
        url: '/api/emails/extract-tasks',
        method: 'POST',
        body: {
          email_ids: data.email_ids,
          apply_to_outlook: false,
        },
      }),
      invalidatesTags: [
        { type: 'Task', id: 'LIST' },
        { type: 'Task', id: 'STATS' },
      ],
    }),
  }),
});

export const {
  useGetEmailsQuery,
  useSearchEmailsQuery,
  useGetEmailByIdQuery,
  useGetEmailStatsQuery,
  useBatchEmailOperationMutation,
  useMarkEmailReadMutation,
  useDeleteEmailMutation,
  useMoveEmailMutation,
  useGetCategoryMappingsQuery,
  useUpdateEmailClassificationMutation,
  useBulkApplyToOutlookMutation,
  useSyncEmailsToDatabaseMutation,
  useExtractTasksFromEmailsMutation,
} = emailApi;
