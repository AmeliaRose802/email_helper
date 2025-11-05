package services

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"path/filepath"
	"strings"
	"time"

	"email-helper-backend/config"
	"email-helper-backend/internal/database"
	"email-helper-backend/internal/models"
	"email-helper-backend/pkg/azureopenai"
	"email-helper-backend/pkg/outlook"
	"email-helper-backend/pkg/prompty"

	"github.com/Azure/azure-sdk-for-go/sdk/ai/azopenai"
	"github.com/Azure/azure-sdk-for-go/sdk/azcore/to"
)

// OutlookProvider interface for email operations
type OutlookProvider interface {
	Initialize() error
	Close() error
	GetEmails(folder string, limit, offset int) ([]*models.Email, error)
	GetEmailByID(id string) (*models.Email, error)
	MarkAsRead(id string, read bool) error
	MoveToFolder(id, folder string) error
	ApplyClassification(id, category string) error
	GetFolders() ([]models.EmailFolder, error)
	GetConversationEmails(conversationID string) ([]*models.Email, error)
}

// AIClient interface for AI operations
type AIClient interface {
	ClassifyEmail(ctx context.Context, subject, sender, content, userContext string) (*models.AIClassificationResponse, error)
	ExtractActionItems(ctx context.Context, emailContent, userContext string) (*models.ActionItemResponse, error)
	Summarize(ctx context.Context, emailContent, summaryType string) (*models.SummaryResponse, error)
	CheckHealth(ctx context.Context) error
}

// EmailService handles email-related operations
type EmailService struct {
	outlookProvider OutlookProvider
	aiClient        AIClient
	useComBackend   bool
}

// NewEmailService creates a new email service
func NewEmailService(cfg *config.Config) (*EmailService, error) {
	var outlookProvider *outlook.Provider
	var err error

	if cfg.UseComBackend {
		outlookProvider, err = outlook.NewProvider()
		if err != nil {
			return nil, fmt.Errorf("failed to create Outlook provider: %w", err)
		}
		if err := outlookProvider.Initialize(); err != nil {
			return nil, fmt.Errorf("failed to initialize Outlook: %w", err)
		}
		log.Println("Outlook COM provider initialized")
	}

	var aiClient *azureopenai.Client
	if cfg.AzureOpenAIEndpoint != "" {
		// Create AI client - uses DefaultAzureCredential if API key is empty
		aiClient, err = azureopenai.NewClient(
			cfg.AzureOpenAIEndpoint,
			cfg.AzureOpenAIAPIKey, // Empty string = use az login
			cfg.AzureOpenAIDeployment,
			cfg.PromptsDirectory,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to create AI client: %w", err)
		}
		log.Println("Azure OpenAI client initialized")
	} else {
		log.Println("Azure OpenAI endpoint not configured - AI features will be unavailable")
	}

	return &EmailService{
		outlookProvider: outlookProvider,
		aiClient:        aiClient,
		useComBackend:   cfg.UseComBackend,
	}, nil
}

// Close cleans up resources
func (s *EmailService) Close() error {
	if s.outlookProvider != nil {
		return s.outlookProvider.Close()
	}
	return nil
}

// GetEmails retrieves emails from either Outlook or database
func (s *EmailService) GetEmails(folder string, limit, offset int, source, category string) ([]*models.Email, int, error) {
	if source == "outlook" && s.useComBackend && s.outlookProvider != nil {
		emails, err := s.outlookProvider.GetEmails(folder, limit, offset)
		if err != nil {
			return nil, 0, fmt.Errorf("failed to get emails from Outlook: %w", err)
		}
		
		// Enrich Outlook emails with database data (AI classifications, etc.)
		enrichedEmails := s.enrichEmailsWithDatabaseData(emails)
		
		return enrichedEmails, len(enrichedEmails), nil
	}

	// Get from database
	emails, total, err := database.GetEmails(limit, offset, category)
	if err != nil {
		return nil, 0, fmt.Errorf("failed to get emails from database: %w", err)
	}
	return emails, total, nil
}

// GetEmailByID retrieves a specific email
func (s *EmailService) GetEmailByID(id, source string) (*models.Email, error) {
	if source == "outlook" && s.useComBackend && s.outlookProvider != nil {
		return s.outlookProvider.GetEmailByID(id)
	}
	return database.GetEmailByID(id)
}

// SearchEmails searches emails
func (s *EmailService) SearchEmails(query string, page, perPage int) ([]*models.Email, int, error) {
	return database.SearchEmails(query, page, perPage)
}

