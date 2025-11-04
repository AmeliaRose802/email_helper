package models

import "time"

// Email represents an email message
type Email struct {
	ID               string    `json:"id"`
	Subject          string    `json:"subject"`
	Sender           string    `json:"sender"`
	Recipient        string    `json:"recipient,omitempty"`
	Body             string    `json:"body"`
	Content          string    `json:"content,omitempty"`
	ReceivedTime     time.Time `json:"received_time,omitempty"`
	Date             time.Time `json:"date"`
	IsRead           bool      `json:"is_read"`
	HasAttachments   bool      `json:"has_attachments"`
	Importance       string    `json:"importance"`
	Categories       []string  `json:"categories"`
	ConversationID   string    `json:"conversation_id,omitempty"`
	ConversationCount int      `json:"conversation_count,omitempty"`

	// AI Classification
	AICategory    string  `json:"ai_category,omitempty"`
	AIConfidence  float64 `json:"ai_confidence,omitempty"`
	AIReasoning   string  `json:"ai_reasoning,omitempty"`
	OneLineSummary string `json:"one_line_summary,omitempty"`

	// User correction
	Category string `json:"category,omitempty"`
}

// EmailListResponse represents paginated email list
type EmailListResponse struct {
	Emails  []Email `json:"emails"`
	Total   int     `json:"total"`
	Offset  int     `json:"offset"`
	Limit   int     `json:"limit"`
	HasMore bool    `json:"has_more"`
}

// EmailOperationResponse represents result of email operation
type EmailOperationResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	EmailID string `json:"email_id"`
}

// EmailFolderResponse represents list of email folders
type EmailFolderResponse struct {
	Folders []EmailFolder `json:"folders"`
	Total   int           `json:"total"`
}

// EmailFolder represents an email folder
type EmailFolder struct {
	Name          string `json:"name"`
	UnreadCount   int    `json:"unread_count"`
	TotalCount    int    `json:"total_count"`
	FolderPath    string `json:"folder_path,omitempty"`
}

// ConversationResponse represents an email conversation thread
type ConversationResponse struct {
	ConversationID string  `json:"conversation_id"`
	Emails         []Email `json:"emails"`
	Total          int     `json:"total"`
}

// UpdateClassificationRequest represents classification update
type UpdateClassificationRequest struct {
	Category         string `json:"category"`
	ApplyToOutlook   bool   `json:"apply_to_outlook"`
}

// CategoryFolderMapping maps categories to folders
type CategoryFolderMapping struct {
	Category      string `json:"category"`
	FolderName    string `json:"folder_name"`
	StaysInInbox  bool   `json:"stays_in_inbox"`
}

// BulkApplyRequest for bulk operations
type BulkApplyRequest struct {
	EmailIDs       []string `json:"email_ids"`
	ApplyToOutlook bool     `json:"apply_to_outlook"`
}

// BulkApplyResponse response from bulk operations
type BulkApplyResponse struct {
	Success    bool     `json:"success"`
	Processed  int      `json:"processed"`
	Successful int      `json:"successful"`
	Failed     int      `json:"failed"`
	Errors     []string `json:"errors,omitempty"`
}

// SyncEmailRequest for syncing emails to database
type SyncEmailRequest struct {
	Emails []Email `json:"emails"`
}

// EmailBatch for batch processing
type EmailBatch struct {
	Emails []interface{} `json:"emails"` // Can be Email objects or just IDs
}

// EmailBatchResult result of batch processing
type EmailBatchResult struct {
	ProcessedCount  int                      `json:"processed_count"`
	SuccessfulCount int                      `json:"successful_count"`
	FailedCount     int                      `json:"failed_count"`
	Results         []EmailProcessingResult  `json:"results"`
	Errors          []string                 `json:"errors,omitempty"`
}

// EmailProcessingResult individual email processing result
type EmailProcessingResult struct {
	EmailID     string        `json:"email_id"`
	Category    string        `json:"category"`
	Confidence  float64       `json:"confidence"`
	Reasoning   string        `json:"reasoning"`
	ActionItems []string      `json:"action_items"`
	Priority    string        `json:"priority"`
	Error       string        `json:"error,omitempty"`
}
