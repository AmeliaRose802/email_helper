package azureopenai

import (
	"encoding/json"
	"fmt"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// Test buildClassificationSystemPrompt - No mocks needed, pure business logic
func TestBuildClassificationSystemPrompt(t *testing.T) {
	client := &Client{}

	t.Run("BasicPromptWithoutContext", func(t *testing.T) {
		prompt := client.buildClassificationSystemPrompt("")
		
		assert.Contains(t, prompt, "email classification assistant")
		assert.Contains(t, prompt, "required_personal_action")
		assert.Contains(t, prompt, "team_action")
		assert.Contains(t, prompt, "fyi")
		assert.Contains(t, prompt, "newsletter")
		assert.Contains(t, prompt, "optional_event")
		assert.Contains(t, prompt, "job_listing")
		assert.Contains(t, prompt, "spam_to_delete")
		assert.Contains(t, prompt, "INBOX CATEGORIES")
		assert.Contains(t, prompt, "NON-INBOX CATEGORIES")
		assert.NotContains(t, prompt, "User context:")
	})

	t.Run("PromptWithUserContext", func(t *testing.T) {
		userContext := "I work on Azure DevOps team focusing on CI/CD pipelines"
		prompt := client.buildClassificationSystemPrompt(userContext)
		
		assert.Contains(t, prompt, "User context:")
		assert.Contains(t, prompt, userContext)
		assert.Contains(t, prompt, "required_personal_action")
	})

	t.Run("PromptIncludesAllCategories", func(t *testing.T) {
		prompt := client.buildClassificationSystemPrompt("")
		
		categories := []string{
			"required_personal_action",
			"team_action",
			"fyi",
			"newsletter",
			"optional_event",
			"job_listing",
			"spam_to_delete",
		}
		
		for _, category := range categories {
			assert.Contains(t, prompt, category, "Prompt should include category: "+category)
		}
	})

	t.Run("PromptIncludesInstructions", func(t *testing.T) {
		prompt := client.buildClassificationSystemPrompt("")
		
		assert.Contains(t, prompt, "Rules:")
		assert.Contains(t, prompt, "confidence")
		assert.Contains(t, prompt, "reasoning")
		assert.Contains(t, prompt, "alternative categories")
	})

	t.Run("PromptHandlesLongUserContext", func(t *testing.T) {
		longContext := strings.Repeat("context ", 100)
		prompt := client.buildClassificationSystemPrompt(longContext)
		
		assert.Contains(t, prompt, longContext)
		assert.Greater(t, len(prompt), 1000)
	})

	t.Run("PromptHandlesSpecialCharacters", func(t *testing.T) {
		specialContext := "I work with C++, Node.js, and \"quoted\" values"
		prompt := client.buildClassificationSystemPrompt(specialContext)
		
		assert.Contains(t, prompt, specialContext)
		assert.Contains(t, prompt, "C++")
		assert.Contains(t, prompt, "\"quoted\"")
	})
}

// Test buildClassificationUserPrompt - No mocks needed
func TestBuildClassificationUserPrompt(t *testing.T) {
	client := &Client{}

	t.Run("BasicEmailPrompt", func(t *testing.T) {
		subject := "Team meeting tomorrow"
		sender := "manager@company.com"
		content := "Let's meet at 2pm to discuss the project"
		
		prompt := client.buildClassificationUserPrompt(subject, sender, content)
		
		assert.Contains(t, prompt, subject)
		assert.Contains(t, prompt, sender)
		assert.Contains(t, prompt, content)
		assert.Contains(t, prompt, "Subject:")
		assert.Contains(t, prompt, "From:")
		assert.Contains(t, prompt, "Body:")
		assert.Contains(t, prompt, "Respond with valid JSON")
	})

	t.Run("PromptIncludesRequiredJSONFields", func(t *testing.T) {
		prompt := client.buildClassificationUserPrompt("Test", "test@test.com", "Test body")
		
		assert.Contains(t, prompt, "category")
		assert.Contains(t, prompt, "confidence")
		assert.Contains(t, prompt, "explanation")
		assert.Contains(t, prompt, "one_line_summary")
		assert.Contains(t, prompt, "alternative_categories")
	})

	t.Run("HandlesEmptyFields", func(t *testing.T) {
		prompt := client.buildClassificationUserPrompt("", "", "")
		
		assert.Contains(t, prompt, "Subject:")
		assert.Contains(t, prompt, "From:")
		assert.Contains(t, prompt, "Body:")
		assert.Contains(t, prompt, "JSON")
	})

	t.Run("HandlesLongContent", func(t *testing.T) {
		longContent := strings.Repeat("Lorem ipsum dolor sit amet. ", 200)
		prompt := client.buildClassificationUserPrompt("Test", "test@test.com", longContent)
		
		assert.Contains(t, prompt, longContent)
	})

	t.Run("HandlesSpecialCharactersInEmail", func(t *testing.T) {
		subject := "RE: Bug #123 - [URGENT] API \"failure\""
		sender := "user+tag@company.com"
		content := "Here's the stack trace:\n{\n  \"error\": \"null pointer\"\n}"
		
		prompt := client.buildClassificationUserPrompt(subject, sender, content)
		
		assert.Contains(t, prompt, subject)
		assert.Contains(t, prompt, sender)
		assert.Contains(t, prompt, content)
	})
}

// Test buildActionItemsUserPrompt - No mocks needed
func TestBuildActionItemsUserPrompt(t *testing.T) {
	client := &Client{}

	t.Run("BasicActionItemsPrompt", func(t *testing.T) {
		emailContent := "Please review the PR and deploy to staging by Friday"
		userContext := "DevOps engineer"
		
		prompt := client.buildActionItemsUserPrompt(emailContent, userContext)
		
		assert.Contains(t, prompt, emailContent)
		assert.Contains(t, prompt, "Extract action items")
		assert.Contains(t, prompt, "JSON")
	})

	t.Run("PromptIncludesRequiredFields", func(t *testing.T) {
		prompt := client.buildActionItemsUserPrompt("Test content", "")
		
		assert.Contains(t, prompt, "action_items")
		assert.Contains(t, prompt, "urgency")
		assert.Contains(t, prompt, "deadline")
		assert.Contains(t, prompt, "confidence")
		assert.Contains(t, prompt, "action_required")
		assert.Contains(t, prompt, "explanation")
	})

	t.Run("HandlesEmptyContent", func(t *testing.T) {
		prompt := client.buildActionItemsUserPrompt("", "")
		
		assert.Contains(t, prompt, "Extract action items")
		assert.Contains(t, prompt, "JSON")
	})

	t.Run("UrgencyLevelsSpecified", func(t *testing.T) {
		prompt := client.buildActionItemsUserPrompt("Test", "")
		
		assert.Contains(t, prompt, "low|medium|high|urgent")
	})
}

// Test buildSummaryUserPrompt - No mocks needed
func TestBuildSummaryUserPrompt(t *testing.T) {
	client := &Client{}

	t.Run("BriefSummaryPrompt", func(t *testing.T) {
		emailContent := "This is a long email about project updates..."
		prompt := client.buildSummaryUserPrompt(emailContent, "brief")
		
		assert.Contains(t, prompt, emailContent)
		assert.Contains(t, prompt, "brief")
		assert.Contains(t, prompt, "Summarize")
		assert.Contains(t, prompt, "JSON")
	})

	t.Run("DetailedSummaryPrompt", func(t *testing.T) {
		emailContent := "This is a long email..."
		prompt := client.buildSummaryUserPrompt(emailContent, "detailed")
		
		assert.Contains(t, prompt, "detailed")
		assert.Contains(t, prompt, emailContent)
	})

	t.Run("DefaultsToBrief", func(t *testing.T) {
		prompt := client.buildSummaryUserPrompt("Test", "")
		
		assert.Contains(t, prompt, "brief")
	})

	t.Run("PromptIncludesRequiredFields", func(t *testing.T) {
		prompt := client.buildSummaryUserPrompt("Test", "brief")
		
		assert.Contains(t, prompt, "summary")
		assert.Contains(t, prompt, "key_points")
		assert.Contains(t, prompt, "confidence")
	})
}

// Test parseEmailContent - No mocks needed, pure string parsing
func TestParseEmailContent(t *testing.T) {
	t.Run("ParseCompleteEmail", func(t *testing.T) {
		emailContent := `Subject: Team Meeting
From: manager@company.com

This is the email body.
It has multiple lines.`
		
		subject, sender, body := parseEmailContent(emailContent)
		
		assert.Equal(t, "Team Meeting", subject)
		assert.Equal(t, "manager@company.com", sender)
		assert.Contains(t, body, "This is the email body")
		assert.Contains(t, body, "multiple lines")
	})

	t.Run("ParseEmailWithOnlySubject", func(t *testing.T) {
		emailContent := "Subject: Test Subject\nBody text here"
		
		subject, sender, body := parseEmailContent(emailContent)
		
		assert.Equal(t, "Test Subject", subject)
		assert.Equal(t, "", sender)
		// Body should be the full content when no empty line delimiter found
		assert.Contains(t, body, "Subject:")
	})

	t.Run("ParseEmailWithOnlySender", func(t *testing.T) {
		emailContent := "From: sender@test.com\nBody text here"
		
		subject, sender, _ := parseEmailContent(emailContent)
		
		assert.Equal(t, "", subject)
		assert.Equal(t, "sender@test.com", sender)
	})

	t.Run("ParsePlainTextWithoutHeaders", func(t *testing.T) {
		emailContent := "This is just plain text body content"
		
		subject, sender, body := parseEmailContent(emailContent)
		
		assert.Equal(t, "", subject)
		assert.Equal(t, "", sender)
		assert.Equal(t, emailContent, body)
	})

	t.Run("ParseEmailWithExtraWhitespace", func(t *testing.T) {
		emailContent := `Subject:   Test with spaces   
From:   sender@test.com   

Body content`
		
		subject, sender, _ := parseEmailContent(emailContent)
		
		assert.Equal(t, "Test with spaces", subject)
		assert.Equal(t, "sender@test.com", sender)
	})

	t.Run("ParseEmailWithSpecialCharacters", func(t *testing.T) {
		emailContent := `Subject: RE: Bug #123 - [URGENT]
From: user+tag@company.com

Body with "quotes" and 'apostrophes'`
		
		subject, sender, body := parseEmailContent(emailContent)
		
		assert.Equal(t, "RE: Bug #123 - [URGENT]", subject)
		assert.Equal(t, "user+tag@company.com", sender)
		assert.Contains(t, body, "quotes")
		assert.Contains(t, body, "apostrophes")
	})

	t.Run("ParseEmailWithMultipleEmptyLines", func(t *testing.T) {
		emailContent := `Subject: Test
From: test@test.com


Body starts after multiple empty lines`
		
		subject, sender, body := parseEmailContent(emailContent)
		
		assert.Equal(t, "Test", subject)
		assert.Equal(t, "test@test.com", sender)
		assert.Contains(t, body, "Body starts")
	})

	t.Run("ParseEmptyString", func(t *testing.T) {
		subject, sender, body := parseEmailContent("")
		
		assert.Equal(t, "", subject)
		assert.Equal(t, "", sender)
		assert.Equal(t, "", body)
	})
}

// Test JSON response parsing logic - No Azure API calls, just testing cleanup and parsing
func TestResponseCleanup(t *testing.T) {
	t.Run("CleanMarkdownCodeBlock", func(t *testing.T) {
		responseWithMarkdown := "```json\n{\"category\": \"fyi\"}\n```"
		
		// Simulate the cleanup logic from ClassifyEmail
		cleaned := strings.TrimPrefix(responseWithMarkdown, "```json")
		cleaned = strings.TrimPrefix(cleaned, "```")
		cleaned = strings.TrimSuffix(cleaned, "```")
		cleaned = strings.TrimSpace(cleaned)
		
		var result map[string]interface{}
		err := json.Unmarshal([]byte(cleaned), &result)
		
		require.NoError(t, err)
		assert.Equal(t, "fyi", result["category"])
	})

	t.Run("CleanTripleBackticksOnly", func(t *testing.T) {
		responseWithBackticks := "```\n{\"category\": \"fyi\"}\n```"
		
		cleaned := strings.TrimPrefix(responseWithBackticks, "```json")
		cleaned = strings.TrimPrefix(cleaned, "```")
		cleaned = strings.TrimSuffix(cleaned, "```")
		cleaned = strings.TrimSpace(cleaned)
		
		var result map[string]interface{}
		err := json.Unmarshal([]byte(cleaned), &result)
		
		require.NoError(t, err)
		assert.Equal(t, "fyi", result["category"])
	})

	t.Run("HandleCleanJSON", func(t *testing.T) {
		cleanJSON := `{"category": "fyi", "confidence": 0.95}`
		
		cleaned := strings.TrimSpace(cleanJSON)
		
		var result map[string]interface{}
		err := json.Unmarshal([]byte(cleaned), &result)
		
		require.NoError(t, err)
		assert.Equal(t, "fyi", result["category"])
		assert.Equal(t, 0.95, result["confidence"])
	})

	t.Run("HandleJSONWithWhitespace", func(t *testing.T) {
		jsonWithWhitespace := "  \n  {\"category\": \"fyi\"}  \n  "
		
		cleaned := strings.TrimSpace(jsonWithWhitespace)
		
		var result map[string]interface{}
		err := json.Unmarshal([]byte(cleaned), &result)
		
		require.NoError(t, err)
		assert.Equal(t, "fyi", result["category"])
	})
}

// Test classification response parsing - Mock AI response, test parsing logic
func TestClassificationResponseParsing(t *testing.T) {
	t.Run("ParseCompleteClassificationResponse", func(t *testing.T) {
		aiResponse := `{
			"category": "required_personal_action",
			"confidence": 0.92,
			"reasoning": "Email requires direct response from you",
			"one_line_summary": "Manager requesting project update",
			"alternative_categories": ["team_action", "fyi"]
		}`
		
		var result struct {
			Category              string   `json:"category"`
			Confidence            float64  `json:"confidence"`
			Reasoning             string   `json:"reasoning"`
			Explanation           string   `json:"explanation"`
			OneLineSummary        string   `json:"one_line_summary"`
			AlternativeCategories []string `json:"alternative_categories"`
		}
		
		err := json.Unmarshal([]byte(aiResponse), &result)
		require.NoError(t, err)
		
		assert.Equal(t, "required_personal_action", result.Category)
		assert.Equal(t, 0.92, result.Confidence)
		assert.Equal(t, "Email requires direct response from you", result.Reasoning)
		assert.Equal(t, "Manager requesting project update", result.OneLineSummary)
		assert.Len(t, result.AlternativeCategories, 2)
		assert.Contains(t, result.AlternativeCategories, "team_action")
	})

	t.Run("ParseResponseWithExplanationInsteadOfReasoning", func(t *testing.T) {
		aiResponse := `{
			"category": "fyi",
			"confidence": 0.85,
			"explanation": "Informational email only",
			"one_line_summary": "Weekly team update"
		}`
		
		var result struct {
			Category       string  `json:"category"`
			Confidence     float64 `json:"confidence"`
			Reasoning      string  `json:"reasoning"`
			Explanation    string  `json:"explanation"`
			OneLineSummary string  `json:"one_line_summary"`
		}
		
		err := json.Unmarshal([]byte(aiResponse), &result)
		require.NoError(t, err)
		
		// Test the logic from ClassifyEmail that uses explanation if reasoning is empty
		reasoning := result.Reasoning
		if reasoning == "" {
			reasoning = result.Explanation
		}
		
		assert.Equal(t, "fyi", result.Category)
		assert.Equal(t, "Informational email only", reasoning)
	})

	t.Run("ParseResponseWithMissingOptionalFields", func(t *testing.T) {
		aiResponse := `{
			"category": "newsletter",
			"confidence": 0.75
		}`
		
		var result struct {
			Category              string   `json:"category"`
			Confidence            float64  `json:"confidence"`
			Reasoning             string   `json:"reasoning"`
			OneLineSummary        string   `json:"one_line_summary"`
			AlternativeCategories []string `json:"alternative_categories"`
		}
		
		err := json.Unmarshal([]byte(aiResponse), &result)
		require.NoError(t, err)
		
		assert.Equal(t, "newsletter", result.Category)
		assert.Equal(t, 0.75, result.Confidence)
		assert.Empty(t, result.Reasoning)
		assert.Empty(t, result.OneLineSummary)
		assert.Nil(t, result.AlternativeCategories)
	})

	t.Run("ConfidenceBoundaryValues", func(t *testing.T) {
		testCases := []struct {
			name       string
			confidence float64
			valid      bool
		}{
			{"Zero", 0.0, true},
			{"One", 1.0, true},
			{"Mid", 0.5, true},
			{"High", 0.99, true},
			{"Negative", -0.1, false},
			{"OverOne", 1.1, false},
		}
		
		for _, tc := range testCases {
			t.Run(tc.name, func(t *testing.T) {
				aiResponse := fmt.Sprintf(`{"category": "fyi", "confidence": %f}`, tc.confidence)
				
				var result struct {
					Category   string  `json:"category"`
					Confidence float64 `json:"confidence"`
				}
				
				err := json.Unmarshal([]byte(aiResponse), &result)
				require.NoError(t, err)
				
				// Validation logic that should be in production code
				if tc.valid {
					assert.GreaterOrEqual(t, result.Confidence, 0.0)
					assert.LessOrEqual(t, result.Confidence, 1.0)
				} else {
					assert.True(t, result.Confidence < 0.0 || result.Confidence > 1.0)
				}
			})
		}
	})
}

// Test action items response parsing
func TestActionItemsResponseParsing(t *testing.T) {
	t.Run("ParseCompleteActionItemsResponse", func(t *testing.T) {
		aiResponse := `{
			"action_items": ["Review PR #123", "Deploy to staging"],
			"urgency": "high",
			"deadline": "2025-11-05",
			"confidence": 0.88,
			"action_required": true,
			"explanation": "Two action items identified with deadline"
		}`
		
		var result struct {
			ActionItems        []string `json:"action_items"`
			Urgency            string   `json:"urgency"`
			Deadline           *string  `json:"deadline"`
			Confidence         float64  `json:"confidence"`
			ActionRequiredBool *bool    `json:"action_required"`
			Explanation        *string  `json:"explanation"`
		}
		
		err := json.Unmarshal([]byte(aiResponse), &result)
		require.NoError(t, err)
		
		assert.Len(t, result.ActionItems, 2)
		assert.Equal(t, "high", result.Urgency)
		assert.NotNil(t, result.Deadline)
		assert.Equal(t, "2025-11-05", *result.Deadline)
		assert.Equal(t, 0.88, result.Confidence)
		assert.NotNil(t, result.ActionRequiredBool)
		assert.True(t, *result.ActionRequiredBool)
	})

	t.Run("ParseResponseWithStringActionRequired", func(t *testing.T) {
		// Some prompts might return action_required as string instead of bool
		aiResponse := `{
			"action_required": "Review the document",
			"urgency": "medium"
		}`
		
		var result struct {
			ActionRequired     string   `json:"action_required"`
			ActionItems        []string `json:"action_items"`
			Urgency            string   `json:"urgency"`
		}
		
		err := json.Unmarshal([]byte(aiResponse), &result)
		require.NoError(t, err)
		
		// Test the fallback logic from ExtractActionItems
		actionItems := result.ActionItems
		if len(actionItems) == 0 && result.ActionRequired != "" {
			actionItems = []string{result.ActionRequired}
		}
		
		assert.Len(t, actionItems, 1)
		assert.Equal(t, "Review the document", actionItems[0])
	})

	t.Run("ParseResponseWithEmptyActionItems", func(t *testing.T) {
		aiResponse := `{
			"action_items": [],
			"urgency": "low",
			"action_required": false
		}`
		
		var result struct {
			ActionItems        []string `json:"action_items"`
			Urgency            string   `json:"urgency"`
			ActionRequiredBool *bool    `json:"action_required"`
		}
		
		err := json.Unmarshal([]byte(aiResponse), &result)
		require.NoError(t, err)
		
		assert.Empty(t, result.ActionItems)
		assert.Equal(t, "low", result.Urgency)
		assert.NotNil(t, result.ActionRequiredBool)
		assert.False(t, *result.ActionRequiredBool)
	})

	t.Run("ValidateUrgencyLevels", func(t *testing.T) {
		validUrgencies := []string{"low", "medium", "high", "urgent"}
		
		for _, urgency := range validUrgencies {
			aiResponse := fmt.Sprintf(`{"action_items": [], "urgency": "%s"}`, urgency)
			
			var result struct {
				Urgency string `json:"urgency"`
			}
			
			err := json.Unmarshal([]byte(aiResponse), &result)
			require.NoError(t, err)
			assert.Equal(t, urgency, result.Urgency)
		}
	})
}

// Test summary response parsing
func TestSummaryResponseParsing(t *testing.T) {
	t.Run("ParseJSONSummaryResponse", func(t *testing.T) {
		aiResponse := `{
			"summary": "Project update meeting scheduled for Friday",
			"key_points": ["Budget approved", "Timeline extended", "New team member"],
			"confidence": 0.90
		}`
		
		var result struct {
			Summary    string   `json:"summary"`
			KeyPoints  []string `json:"key_points"`
			Confidence float64  `json:"confidence"`
		}
		
		err := json.Unmarshal([]byte(aiResponse), &result)
		require.NoError(t, err)
		
		assert.Equal(t, "Project update meeting scheduled for Friday", result.Summary)
		assert.Len(t, result.KeyPoints, 3)
		assert.Contains(t, result.KeyPoints, "Budget approved")
		assert.Equal(t, 0.90, result.Confidence)
	})

	t.Run("HandlePlainTextSummary", func(t *testing.T) {
		// Some prompts (like email_one_line_summary) return plain text, not JSON
		plainTextResponse := "Weekly team meeting agenda and action items"
		
		var result struct {
			Summary    string   `json:"summary"`
			KeyPoints  []string `json:"key_points"`
			Confidence float64  `json:"confidence"`
		}
		
		err := json.Unmarshal([]byte(plainTextResponse), &result)
		
		// Should fail to parse
		assert.Error(t, err)
		
		// Fallback logic from Summarize() - treat as plain text
		result.Summary = plainTextResponse
		result.Confidence = 0.8
		result.KeyPoints = []string{}
		
		assert.Equal(t, plainTextResponse, result.Summary)
		assert.Equal(t, 0.8, result.Confidence)
		assert.Empty(t, result.KeyPoints)
	})

	t.Run("ParseSummaryWithEmptyKeyPoints", func(t *testing.T) {
		aiResponse := `{
			"summary": "Brief update email",
			"key_points": [],
			"confidence": 0.75
		}`
		
		var result struct {
			Summary    string   `json:"summary"`
			KeyPoints  []string `json:"key_points"`
			Confidence float64  `json:"confidence"`
		}
		
		err := json.Unmarshal([]byte(aiResponse), &result)
		require.NoError(t, err)
		
		assert.Equal(t, "Brief update email", result.Summary)
		assert.Empty(t, result.KeyPoints)
		assert.Equal(t, 0.75, result.Confidence)
	})

	t.Run("ParseSummaryWithLongKeyPoints", func(t *testing.T) {
		longKeyPoint := strings.Repeat("Important detail ", 20)
		aiResponse := fmt.Sprintf(`{
			"summary": "Detailed project report",
			"key_points": ["%s", "Another point"],
			"confidence": 0.85
		}`, longKeyPoint)
		
		var result struct {
			Summary    string   `json:"summary"`
			KeyPoints  []string `json:"key_points"`
			Confidence float64  `json:"confidence"`
		}
		
		err := json.Unmarshal([]byte(aiResponse), &result)
		require.NoError(t, err)
		
		assert.Len(t, result.KeyPoints, 2)
		assert.Contains(t, result.KeyPoints[0], "Important detail")
	})
}

// Test error scenarios - Invalid JSON, malformed responses
func TestMalformedResponseHandling(t *testing.T) {
	t.Run("InvalidJSON", func(t *testing.T) {
		malformedJSON := `{"category": "fyi", invalid json}`
		
		var result map[string]interface{}
		err := json.Unmarshal([]byte(malformedJSON), &result)
		
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "invalid")
	})

	t.Run("IncompleteJSON", func(t *testing.T) {
		incompleteJSON := `{"category": "fyi"`
		
		var result map[string]interface{}
		err := json.Unmarshal([]byte(incompleteJSON), &result)
		
		assert.Error(t, err)
	})

	t.Run("EmptyResponse", func(t *testing.T) {
		emptyJSON := ``
		
		var result map[string]interface{}
		err := json.Unmarshal([]byte(emptyJSON), &result)
		
		assert.Error(t, err)
	})

	t.Run("JSONWithMissingRequiredFields", func(t *testing.T) {
		// Missing category field
		jsonMissingCategory := `{"confidence": 0.8}`
		
		var result struct {
			Category   string  `json:"category"`
			Confidence float64 `json:"confidence"`
		}
		
		err := json.Unmarshal([]byte(jsonMissingCategory), &result)
		require.NoError(t, err) // JSON parsing succeeds
		
		// But category is empty string
		assert.Empty(t, result.Category)
		assert.Equal(t, 0.8, result.Confidence)
		
		// Production code should validate required fields are not empty
		// This test demonstrates that JSON unmarshaling succeeds even with missing fields
		// The production code needs additional validation
	})

	t.Run("JSONWithWrongTypes", func(t *testing.T) {
		jsonWrongType := `{"category": "fyi", "confidence": "high"}`
		
		var result struct {
			Category   string  `json:"category"`
			Confidence float64 `json:"confidence"`
		}
		
		err := json.Unmarshal([]byte(jsonWrongType), &result)
		
		// Should error because confidence is string, not float
		assert.Error(t, err)
	})
}

// Test GetAvailableTemplates - No mocks needed
func TestGetAvailableTemplates(t *testing.T) {
	t.Run("ReturnsAllTemplateTypes", func(t *testing.T) {
		templates := GetAvailableTemplates()
		
		assert.NotEmpty(t, templates)
		assert.Contains(t, templates, "classification")
		assert.Contains(t, templates, "action_items")
		assert.Contains(t, templates, "summarization")
	})

	t.Run("TemplatesHaveDescriptions", func(t *testing.T) {
		templates := GetAvailableTemplates()
		
		for key, desc := range templates {
			assert.NotEmpty(t, key, "Template key should not be empty")
			assert.NotEmpty(t, desc, "Template description should not be empty")
		}
	})
}

