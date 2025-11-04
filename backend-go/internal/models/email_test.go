package models

import (
	"encoding/json"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestEmailSerialization(t *testing.T) {
	confidence := 0.95
	email := Email{
		ID:             "test-123",
		Subject:        "Test Subject",
		Sender:         "sender@test.com",
		Recipient:      "recipient@test.com",
		Body:           "Test body",
		Content:        "Test content",
		ReceivedTime:   time.Now(),
		Date:           time.Now(),
		IsRead:         false,
		HasAttachments: true,
		Importance:     "High",
		Categories:     []string{"Test", "Important"},
		ConversationID: "conv-456",
		AICategory:     "required_personal_action",
		AIConfidence:   confidence,
		AIReasoning:    "Requires immediate attention",
		OneLineSummary: "Action required",
		Category:       "work",
	}

	// Test JSON serialization
	jsonData, err := json.Marshal(email)
	assert.NoError(t, err)
	assert.NotEmpty(t, jsonData)

	// Test JSON deserialization
	var decoded Email
	err = json.Unmarshal(jsonData, &decoded)
	assert.NoError(t, err)
	assert.Equal(t, email.ID, decoded.ID)
	assert.Equal(t, email.Subject, decoded.Subject)
	assert.Equal(t, email.Sender, decoded.Sender)
	assert.Equal(t, email.AICategory, decoded.AICategory)
	assert.Equal(t, email.AIConfidence, decoded.AIConfidence)
}

func TestEmailListResponse(t *testing.T) {
	emails := []Email{
		{ID: "1", Subject: "Email 1"},
		{ID: "2", Subject: "Email 2"},
	}

	response := EmailListResponse{
		Emails:  emails,
		Total:   10,
		Offset:  0,
		Limit:   2,
		HasMore: true,
	}

	jsonData, err := json.Marshal(response)
	assert.NoError(t, err)
	assert.Contains(t, string(jsonData), "Email 1")
	assert.Contains(t, string(jsonData), "has_more")
}

func TestCategoryFolderMapping(t *testing.T) {
	mapping := CategoryFolderMapping{
		Category:     "required_personal_action",
		FolderName:   "Work Relevant",
		StaysInInbox: true,
	}

	jsonData, err := json.Marshal(mapping)
	assert.NoError(t, err)
	assert.Contains(t, string(jsonData), "required_personal_action")
	assert.Contains(t, string(jsonData), "stays_in_inbox")
}

func TestBulkApplyRequest(t *testing.T) {
	request := BulkApplyRequest{
		EmailIDs:       []string{"email-1", "email-2", "email-3"},
		ApplyToOutlook: true,
	}

	jsonData, err := json.Marshal(request)
	assert.NoError(t, err)

	var decoded BulkApplyRequest
	err = json.Unmarshal(jsonData, &decoded)
	assert.NoError(t, err)
	assert.Equal(t, len(request.EmailIDs), len(decoded.EmailIDs))
	assert.Equal(t, request.ApplyToOutlook, decoded.ApplyToOutlook)
}

func TestEmailBatchResult(t *testing.T) {
	result := EmailBatchResult{
		ProcessedCount:  10,
		SuccessfulCount: 8,
		FailedCount:     2,
		Results: []EmailProcessingResult{
			{
				EmailID:    "email-1",
				Category:   "fyi",
				Confidence: 0.92,
				Reasoning:  "Informational only",
				Priority:   "low",
			},
		},
		Errors: []string{"Error processing email-2"},
	}

	jsonData, err := json.Marshal(result)
	assert.NoError(t, err)
	assert.Contains(t, string(jsonData), "processed_count")
	assert.Contains(t, string(jsonData), "email-1")
}
