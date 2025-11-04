package azureopenai

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"path/filepath"
	"strings"
	"time"

	"email-helper-backend/internal/models"
	"email-helper-backend/pkg/prompty"

	"github.com/Azure/azure-sdk-for-go/sdk/ai/azopenai"
	"github.com/Azure/azure-sdk-for-go/sdk/azcore"
	"github.com/Azure/azure-sdk-for-go/sdk/azcore/to"
	"github.com/Azure/azure-sdk-for-go/sdk/azidentity"
)

// Client handles Azure OpenAI API calls
type Client struct {
	client     *azopenai.Client
	deployment string
	endpoint   string
	prompts    map[string]*prompty.PromptyTemplate
}

// NewClient creates a new Azure OpenAI client using DefaultAzureCredential (az login)
// This matches the Python backend's authentication approach
func NewClient(endpoint, apiKey, deployment string) (*Client, error) {
	if endpoint == "" {
		return nil, fmt.Errorf("Azure OpenAI endpoint is required")
	}

	var client *azopenai.Client
	var err error

	// Prefer Azure DefaultCredential (az login) over API key for security
	// Only use API key if explicitly set (not recommended)
	if apiKey == "" {
		// Use DefaultAzureCredential (preferred - works with az login)
		log.Println("🔐 Using Azure DefaultCredential authentication (az login)")
		
		cred, err := azidentity.NewDefaultAzureCredential(nil)
		if err != nil {
			return nil, fmt.Errorf("failed to create Azure credential (run 'az login'): %w", err)
		}

		// Convert OpenAI endpoint to cognitive services endpoint if needed
		cognitiveEndpoint := strings.Replace(endpoint, ".openai.azure.com", ".cognitiveservices.azure.com", 1)
		
		client, err = azopenai.NewClient(cognitiveEndpoint, cred, nil)
		if err != nil {
			return nil, fmt.Errorf("failed to create Azure OpenAI client with credential: %w", err)
		}
		log.Println("✅ Azure OpenAI client authenticated via az login")
	} else {
		// Fallback to API key authentication (not recommended)
		log.Println("⚠️  Using API key authentication (consider using 'az login' instead)")
		
		keyCredential := azcore.NewKeyCredential(apiKey)
		client, err = azopenai.NewClientWithKeyCredential(endpoint, keyCredential, nil)
		if err != nil {
			return nil, fmt.Errorf("failed to create Azure OpenAI client: %w", err)
		}
	}

	// Load prompty templates from the prompts directory
	promptsDir := filepath.Join(".", "prompts")
	prompts, err := prompty.LoadPromptDirectory(promptsDir)
	if err != nil {
		// Try from parent directory (when running from backend-go/)
		promptsDir = filepath.Join("..", "prompts")
		prompts, err = prompty.LoadPromptDirectory(promptsDir)
		if err != nil {
			log.Printf("Warning: failed to load prompty files: %v (continuing with hardcoded prompts)", err)
			prompts = make(map[string]*prompty.PromptyTemplate)
		}
	}

	log.Printf("Loaded %d prompty templates from %s", len(prompts), promptsDir)

	return &Client{
		client:     client,
		deployment: deployment,
		endpoint:   endpoint,
		prompts:    prompts,
	}, nil
}

