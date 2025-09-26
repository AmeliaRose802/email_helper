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
  categories?: string[];
  conversation_id?: string;
  folder_name?: string;
}

export interface EmailListResponse {
  emails: Email[];
  total_count: number;
  page: number;
  per_page: number;
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
