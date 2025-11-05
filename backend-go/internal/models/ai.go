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

// HolisticAnalysisRequest for holistic inbox analysis
type HolisticAnalysisRequest struct {
	EmailIDs []string `json:"email_ids" binding:"required"`
}

// TrulyRelevantAction represents an action that requires attention
type TrulyRelevantAction struct {
	ActionType        string   `json:"action_type"` // required_personal_action, team_action, optional_action
	Priority          string   `json:"priority"`    // high, medium, low
	Topic             string   `json:"topic"`
	CanonicalEmailID  string   `json:"canonical_email_id"`
	RelatedEmailIDs   []string `json:"related_email_ids"`
	Deadline          string   `json:"deadline"` // ISO date or description
	WhyRelevant       string   `json:"why_relevant"`
	BlockingOthers    bool     `json:"blocking_others"`
}

// SupersededAction represents an action made obsolete by a newer email
type SupersededAction struct {
	OriginalEmailID    string `json:"original_email_id"`
	SupersededByEmailID string `json:"superseded_by_email_id"`
	Reason             string `json:"reason"`
}

// DuplicateGroup represents a group of similar/duplicate emails
type DuplicateGroup struct {
	Topic            string   `json:"topic"`
	EmailIDs         []string `json:"email_ids"`
	KeepEmailID      string   `json:"keep_email_id"`
	ArchiveEmailIDs  []string `json:"archive_email_ids"`
}

// ExpiredItem represents an email with a past deadline or event
type ExpiredItem struct {
	EmailID string `json:"email_id"`
	Reason  string `json:"reason"`
}

// HolisticAnalysisResponse results of holistic inbox analysis
type HolisticAnalysisResponse struct {
	TrulyRelevantActions []TrulyRelevantAction `json:"truly_relevant_actions"`
	SupersededActions    []SupersededAction    `json:"superseded_actions"`
	DuplicateGroups      []DuplicateGroup      `json:"duplicate_groups"`
	ExpiredItems         []ExpiredItem         `json:"expired_items"`
	ProcessingTime       float64               `json:"processing_time,omitempty"`
	EmailsAnalyzed       int                   `json:"emails_analyzed"`
}
