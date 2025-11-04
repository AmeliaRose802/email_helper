package models

import (
	"encoding/json"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestAIClassificationRequest(t *testing.T) {
	request := AIClassificationRequest{
		Subject: "Important Meeting",
		Sender:  "boss@company.com",
		Content: "Please attend the meeting tomorrow at 10 AM",
		Context: "Work emails about meetings",
	}

	jsonData, err := json.Marshal(request)
	assert.NoError(t, err)
	assert.Contains(t, string(jsonData), "Important Meeting")
	assert.Contains(t, string(jsonData), "boss@company.com")

	var decoded AIClassificationRequest
	err = json.Unmarshal(jsonData, &decoded)
	assert.NoError(t, err)
	assert.Equal(t, request.Subject, decoded.Subject)
	assert.Equal(t, request.Sender, decoded.Sender)
}

func TestAIClassificationResponse(t *testing.T) {
	confidence := 0.92
	response := AIClassificationResponse{
		Category:              "required_personal_action",
		Confidence:            &confidence,
		Reasoning:             "Meeting invitation requires response",
		AlternativeCategories: []string{"team_action", "fyi"},
		ProcessingTime:        0.35,
		OneLineSummary:        "Meeting invitation for tomorrow",
	}

	jsonData, err := json.Marshal(response)
	assert.NoError(t, err)
	assert.Contains(t, string(jsonData), "required_personal_action")
	assert.Contains(t, string(jsonData), "confidence")

	var decoded AIClassificationResponse
	err = json.Unmarshal(jsonData, &decoded)
	assert.NoError(t, err)
	assert.Equal(t, response.Category, decoded.Category)
	assert.NotNil(t, decoded.Confidence)
	assert.Equal(t, *response.Confidence, *decoded.Confidence)
}

func TestActionItemRequest(t *testing.T) {
	request := ActionItemRequest{
		EmailContent: "Please review the document and provide feedback by Friday",
		Context:      "Work project",
	}

	jsonData, err := json.Marshal(request)
	assert.NoError(t, err)
	assert.Contains(t, string(jsonData), "review the document")

	var decoded ActionItemRequest
	err = json.Unmarshal(jsonData, &decoded)
	assert.NoError(t, err)
	assert.Equal(t, request.EmailContent, decoded.EmailContent)
}

func TestActionItemResponse(t *testing.T) {
	deadline := "2025-11-15"
	actionRequired := true
	explanation := "Multiple action items found"

	response := ActionItemResponse{
		ActionItems:    []string{"Review document", "Provide feedback"},
		Urgency:        "high",
		Deadline:       &deadline,
		Confidence:     0.88,
		ActionRequired: &actionRequired,
		Explanation:    &explanation,
	}

	jsonData, err := json.Marshal(response)
	assert.NoError(t, err)
	assert.Contains(t, string(jsonData), "Review document")
	assert.Contains(t, string(jsonData), "urgency")

	var decoded ActionItemResponse
	err = json.Unmarshal(jsonData, &decoded)
	assert.NoError(t, err)
	assert.Equal(t, len(response.ActionItems), len(decoded.ActionItems))
	assert.NotNil(t, decoded.Deadline)
	assert.Equal(t, *response.Deadline, *decoded.Deadline)
}

func TestSummaryRequest(t *testing.T) {
	request := SummaryRequest{
		EmailContent: "Long email content here...",
		SummaryType:  "brief",
	}

	jsonData, err := json.Marshal(request)
	assert.NoError(t, err)
	assert.Contains(t, string(jsonData), "brief")

	var decoded SummaryRequest
	err = json.Unmarshal(jsonData, &decoded)
	assert.NoError(t, err)
	assert.Equal(t, request.SummaryType, decoded.SummaryType)
}

func TestSummaryResponse(t *testing.T) {
	response := SummaryResponse{
		Summary:        "Email discusses project timeline and deliverables",
		KeyPoints:      []string{"Deadline: Nov 30", "Budget: $50k", "Team: 5 people"},
		Confidence:     0.90,
		ProcessingTime: 0.42,
	}

	jsonData, err := json.Marshal(response)
	assert.NoError(t, err)
	assert.Contains(t, string(jsonData), "project timeline")
	assert.Contains(t, string(jsonData), "key_points")

	var decoded SummaryResponse
	err = json.Unmarshal(jsonData, &decoded)
	assert.NoError(t, err)
	assert.Equal(t, response.Summary, decoded.Summary)
	assert.Equal(t, len(response.KeyPoints), len(decoded.KeyPoints))
	assert.Equal(t, response.Confidence, decoded.Confidence)
}

func TestAvailableTemplatesResponse(t *testing.T) {
	response := AvailableTemplatesResponse{
		Templates: []string{"classification", "action_items", "summary"},
		Descriptions: map[string]string{
			"classification": "Classify emails into categories",
			"action_items":   "Extract actionable tasks",
			"summary":        "Generate email summaries",
		},
	}

	jsonData, err := json.Marshal(response)
	assert.NoError(t, err)
	assert.Contains(t, string(jsonData), "classification")
	assert.Contains(t, string(jsonData), "descriptions")

	var decoded AvailableTemplatesResponse
	err = json.Unmarshal(jsonData, &decoded)
	assert.NoError(t, err)
	assert.Equal(t, len(response.Templates), len(decoded.Templates))
	assert.Equal(t, len(response.Descriptions), len(decoded.Descriptions))
}
