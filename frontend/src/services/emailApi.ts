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
      transformResponse: (response: EmailListResponse) => {
        console.log('[getEmails] Received emails from API:', {
          count: response.emails.length,
          total: response.total,
          sampleClassifications: response.emails.slice(0, 3).map(e => ({
            id: e.id.substring(0, 30),
            subject: e.subject,
            ai_category: e.ai_category,
            categories: e.categories
          }))
        });
        return response;
      },
      providesTags: (result) =>
        result?.emails
          ? [
              ...result.emails.map(({ id }) => ({ type: 'Email' as const, id })),
              { type: 'Email', id: 'LIST' },
            ]
          : [{ type: 'Email', id: 'LIST' }],
      // Keep data fresh for 60 seconds, then refetch when tags are invalidated
      keepUnusedDataFor: 60,
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
      // Cache email details for 5 minutes to prevent redundant fetches
      keepUnusedDataFor: 300,
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
      // Optimistic updates for immediate UI feedback
      async onQueryStarted({ emailId, category }, { dispatch, queryFulfilled, getState }) {
        console.log('[Classification Update] Starting update:', { emailId: emailId.substring(0, 30), category });
        const patches: any[] = [];
        
        // Update individual email cache
        try {
          const patch1 = dispatch(
            emailApi.util.updateQueryData('getEmailById', emailId, (draft) => {
              console.log('[Classification Update] Updating detail cache:', { 
                emailId: emailId.substring(0, 30),
                oldCategory: draft.ai_category,
                newCategory: category 
              });
              draft.ai_category = category as any;
              if (!draft.categories) draft.categories = [];
              if (!draft.categories.includes(category)) {
                draft.categories.push(category);
              }
            })
          );
          patches.push(patch1);
        } catch (e) {
          console.log('[Classification Update] Detail cache not found (expected if not viewing email)');
        }
        
        // Update all email list caches
        const state: any = getState();
        const queries = state.api?.queries || {};
        
        console.log('[Classification Update] Active queries:', Object.keys(queries).filter(k => k.startsWith('getEmails(')));
        
        Object.entries(queries).forEach(([key, value]: [string, any]) => {
          if (key.startsWith('getEmails(') && value?.data?.emails) {
            const args = value.originalArgs;
            try {
              const patch = dispatch(
                emailApi.util.updateQueryData('getEmails', args, (draft) => {
                  const email = draft.emails?.find(e => e.id === emailId);
                  if (email) {
                    console.log('[Classification Update] Updating list cache:', {
                      emailId: emailId.substring(0, 30),
                      oldCategory: email.ai_category,
                      newCategory: category,
                      queryKey: key
                    });
                    email.ai_category = category as any;
                    if (!email.categories) email.categories = [];
                    if (!email.categories.includes(category)) {
                      email.categories.push(category);
                    }
                  } else {
                    console.warn('[Classification Update] Email not found in list cache:', { emailId: emailId.substring(0, 30), queryKey: key });
                  }
                })
              );
              patches.push(patch);
            } catch (e) {
              console.warn('[Classification Update] Failed to update email list cache:', e);
            }
          }
        });
        
        console.log('[Classification Update] Applied', patches.length, 'optimistic updates');
        
        try {
          const result = await queryFulfilled;
          console.log('[Classification Update] ✅ Success:', result);
        } catch (error) {
          console.error('[Classification Update] ❌ Failed, reverting updates:', error);
          // Revert all optimistic updates on error
          patches.forEach(patch => {
            try {
              patch.undo();
            } catch (e) {
              console.warn('[Classification Update] Failed to undo patch:', e);
            }
          });
        }
      },
      // Invalidate caches as fallback
      invalidatesTags: (_result, _error, { emailId }) => [
        { type: 'Email', id: emailId },
        { type: 'Email', id: 'LIST' },
        { type: 'Email', id: 'SEARCH' },
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
      { emails: Email[] }
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
