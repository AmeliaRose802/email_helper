package models

// AIClassificationRequest for email classification
type AIClassificationRequest struct {
	Subject string `json:"subject" binding:"required"`
	Sender  string `json:"sender" binding:"required"`
	Content string `json:"content" binding:"required"`
	Context string `json:"context"`
}

// AIClassificationResponse classification result
type AIClassificationResponse struct {
	Category              string   `json:"category"`
	Confidence            *float64 `json:"confidence,omitempty"`
	Reasoning             string   `json:"reasoning"`
	AlternativeCategories []string `json:"alternative_categories,omitempty"`
	ProcessingTime        float64  `json:"processing_time"`
	OneLineSummary        string   `json:"one_line_summary"`
}

// ActionItemRequest for extracting action items
type ActionItemRequest struct {
	EmailContent string `json:"email_content" binding:"required"`
	Context      string `json:"context"`
}

// ActionItemResponse action items result
type ActionItemResponse struct {
	ActionItems    []string `json:"action_items"`
	Urgency        string   `json:"urgency"`
	Deadline       *string  `json:"deadline,omitempty"`
	Confidence     float64  `json:"confidence"`
	DueDate        *string  `json:"due_date,omitempty"`
	ActionRequired *bool    `json:"action_required,omitempty"`
	Explanation    *string  `json:"explanation,omitempty"`
	Relevance      *string  `json:"relevance,omitempty"`
	Links          []string `json:"links,omitempty"`
}

// SummaryRequest for generating summaries
type SummaryRequest struct {
	EmailContent string `json:"email_content" binding:"required"`
	SummaryType  string `json:"summary_type"` // brief or detailed
}

// SummaryResponse summary result
type SummaryResponse struct {
	Summary        string   `json:"summary"`
	KeyPoints      []string `json:"key_points,omitempty"`
	Confidence     float64  `json:"confidence"`
	ProcessingTime float64  `json:"processing_time"`
}

// AvailableTemplatesResponse list of templates
type AvailableTemplatesResponse struct {
	Templates    []string          `json:"templates"`
	Descriptions map[string]string `json:"descriptions"`
}