// MarkAsRead marks an email as read
func (s *EmailService) MarkAsRead(id string, read bool) error {
	if s.useComBackend && s.outlookProvider != nil {
		return s.outlookProvider.MarkAsRead(id, read)
	}
	return fmt.Errorf("COM backend not available")
}

// MoveToFolder moves an email to a folder
func (s *EmailService) MoveToFolder(id, folder string) error {
	if s.useComBackend && s.outlookProvider != nil {
		return s.outlookProvider.MoveToFolder(id, folder)
	}
	return fmt.Errorf("COM backend not available")
}

// UpdateClassification updates email classification
func (s *EmailService) UpdateClassification(id, category string, applyToOutlook bool) error {
	// First, check if email exists in database
	_, err := database.GetEmailByID(id)
	if err != nil {
		// Email doesn't exist in database, need to fetch from Outlook and insert it
		// Truncate ID for logging (max 30 chars)
		idLog := id
		if len(id) > 30 {
			idLog = id[:30] + "..."
		}
		log.Printf("[UpdateClassification] Email %s not in database, fetching from Outlook", idLog)
		
		if s.useComBackend && s.outlookProvider != nil {
			email, err := s.outlookProvider.GetEmailByID(id)
			if err != nil {
				return fmt.Errorf("failed to fetch email from Outlook: %w", err)
			}
			
		// Set the classification
		email.AICategory = category
		email.Category = category
		
		// Insert into database
		if err := database.SaveEmail(email); err != nil {
			return fmt.Errorf("failed to save email to database: %w", err)
		}
		// Truncate ID for logging (max 30 chars)
		idLog := id
		if len(id) > 30 {
			idLog = id[:30] + "..."
		}
		log.Printf("[UpdateClassification] Email %s inserted into database with category %s", idLog, category)
	} else {
		return fmt.Errorf("email not in database and COM backend not available")
	}
} else {
	// Email exists, update it
	if err := database.UpdateEmailClassification(id, category); err != nil {
		return fmt.Errorf("failed to update classification in database: %w", err)
	}
	// Truncate ID for logging (max 30 chars)
	idLog := id
	if len(id) > 30 {
		idLog = id[:30] + "..."
	}
	log.Printf("[UpdateClassification] Email %s classification updated to %s", idLog, category)
}

// Apply to Outlook if requested
if applyToOutlook && s.useComBackend && s.outlookProvider != nil {
	if err := s.outlookProvider.ApplyClassification(id, category); err != nil {
		log.Printf("[UpdateClassification] Failed to apply to Outlook: %v", err)
		// Don't fail the whole operation if Outlook update fails
	} else {
		// Truncate ID for logging (max 30 chars)
		idLog := id
		if len(id) > 30 {
			idLog = id[:30] + "..."
		}
		log.Printf("[UpdateClassification] Applied classification to Outlook for email %s", idLog)
	}
}

return nil
}

// BulkApplyToOutlook applies classifications to multiple emails
func (s *EmailService) BulkApplyToOutlook(emailIDs []string) (int, int, []string, error) {
	if !s.useComBackend || s.outlookProvider == nil {
		return 0, 0, nil, fmt.Errorf("COM backend not available")
	}

	successful := 0
	failed := 0
	var errors []string

	for _, emailID := range emailIDs {
		// Get email from database to get its category
		email, err := database.GetEmailByID(emailID)
		if err != nil {
			failed++
			errors = append(errors, fmt.Sprintf("Email %s: %v", emailID, err))
			continue
		}

		category := email.AICategory
		if email.Category != "" {
			category = email.Category
		}

		if err := s.outlookProvider.ApplyClassification(emailID, category); err != nil {
			failed++
			errors = append(errors, fmt.Sprintf("Email %s: %v", emailID, err))
		} else {
			successful++
		}
	}

	return successful, failed, errors, nil
}

// SyncToDatabase saves emails to database
func (s *EmailService) SyncToDatabase(emails []*models.Email) error {
	for _, email := range emails {
		if err := database.SaveEmail(email); err != nil {
			log.Printf("Failed to save email %s: %v", email.ID, err)
			// Continue with other emails
		}
	}
	return nil
}

// GetFolders retrieves email folders
func (s *EmailService) GetFolders() ([]models.EmailFolder, error) {
	if s.useComBackend && s.outlookProvider != nil {
		return s.outlookProvider.GetFolders()
	}
	return nil, fmt.Errorf("COM backend not available")
}

// GetConversation retrieves emails in a conversation
func (s *EmailService) GetConversation(conversationID, source string) ([]*models.Email, error) {
	if source == "outlook" && s.useComBackend && s.outlookProvider != nil {
		return s.outlookProvider.GetConversationEmails(conversationID)
	}
	return database.GetConversationEmails(conversationID)
}

