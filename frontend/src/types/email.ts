// Email types for T2 backend integration

export interface Email {
  id: string;
  subject: string;
  sender: string;
  recipient: string;
  date: string;
  body: string;
  html_body?: string;
  has_attachments: boolean;
  is_read: boolean;
  importance: 'Low' | 'Normal' | 'High';
  categories?: string[]; // Outlook categories
  conversation_id?: string;
  folder_name?: string;
  // AI Classification fields
  ai_category?: 'required_personal_action' | 'team_action' | 'optional_action' | 'job_listing' | 'optional_event' | 'work_relevant' | 'fyi' | 'newsletter' | 'spam_to_delete';
  ai_confidence?: number;
  ai_reasoning?: string;
  classification_status?: 'pending' | 'classifying' | 'classified' | 'error';
  one_line_summary?: string; // AI-generated one-line summary
  holistic_classification?: HolisticClassification; // Holistic inbox analysis results
}

export interface EmailListResponse {
  emails: Email[];
  total: number;  // Backend returns 'total', not 'total_count'
  offset: number;
  limit: number;
  has_more: boolean;
}

export interface EmailFilter {
  folder?: string;
  sender?: string;
  subject?: string;
  date_from?: string;
  date_to?: string;
  is_read?: boolean;
  has_attachments?: boolean;
  importance?: 'Low' | 'Normal' | 'High';
}

export interface EmailBatchOperation {
  email_ids: string[];
  operation: 'mark_read' | 'mark_unread' | 'delete' | 'move';
  target_folder?: string;
}

export interface EmailStats {
  total_emails: number;
  unread_emails: number;
  emails_by_folder: Record<string, number>;
  emails_by_sender: Record<string, number>;
}

export interface HolisticClassification {
  action_type?: 'required_personal_action' | 'team_action' | 'optional_action';
  priority?: 'high' | 'medium' | 'low';
  topic?: string;
  deadline?: string;
  why_relevant?: string;
  blocking_others?: boolean;
  is_superseded?: boolean;
  superseded_by?: string;
  is_duplicate?: boolean;
  canonical_email_id?: string;
  is_expired?: boolean;
}
