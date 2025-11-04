package testutil

import (
	"time"
	"email-helper-backend/internal/models"
)

// CreateTestEmail creates a sample email for testing
func CreateTestEmail(id string) *models.Email {
	receivedTime := time.Now().Add(-24 * time.Hour)
	return &models.Email{
		ID:             id,
		Subject:        "Test Email Subject",
		Sender:         "sender@example.com",
		Recipient:      "recipient@example.com",
		Body:           "This is a test email body.",
		Content:        "This is a test email content.",
		ReceivedTime:   receivedTime,
		Date:           receivedTime,
		IsRead:         false,
		HasAttachments: false,
		Importance:     "Normal",
		Categories:     []string{"Test"},
		ConversationID: "conv-123",
		AICategory:     "fyi",
		AIConfidence:   0.95,
		AIReasoning:    "Test reasoning",
		OneLineSummary: "Test summary",
		Category:       "fyi",
	}
}

// CreateTestEmailList creates a list of test emails
func CreateTestEmailList(count int) []*models.Email {
	emails := make([]*models.Email, count)
	for i := 0; i < count; i++ {
		emails[i] = CreateTestEmail(string(rune('A' + i)))
	}
	return emails
}

// CreateTestTask creates a sample task for testing
func CreateTestTask(id int) *models.Task {
	now := time.Now()
	dueDate := now.Add(7 * 24 * time.Hour)
	emailID := "email-123"
	summary := "Task summary"
	
	return &models.Task{
		ID:             id,
		UserID:         1,
		Title:          "Test Task",
		Description:    "Test task description",
		Status:         "pending",
		Priority:       "medium",
		Category:       "work",
		EmailID:        &emailID,
		OneLineSummary: &summary,
		DueDate:        &dueDate,
		CreatedAt:      now,
		UpdatedAt:      now,
		CompletedAt:    nil,
	}
}

// CreateTestTaskList creates a list of test tasks
func CreateTestTaskList(count int) []*models.Task {
	tasks := make([]*models.Task, count)
	for i := 0; i < count; i++ {
		tasks[i] = CreateTestTask(i + 1)
	}
	return tasks
}

// CreateTestSettings creates sample user settings
func CreateTestSettings() *models.UserSettings {
	username := "testuser"
	jobContext := "Software Engineer"
	endpoint := "https://test.openai.azure.com"
	deployment := "gpt-4"
	
	return &models.UserSettings{
		Username:              &username,
		JobContext:            &jobContext,
		AzureOpenAIEndpoint:   &endpoint,
		AzureOpenAIDeployment: &deployment,
		CustomPrompts: map[string]string{
			"classification": "Custom classification prompt",
		},
	}
}

// CreateTestAIClassification creates a sample AI classification response
func CreateTestAIClassification() *models.AIClassificationResponse {
	confidence := 0.92
	return &models.AIClassificationResponse{
		Category:              "required_personal_action",
		Confidence:            &confidence,
		Reasoning:             "This email requires immediate action",
		OneLineSummary:        "Action needed: Review quarterly report",
		AlternativeCategories: []string{"team_action", "fyi"},
		ProcessingTime:        0.35,
	}
}

// CreateTestActionItems creates a sample action items response
func CreateTestActionItems() *models.ActionItemResponse {
	actionRequired := true
	deadline := "2025-11-15"
	explanation := "Multiple action items identified"
	
	return &models.ActionItemResponse{
		ActionItems:    []string{"Review document", "Provide feedback", "Schedule meeting"},
		Urgency:        "high",
		Deadline:       &deadline,
		Confidence:     0.88,
		ActionRequired: &actionRequired,
		Explanation:    &explanation,
	}
}

// CreateTestSummary creates a sample summary response
func CreateTestSummary() *models.SummaryResponse {
	return &models.SummaryResponse{
		Summary:        "Brief summary of the email content",
		KeyPoints:      []string{"Key point 1", "Key point 2", "Key point 3"},
		Confidence:     0.90,
		ProcessingTime: 0.25,
	}
}

// CreateTestEmailFolder creates a sample email folder
func CreateTestEmailFolder(name string) models.EmailFolder {
	return models.EmailFolder{
		Name:        name,
		UnreadCount: 5,
		TotalCount:  25,
		FolderPath:  "/" + name,
	}
}
