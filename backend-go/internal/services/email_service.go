package services

import (
	"context"
	"fmt"
	"log"

	"email-helper-backend/config"
	"email-helper-backend/internal/database"
	"email-helper-backend/internal/models"
	"email-helper-backend/pkg/azureopenai"
	"email-helper-backend/pkg/outlook"
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
