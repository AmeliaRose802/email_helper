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
    // Classify single email by email data
    classifyEmail: builder.mutation<
      { category: string; confidence: number; reasoning: string; alternative_categories: string[]; processing_time: number; one_line_summary?: string },
      { subject: string; sender: string; content: string; context?: string }
    >({
      query: (emailData) => ({
        url: '/api/ai/classify',
        method: 'POST',
        body: emailData,
      }),
      invalidatesTags: [{ type: 'AIClassification', id: 'LIST' }],
    }),

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