// ClassifyEmail classifies an email using AI
func (c *Client) ClassifyEmail(ctx context.Context, subject, sender, content, userContext string) (*models.AIClassificationResponse, error) {
	startTime := time.Now()

	var systemPrompt, userPrompt string
	var temperature float32 = 0.3
	var maxTokens int32 = 500

	// Try to use prompty template if available
	if tmpl, ok := c.prompts["email_classifier_with_explanation"]; ok {
		vars := map[string]string{
			"context":          userContext,
			"job_role_context": "Software Engineer", // TODO: Make configurable
			"username":         "User",              // TODO: Make configurable
			"subject":          subject,
			"sender":           sender,
			"date":             time.Now().Format(time.RFC1123),
			"content":          content,
		}

		var err error
		systemPrompt, err = tmpl.RenderPrompt("system", vars)
		if err != nil {
			log.Printf("Warning: failed to render system prompt: %v (using fallback)", err)
			systemPrompt = c.buildClassificationSystemPrompt(userContext)
		}

		userPrompt, err = tmpl.RenderPrompt("user", vars)
		if err != nil {
			log.Printf("Warning: failed to render user prompt: %v (using fallback)", err)
			userPrompt = c.buildClassificationUserPrompt(subject, sender, content)
		}

		// Use template parameters if available
		temperature = tmpl.Model.Parameters.Temperature
		maxTokens = tmpl.Model.Parameters.MaxTokens
	} else {
		// Fallback to hardcoded prompts
		log.Printf("Warning: email_classifier_with_explanation.prompty not found, using fallback prompts")
		systemPrompt = c.buildClassificationSystemPrompt(userContext)
		userPrompt = c.buildClassificationUserPrompt(subject, sender, content)
	}

	messages := []azopenai.ChatRequestMessageClassification{
		&azopenai.ChatRequestSystemMessage{Content: to.Ptr(systemPrompt)},
		&azopenai.ChatRequestUserMessage{Content: azopenai.NewChatRequestUserMessageContent(userPrompt)},
	}

	resp, err := c.client.GetChatCompletions(ctx, azopenai.ChatCompletionsOptions{
		Messages:       messages,
		DeploymentName: to.Ptr(c.deployment),
		MaxTokens:      to.Ptr(maxTokens),
		Temperature:    to.Ptr(temperature),
	}, nil)

	if err != nil {
		return nil, fmt.Errorf("failed to get classification: %w", err)
	}

	if len(resp.Choices) == 0 {
		return nil, fmt.Errorf("no response from AI")
	}

	responseText := *resp.Choices[0].Message.Content
	
	// Clean up response - remove markdown code blocks if present
	responseText = strings.TrimPrefix(responseText, "```json")
	responseText = strings.TrimPrefix(responseText, "```")
	responseText = strings.TrimSuffix(responseText, "```")
	responseText = strings.TrimSpace(responseText)

	// Parse JSON response
	var result struct {
		Category              string   `json:"category"`
		Confidence            float64  `json:"confidence"`
		Reasoning             string   `json:"reasoning"`
		Explanation           string   `json:"explanation"`
		OneLineSummary        string   `json:"one_line_summary"`
		AlternativeCategories []string `json:"alternative_categories"`
	}

	if err := json.Unmarshal([]byte(responseText), &result); err != nil {
		return nil, fmt.Errorf("failed to parse AI response: %w", err)
	}

	// Use explanation if reasoning is empty (different prompts use different field names)
	reasoning := result.Reasoning
	if reasoning == "" {
		reasoning = result.Explanation
	}

	processingTime := time.Since(startTime).Seconds()

	return &models.AIClassificationResponse{
		Category:              result.Category,
		Confidence:            &result.Confidence,
		Reasoning:             reasoning,
		OneLineSummary:        result.OneLineSummary,
		AlternativeCategories: result.AlternativeCategories,
		ProcessingTime:        processingTime,
	}, nil
}

// ExtractActionItems extracts action items from email content
func (c *Client) ExtractActionItems(ctx context.Context, emailContent, userContext string) (*models.ActionItemResponse, error) {
	var systemPrompt, userPrompt string
	var temperature float32 = 0.3
	var maxTokens int32 = 400

	// Try to use prompty template if available
	if tmpl, ok := c.prompts["summerize_action_item"]; ok {
		// Extract subject, sender, and body from emailContent
		subject, sender, body := parseEmailContent(emailContent)
		
		vars := map[string]string{
			"context":  userContext,
			"username": "User", // TODO: Make configurable
			"subject":  subject,
			"sender":   sender,
			"date":     time.Now().Format(time.RFC1123),
			"content":  body,
		}

		var err error
		systemPrompt, err = tmpl.RenderPrompt("system", vars)
		if err != nil {
			log.Printf("Warning: failed to render action items system prompt: %v (using fallback)", err)
			systemPrompt = "You are an expert at extracting action items and tasks from emails."
		}

		userPrompt, err = tmpl.RenderPrompt("user", vars)
		if err != nil {
			log.Printf("Warning: failed to render action items user prompt: %v (using fallback)", err)
			userPrompt = c.buildActionItemsUserPrompt(emailContent, userContext)
		}

		temperature = tmpl.Model.Parameters.Temperature
		maxTokens = tmpl.Model.Parameters.MaxTokens
	} else {
		// Fallback to hardcoded prompts
		log.Printf("Warning: summerize_action_item.prompty not found, using fallback prompts")
		systemPrompt = "You are an expert at extracting action items and tasks from emails."
		userPrompt = c.buildActionItemsUserPrompt(emailContent, userContext)
	}

	messages := []azopenai.ChatRequestMessageClassification{
		&azopenai.ChatRequestSystemMessage{Content: to.Ptr(systemPrompt)},
		&azopenai.ChatRequestUserMessage{Content: azopenai.NewChatRequestUserMessageContent(userPrompt)},
	}

	resp, err := c.client.GetChatCompletions(ctx, azopenai.ChatCompletionsOptions{
		Messages:       messages,
		DeploymentName: to.Ptr(c.deployment),
		MaxTokens:      to.Ptr(maxTokens),
		Temperature:    to.Ptr(temperature),
	}, nil)

	if err != nil {
		return nil, fmt.Errorf("failed to extract action items: %w", err)
	}

	if len(resp.Choices) == 0 {
		return nil, fmt.Errorf("no response from AI")
	}

	responseText := *resp.Choices[0].Message.Content
	responseText = strings.TrimPrefix(responseText, "```json")
	responseText = strings.TrimPrefix(responseText, "```")
	responseText = strings.TrimSuffix(responseText, "```")
	responseText = strings.TrimSpace(responseText)

	var result struct {
		DueDate        string   `json:"due_date"`
		ActionRequired string   `json:"action_required"`
		ActionItems    []string `json:"action_items"`
		Urgency        string   `json:"urgency"`
		Deadline       *string  `json:"deadline"`
		Confidence     float64  `json:"confidence"`
		ActionRequiredBool *bool    `json:"action_required"`
		Explanation    *string  `json:"explanation"`
		Relevance      *string  `json:"relevance"`
		Links          []string `json:"links"`
	}

	if err := json.Unmarshal([]byte(responseText), &result); err != nil {
		return nil, fmt.Errorf("failed to parse action items response: %w", err)
	}

	// Handle different response formats from different prompts
	actionItems := result.ActionItems
	if len(actionItems) == 0 && result.ActionRequired != "" {
		actionItems = []string{result.ActionRequired}
	}

	return &models.ActionItemResponse{
		ActionItems:    actionItems,
		Urgency:        result.Urgency,
		Deadline:       result.Deadline,
		Confidence:     result.Confidence,
		ActionRequired: result.ActionRequiredBool,
		Explanation:    result.Explanation,
	}, nil
}