// GetStats retrieves email statistics
func (s *EmailService) GetStats(limit int) (map[string]interface{}, error) {
	return database.GetEmailStats(limit)
}

// GetAccuracyStats retrieves AI accuracy statistics
func (s *EmailService) GetAccuracyStats() (map[string]interface{}, error) {
	return database.GetAccuracyStats()
}

// GetCategoryMappings returns category to folder mappings
func (s *EmailService) GetCategoryMappings() []models.CategoryFolderMapping {
	return outlook.GetCategoryMappings()
}

// enrichEmailsWithDatabaseData enriches Outlook emails with AI classifications from database
func (s *EmailService) enrichEmailsWithDatabaseData(emails []*models.Email) []*models.Email {
	enrichedCount := 0
	for _, email := range emails {
		if email == nil || email.ID == "" {
			continue
		}
		
		// Try to get email from database by ID
		dbEmail, err := database.GetEmailByID(email.ID)
		if err != nil {
			// Email not in database yet, skip enrichment
			continue
		}
		
		// Merge AI classification data from database
		enriched := false
		if dbEmail.AICategory != "" {
			email.AICategory = dbEmail.AICategory
			enriched = true
		}
		if dbEmail.AIConfidence > 0 {
			email.AIConfidence = dbEmail.AIConfidence
		}
		if dbEmail.AIReasoning != "" {
			email.AIReasoning = dbEmail.AIReasoning
		}
		if dbEmail.OneLineSummary != "" {
			email.OneLineSummary = dbEmail.OneLineSummary
		}
		if dbEmail.Category != "" {
			email.Category = dbEmail.Category
		}
		
		if enriched {
			enrichedCount++
		}
	}
	
	log.Printf("[Email Enrichment] Enriched %d/%d emails with database data", enrichedCount, len(emails))
	
	return emails
}

// ClassifyEmail classifies an email using AI
func (s *EmailService) ClassifyEmail(ctx context.Context, subject, sender, content, userContext string) (*models.AIClassificationResponse, error) {
	if s.aiClient == nil {
		return nil, fmt.Errorf("AI client not configured")
	}
	return s.aiClient.ClassifyEmail(ctx, subject, sender, content, userContext)
}

// ExtractActionItems extracts action items from email
func (s *EmailService) ExtractActionItems(ctx context.Context, emailContent, userContext string) (*models.ActionItemResponse, error) {
	if s.aiClient == nil {
		return nil, fmt.Errorf("AI client not configured")
	}
	return s.aiClient.ExtractActionItems(ctx, emailContent, userContext)
}

// SummarizeEmail generates email summary
func (s *EmailService) SummarizeEmail(ctx context.Context, emailContent, summaryType string) (*models.SummaryResponse, error) {
	if s.aiClient == nil {
		return nil, fmt.Errorf("AI client not configured")
	}
	return s.aiClient.Summarize(ctx, emailContent, summaryType)
}

// CheckAIHealth checks AI service health
func (s *EmailService) CheckAIHealth(ctx context.Context) error {
	if s.aiClient == nil {
		return fmt.Errorf("AI client not configured")
	}
	return s.aiClient.CheckHealth(ctx)
}

// AnalyzeHolistically performs holistic email analysis across multiple emails
// Identifies truly relevant actions, superseded items, duplicates, and expired deadlines
func (s *EmailService) AnalyzeHolistically(ctx context.Context, emailIDs []string) (*models.HolisticAnalysisResponse, error) {
	if s.aiClient == nil {
		return nil, fmt.Errorf("AI client not configured")
	}

	// Fetch emails by ID (try database first, then Outlook)
	emails := make([]*models.Email, 0, len(emailIDs))
	for _, emailID := range emailIDs {
		// Try database first, fallback to Outlook
		email, err := s.GetEmailByID(emailID, "database")
		if err != nil {
			// Try Outlook if database fetch failed
			email, err = s.GetEmailByID(emailID, "outlook")
			if err != nil {
				log.Printf("Failed to fetch email %s: %v", emailID, err)
				continue // Skip emails that can't be fetched
			}
		}
		emails = append(emails, email)
	}

	if len(emails) == 0 {
		return nil, fmt.Errorf("no valid emails found for analysis")
	}

	// Build inbox summary for AI analysis
	inboxSummary := buildInboxSummary(emails)

	// Call AI with holistic analyzer prompty
	return analyzeHolisticallyWithAI(ctx, s.aiClient, inboxSummary, len(emails))
}

