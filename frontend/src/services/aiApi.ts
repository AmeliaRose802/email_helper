// AI processing API service for T3 backend integration
import { apiSlice } from './api';
import type {
  EmailClassification,
  BatchClassificationRequest,
  BatchClassificationResponse,
  ActionItem,
  AIAnalysisRequest,
} from '@/types/ai';

export const aiApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    // Classify single email
    classifyEmail: builder.mutation<EmailClassification, { email_id: string; use_cache?: boolean }>(
      {
        query: ({ email_id, use_cache = true }) => ({
          url: '/api/ai/classify',
          method: 'POST',
          body: { email_id, use_cache },
        }),
        invalidatesTags: [{ type: 'AIClassification', id: 'LIST' }],
      }
    ),

    // Batch classify multiple emails
    classifyEmailBatch: builder.mutation<BatchClassificationResponse, BatchClassificationRequest>({
      query: (request) => ({
        url: '/api/ai/analyze-batch',
        method: 'POST',
        body: request,
      }),
      invalidatesTags: [{ type: 'AIClassification', id: 'LIST' }],
    }),

    // Get action items from emails
    getActionItems: builder.query<ActionItem[], { email_ids?: string[]; category?: string }>({
      query: (params) => ({
        url: '/api/ai/action-items',
        params,
      }),
      providesTags: [{ type: 'AIClassification', id: 'ACTION_ITEMS' }],
    }),

    // Generate email summary
    generateEmailSummary: builder.mutation<
      { summary: string; action_items: ActionItem[]; key_points: string[] },
      { email_ids: string[]; summary_type?: 'brief' | 'detailed' }
    >({
      query: (request) => ({
        url: '/api/ai/summarize',
        method: 'POST',
        body: request,
      }),
    }),

    // Get AI analysis for specific email
    analyzeEmail: builder.mutation<
      {
        classification: EmailClassification;
        action_items: ActionItem[];
        summary: string;
        key_insights: string[];
      },
      AIAnalysisRequest
    >({
      query: (request) => ({
        url: '/api/ai/analyze',
        method: 'POST',
        body: request,
      }),
      invalidatesTags: [{ type: 'AIClassification', id: 'LIST' }],
    }),

    // Get AI processing status
    getProcessingStatus: builder.query<
      {
        is_processing: boolean;
        queue_length: number;
        processed_today: number;
        last_processed: string | null;
      },
      void
    >({
      query: () => '/api/ai/status',
    }),

    // Cancel AI processing
    cancelProcessing: builder.mutation<void, void>({
      query: () => ({
        url: '/api/ai/cancel',
        method: 'POST',
      }),
    }),
  }),
});

export const {
  useClassifyEmailMutation,
  useClassifyEmailBatchMutation,
  useGetActionItemsQuery,
  useGenerateEmailSummaryMutation,
  useAnalyzeEmailMutation,
  useGetProcessingStatusQuery,
  useCancelProcessingMutation,
} = aiApi;