// Summarize generates a summary of email content
func (c *Client) Summarize(ctx context.Context, emailContent string, summaryType string) (*models.SummaryResponse, error) {
	startTime := time.Now()

	var systemPrompt, userPrompt string
	var temperature float32 = 0.2
	var maxTokens int32 = 300

	// Try to use prompty template if available
	if tmpl, ok := c.prompts["email_one_line_summary"]; ok {
		// Extract subject, sender, and body from emailContent
		subject, sender, body := parseEmailContent(emailContent)
		
		vars := map[string]string{
			"context":  "",
			"username": "User", // TODO: Make configurable
			"subject":  subject,
			"sender":   sender,
			"date":     time.Now().Format(time.RFC1123),
			"content":  body,
		}

		var err error
		systemPrompt, err = tmpl.RenderPrompt("system", vars)
		if err != nil {
			log.Printf("Warning: failed to render summary system prompt: %v (using fallback)", err)
			systemPrompt = "You are an expert at summarizing email content concisely."
		}

		userPrompt, err = tmpl.RenderPrompt("user", vars)
		if err != nil {
			log.Printf("Warning: failed to render summary user prompt: %v (using fallback)", err)
			userPrompt = c.buildSummaryUserPrompt(emailContent, summaryType)
		}

		temperature = tmpl.Model.Parameters.Temperature
		maxTokens = tmpl.Model.Parameters.MaxTokens
	} else {
		// Fallback to hardcoded prompts
		log.Printf("Warning: email_one_line_summary.prompty not found, using fallback prompts")
		systemPrompt = "You are an expert at summarizing email content concisely."
		userPrompt = c.buildSummaryUserPrompt(emailContent, summaryType)
	}

	messages := []azopenai.ChatRequestMessageClassification{
		&azopenai.ChatRequestSystemMessage{Content: to.Ptr(systemPrompt)},
		&azopenai.ChatRequestUserMessage{Content: azopenai.NewChatRequestUserMessageContent(userPrompt)},
	}

	resp, err := c.client.GetChatCompletions(ctx, azopenai.ChatCompletionsOptions{
		Messages:       messages,
		DeploymentName: to.Ptr(c.deployment),
		MaxTokens:      to.Ptr(maxTokens),
		Temperature:    to.Ptr(temperature),
	}, nil)

	if err != nil {
		return nil, fmt.Errorf("failed to generate summary: %w", err)
	}

	if len(resp.Choices) == 0 {
		return nil, fmt.Errorf("no response from AI")
	}

	responseText := *resp.Choices[0].Message.Content
	responseText = strings.TrimPrefix(responseText, "```json")
	responseText = strings.TrimPrefix(responseText, "```")
	responseText = strings.TrimSuffix(responseText, "```")
	responseText = strings.TrimSpace(responseText)

	// Try to parse as JSON first
	var result struct {
		Summary    string   `json:"summary"`
		KeyPoints  []string `json:"key_points"`
		Confidence float64  `json:"confidence"`
	}

	err = json.Unmarshal([]byte(responseText), &result)
	if err != nil {
		// If not JSON, treat entire response as summary (email_one_line_summary returns plain text)
		result.Summary = responseText
		result.Confidence = 0.8
		result.KeyPoints = []string{}
	}

	processingTime := time.Since(startTime).Seconds()

	return &models.SummaryResponse{
		Summary:        result.Summary,
		KeyPoints:      result.KeyPoints,
		Confidence:     result.Confidence,
		ProcessingTime: processingTime,
	}, nil
}