// buildInboxSummary creates a formatted summary of emails for AI analysis
func buildInboxSummary(emails []*models.Email) string {
	var summary strings.Builder
	
	for i, email := range emails {
		summary.WriteString(fmt.Sprintf("Email %d:\n", i+1))
		summary.WriteString(fmt.Sprintf("  ID: %s\n", email.ID))
		summary.WriteString(fmt.Sprintf("  Subject: %s\n", email.Subject))
		summary.WriteString(fmt.Sprintf("  Sender: %s\n", email.Sender))
		summary.WriteString(fmt.Sprintf("  Date: %s\n", email.ReceivedTime))
		
		// Include a snippet of content (first 200 chars)
		content := email.Content
		if len(content) > 200 {
			content = content[:200] + "..."
		}
		summary.WriteString(fmt.Sprintf("  Content: %s\n", content))
		
		// Include classification if available
		if email.AICategory != "" {
			summary.WriteString(fmt.Sprintf("  Category: %s\n", email.AICategory))
		}
		if email.OneLineSummary != "" {
			summary.WriteString(fmt.Sprintf("  Summary: %s\n", email.OneLineSummary))
		}
		
		summary.WriteString("\n")
	}
	
	return summary.String()
}

// analyzeHolisticallyWithAI calls Azure OpenAI with the holistic analyzer prompt
func analyzeHolisticallyWithAI(ctx context.Context, aiClient AIClient, inboxSummary string, emailCount int) (*models.HolisticAnalysisResponse, error) {
	startTime := time.Now()
	
	// Load holistic_inbox_analyzer prompty template
	promptsDir := filepath.Join(".", "prompts")
	prompts, err := prompty.LoadPromptDirectory(promptsDir)
	if err != nil {
		// Try from parent directory
		promptsDir = filepath.Join("..", "prompts")
		prompts, err = prompty.LoadPromptDirectory(promptsDir)
		if err != nil {
			return nil, fmt.Errorf("failed to load prompty files: %w", err)
		}
	}

	tmpl, ok := prompts["holistic_inbox_analyzer"]
	if !ok {
		return nil, fmt.Errorf("holistic_inbox_analyzer.prompty template not found")
	}

	// Prepare template variables
	vars := map[string]string{
		"context":          "", // Optional user context
		"job_role_context": "Software Engineer", // TODO: Make configurable from settings
		"username":         "User", // TODO: Make configurable from settings
		"inbox_summary":    inboxSummary,
		"current_date":     time.Now().Format("2006-01-02"),
	}

	// Render prompts
	systemPrompt, err := tmpl.RenderPrompt("system", vars)
	if err != nil {
		return nil, fmt.Errorf("failed to render system prompt: %w", err)
	}

	userPrompt, err := tmpl.RenderPrompt("user", vars)
	if err != nil {
		return nil, fmt.Errorf("failed to render user prompt: %w", err)
	}

	// Prepare chat completions request
	messages := []azopenai.ChatRequestMessageClassification{
		&azopenai.ChatRequestSystemMessage{Content: to.Ptr(systemPrompt)},
		&azopenai.ChatRequestUserMessage{Content: azopenai.NewChatRequestUserMessageContent(userPrompt)},
	}

	options := azopenai.ChatCompletionsOptions{
		Messages:    messages,
		MaxTokens:   to.Ptr(tmpl.Model.Parameters.MaxTokens),
		Temperature: to.Ptr(tmpl.Model.Parameters.Temperature),
	}

	// Call AI client's GetChatCompletions method (exposed by azureopenai.Client)
	type AIClientWithCompletions interface {
		GetChatCompletions(ctx context.Context, options azopenai.ChatCompletionsOptions, opts *azopenai.GetChatCompletionsOptions) (azopenai.GetChatCompletionsResponse, error)
	}

	aiClientWithCompletions, ok := aiClient.(AIClientWithCompletions)
	if !ok {
		return nil, fmt.Errorf("AI client does not support GetChatCompletions")
	}

	resp, err := aiClientWithCompletions.GetChatCompletions(ctx, options, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to get AI completions: %w", err)
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

	// Parse JSON response into our model
	var analysisResult models.HolisticAnalysisResponse
	if err := json.Unmarshal([]byte(responseText), &analysisResult); err != nil {
		return nil, fmt.Errorf("failed to parse AI response: %w (response: %s)", err, responseText)
	}

	// Add metadata
	analysisResult.ProcessingTime = time.Since(startTime).Seconds()
	analysisResult.EmailsAnalyzed = emailCount

	return &analysisResult, nil
}
