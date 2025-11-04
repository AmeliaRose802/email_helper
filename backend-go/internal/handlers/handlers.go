package handlers

import (
	"context"
"net/http"
"email-helper-backend/internal/models"
"email-helper-backend/internal/services"
"github.com/gin-gonic/gin"
)

// EmailServiceInterface defines methods for email operations
type EmailServiceInterface interface {
	GetEmails(folder string, limit, offset int, source, category string) ([]*models.Email, int, error)
	GetEmailByID(id, source string) (*models.Email, error)
	SearchEmails(query string, page, perPage int) ([]*models.Email, int, error)
	MarkAsRead(id string, read bool) error
	MoveToFolder(id, folder string) error
	UpdateClassification(id, category string, applyToOutlook bool) error
	BulkApplyToOutlook(emailIDs []string) (int, int, []string, error)
	SyncToDatabase(emails []*models.Email) error
	GetFolders() ([]models.EmailFolder, error)
	GetConversation(conversationID, source string) ([]*models.Email, error)
	GetStats(limit int) (map[string]interface{}, error)
	GetAccuracyStats() (map[string]interface{}, error)
	GetCategoryMappings() []models.CategoryFolderMapping
	ClassifyEmail(ctx context.Context, subject, sender, content, userContext string) (*models.AIClassificationResponse, error)
	ExtractActionItems(ctx context.Context, emailContent, userContext string) (*models.ActionItemResponse, error)
	SummarizeEmail(ctx context.Context, emailContent, summaryType string) (*models.SummaryResponse, error)
	CheckAIHealth(ctx context.Context) error
	Close() error
}

// TaskServiceInterface defines methods for task operations
type TaskServiceInterface interface {
	CreateTask(task *models.TaskCreate) (*models.Task, error)
	GetTask(id int) (*models.Task, error)
	GetTasks(page, limit int, status, priority, search string) ([]*models.Task, int, error)
	UpdateTask(id int, update *models.TaskUpdate) (*models.Task, error)
	DeleteTask(id int) error
	GetStats() (map[string]interface{}, error)
	BulkUpdate(taskIDs []int, update *models.TaskUpdate) error
	BulkDelete(taskIDs []int) error
	GetTasksByEmail(emailID string) ([]*models.Task, error)
}

// SettingsServiceInterface defines methods for settings operations
type SettingsServiceInterface interface {
	GetSettings() (*models.UserSettings, error)
	UpdateSettings(settings *models.UserSettings) error
	ResetSettings() error
}

var (
emailService    EmailServiceInterface
taskService     TaskServiceInterface
settingsService SettingsServiceInterface
)

func InitializeServices(es *services.EmailService, ts *services.TaskService, ss *services.SettingsService) {
emailService = es
taskService = ts
settingsService = ss
}

func HealthCheck(c *gin.Context) {
c.JSON(http.StatusOK, gin.H{"status": "healthy", "service": "email-helper-api", "version": "1.0.0", "database": "healthy"})
}

func Root(c *gin.Context) {
c.JSON(http.StatusOK, gin.H{"message": "Email Helper API", "version": "1.0.0", "docs": "/docs", "health": "/health"})
}