// CheckHealth checks if the Azure OpenAI service is available
func (c *Client) CheckHealth(ctx context.Context) error {
	messages := []azopenai.ChatRequestMessageClassification{
		&azopenai.ChatRequestUserMessage{Content: azopenai.NewChatRequestUserMessageContent("Test")},
	}

	_, err := c.client.GetChatCompletions(ctx, azopenai.ChatCompletionsOptions{
		Messages:       messages,
		DeploymentName: to.Ptr(c.deployment),
		MaxTokens:      to.Ptr[int32](10),
	}, nil)

	return err
}

// buildClassificationSystemPrompt builds the system prompt for email classification
func (c *Client) buildClassificationSystemPrompt(userContext string) string {
	prompt := `You are an email classification assistant. Classify emails into these categories:

**INBOX CATEGORIES (stay in inbox with Outlook category):**
- required_personal_action: Action required directly from you
- team_action: Action required from your team
- fyi: Informational, no action needed
- newsletter: Regular newsletters and updates

**NON-INBOX CATEGORIES (move to dedicated folders):**
- optional_event: Optional meetings/events
- job_listing: Job postings and recruiting emails
- spam_to_delete: Spam, promotional emails to delete

Rules:
1. Be confident - use high confidence (0.8+) for clear cases
2. If unsure between categories, choose the most actionable one
3. Consider sender domain and email patterns
4. Provide brief reasoning for your classification
5. Suggest 1-2 alternative categories if applicable`

	if userContext != "" {
		prompt += fmt.Sprintf("\n\nUser context:\n%s", userContext)
	}

	return prompt
}

// GetAvailableTemplates returns list of available prompt templates
func GetAvailableTemplates() map[string]string {
	return map[string]string{
		"classification": "Email classification with category assignment",
		"action_items":   "Extract actionable tasks from emails",
		"summarization":  "Generate email summaries",
	}
}

// parseEmailContent extracts subject, sender, and body from email content
func parseEmailContent(emailContent string) (subject, sender, body string) {
	lines := strings.Split(emailContent, "\n")
	body = emailContent // default to full content
	
	for i, line := range lines {
		if strings.HasPrefix(line, "Subject:") {
			subject = strings.TrimSpace(strings.TrimPrefix(line, "Subject:"))
		} else if strings.HasPrefix(line, "From:") {
			sender = strings.TrimSpace(strings.TrimPrefix(line, "From:"))
		} else if strings.TrimSpace(line) == "" && i > 0 {
			// Empty line after headers, rest is body
			if i+1 < len(lines) {
				body = strings.Join(lines[i+1:], "\n")
			}
			break
		}
	}
	
	return subject, sender, body
}

// buildClassificationUserPrompt builds user prompt for classification (fallback)
func (c *Client) buildClassificationUserPrompt(subject, sender, content string) string {
	return fmt.Sprintf(`Classify this email:

Subject: %s
From: %s
Body:
%s

Respond with valid JSON only, no markdown formatting:
{
  "category": "<category>",
  "confidence": <0.0-1.0>,
  "explanation": "<brief explanation>",
  "one_line_summary": "<concise summary>",
  "alternative_categories": ["<alternative1>", "<alternative2>"]
}`, subject, sender, content)
}

// buildActionItemsUserPrompt builds user prompt for action items (fallback)
func (c *Client) buildActionItemsUserPrompt(emailContent, userContext string) string {
	return fmt.Sprintf(`Extract action items from this email:

%s

Respond with valid JSON only:
{
  "action_items": ["<item1>", "<item2>"],
  "urgency": "<low|medium|high|urgent>",
  "deadline": "<date or null>",
  "confidence": <0.0-1.0>,
  "action_required": <true|false>,
  "explanation": "<brief explanation>"
}`, emailContent)
}

// buildSummaryUserPrompt builds user prompt for summarization (fallback)
func (c *Client) buildSummaryUserPrompt(emailContent, summaryType string) string {
	detailLevel := "brief"
	if summaryType == "detailed" {
		detailLevel = "detailed"
	}

	return fmt.Sprintf(`Summarize this email (%s):

%s

Respond with valid JSON only:
{
  "summary": "<concise summary>",
  "key_points": ["<point1>", "<point2>"],
  "confidence": <0.0-1.0>
}`, detailLevel, emailContent)
}
