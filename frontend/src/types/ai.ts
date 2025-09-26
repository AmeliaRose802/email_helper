// AI processing types for T3 backend integration

export interface EmailClassification {
  email_id: string;
  category: 'required_action' | 'team_action' | 'job_listing' | 'optional_event' | 'fyi';
  confidence: number;
  reasoning: string;
  action_required?: string;
  due_date?: string;
  priority: 'high' | 'medium' | 'low';
}

export interface BatchClassificationRequest {
  email_ids: string[];
  classification_type?: string;
  use_cache?: boolean;
}

export interface BatchClassificationResponse {
  classifications: EmailClassification[];
  processing_time: number;
  cached_results: number;
  new_classifications: number;
}

export interface ActionItem {
  id: string;
  email_id: string;
  subject: string;
  sender: string;
  action_required: string;
  due_date?: string;
  priority: 'high' | 'medium' | 'low';
  category: string;
  explanation: string;
  task_id?: string;
  batch_count: number;
}

export interface AIProcessingState {
  isProcessing: boolean;
  classifications: EmailClassification[];
  actionItems: ActionItem[];
  error: string | null;
  lastProcessed: string | null;
}

export interface AIAnalysisRequest {
  email_ids: string[];
  analysis_type: 'classification' | 'action_items' | 'summary';
  options?: {
    include_reasoning?: boolean;
    use_cache?: boolean;
    priority_threshold?: number;
  };
}
