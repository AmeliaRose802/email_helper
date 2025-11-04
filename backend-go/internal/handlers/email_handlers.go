package handlers

import (
	"fmt"
	"net/http"
	"strconv"

	"email-helper-backend/internal/models"

	"github.com/gin-gonic/gin"
)

// GetEmails retrieves paginated list of emails
func GetEmails(c *gin.Context) {
	folder := c.DefaultQuery("folder", "Inbox")
	limitStr := c.DefaultQuery("limit", "50")
	offsetStr := c.DefaultQuery("offset", "0")
	category := c.Query("category")
	source := c.DefaultQuery("source", "outlook")

	limit, _ := strconv.Atoi(limitStr)
	offset, _ := strconv.Atoi(offsetStr)

	if limit <= 0 || limit > 50000 {
		limit = 50
	}

	emails, total, err := emailService.GetEmails(folder, limit, offset, source, category)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	hasMore := offset+limit < total

	// Convert []*models.Email to []models.Email
	emailList := make([]models.Email, len(emails))
	for i, e := range emails {
		if e != nil {
			emailList[i] = *e
		}
	}

	c.JSON(http.StatusOK, models.EmailListResponse{
		Emails:  emailList,
		Total:   total,
		Offset:  offset,
		Limit:   limit,
		HasMore: hasMore,
	})
}

// GetEmail retrieves a specific email
func GetEmail(c *gin.Context) {
	id := c.Param("id")
	source := c.DefaultQuery("source", "outlook")

	email, err := emailService.GetEmailByID(id, source)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Email not found"})
		return
	}

	c.JSON(http.StatusOK, email)
}

// SearchEmails searches emails
func SearchEmails(c *gin.Context) {
	query := c.Query("q")
	pageStr := c.DefaultQuery("page", "1")
	perPageStr := c.DefaultQuery("per_page", "20")

	page, _ := strconv.Atoi(pageStr)
	perPage, _ := strconv.Atoi(perPageStr)

	if page < 1 {
		page = 1
	}
	if perPage < 1 || perPage > 100 {
		perPage = 20
	}

	emails, total, err := emailService.SearchEmails(query, page, perPage)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	offset := (page - 1) * perPage
	hasMore := offset+perPage < total

	// Convert []*models.Email to []models.Email
	emailList := make([]models.Email, len(emails))
	for i, e := range emails {
		if e != nil {
			emailList[i] = *e
		}
	}

	c.JSON(http.StatusOK, models.EmailListResponse{
		Emails:  emailList,
		Total:   total,
		Offset:  offset,
		Limit:   perPage,
		HasMore: hasMore,
	})
}

// GetEmailStats retrieves email statistics
func GetEmailStats(c *gin.Context) {
	limitStr := c.DefaultQuery("limit", "100")
	limit, _ := strconv.Atoi(limitStr)

	stats, err := emailService.GetStats(limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, stats)
}

// GetCategoryMappings returns category to folder mappings
func GetCategoryMappings(c *gin.Context) {
	mappings := emailService.GetCategoryMappings()
	// Return array directly (not wrapped) to match frontend expectations
	c.JSON(http.StatusOK, mappings)
}

// GetAccuracyStats returns AI accuracy statistics
func GetAccuracyStats(c *gin.Context) {
	stats, err := emailService.GetAccuracyStats()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, stats)
}

// PrefetchEmails prefetches multiple emails
func PrefetchEmails(c *gin.Context) {
	var emailIDs []string
	if err := c.ShouldBindJSON(&emailIDs); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	var emails []*models.Email
	var errors []string
	successCount := 0
	errorCount := 0

	for _, id := range emailIDs {
		email, err := emailService.GetEmailByID(id, "outlook")
		if err != nil {
			errors = append(errors, err.Error())
			errorCount++
		} else {
			emails = append(emails, email)
			successCount++
		}
	}

	c.JSON(http.StatusOK, gin.H{
		"emails":        emails,
		"success_count": successCount,
		"error_count":   errorCount,
		"errors":        errors,
	})
}

// UpdateEmailReadStatus updates email read status
func UpdateEmailReadStatus(c *gin.Context) {
	id := c.Param("id")
	readStr := c.DefaultQuery("read", "true")
	read := readStr == "true"

	if err := emailService.MarkAsRead(id, read); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, models.EmailOperationResponse{
		Success: true,
		Message: "Status updated",
		EmailID: id,
	})
}

// MarkEmailAsRead marks email as read (deprecated, use UpdateEmailReadStatus)
func MarkEmailAsRead(c *gin.Context) {
	id := c.Param("id")

	if err := emailService.MarkAsRead(id, true); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, models.EmailOperationResponse{
		Success: true,
		Message: "Marked as read",
		EmailID: id,
	})
}

// MoveEmail moves email to folder
func MoveEmail(c *gin.Context) {
	id := c.Param("id")
	destination := c.Query("destination_folder")

	if destination == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "destination_folder required"})
		return
	}

	if err := emailService.MoveToFolder(id, destination); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, models.EmailOperationResponse{
		Success: true,
		Message: "Email moved",
		EmailID: id,
	})
}

// UpdateEmailClassification updates email classification
func UpdateEmailClassification(c *gin.Context) {
	id := c.Param("id")
	
	var req models.UpdateClassificationRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if err := emailService.UpdateClassification(id, req.Category, req.ApplyToOutlook); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, models.EmailOperationResponse{
		Success: true,
		Message: "Classification updated",
		EmailID: id,
	})
}

// BulkApplyToOutlook applies classifications to multiple emails
func BulkApplyToOutlook(c *gin.Context) {
	var req models.BulkApplyRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	successful, failed, errors, err := emailService.BulkApplyToOutlook(req.EmailIDs)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, models.BulkApplyResponse{
		Success:    failed == 0,
		Processed:  len(req.EmailIDs),
		Successful: successful,
		Failed:     failed,
		Errors:     errors,
	})
}

// SyncToDatabase syncs emails to database
func SyncToDatabase(c *gin.Context) {
	var req models.SyncEmailRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Convert []models.Email to []*models.Email
	emails := make([]*models.Email, len(req.Emails))
	for i := range req.Emails {
		emails[i] = &req.Emails[i]
	}

	if err := emailService.SyncToDatabase(emails); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Emails synced to database",
		"count":   len(req.Emails),
	})
}

// GetFolders retrieves email folders
func GetFolders(c *gin.Context) {
	folders, err := emailService.GetFolders()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, models.EmailFolderResponse{
		Folders: folders,
		Total:   len(folders),
	})
}

// GetConversationThread retrieves conversation thread
func GetConversationThread(c *gin.Context) {
	id := c.Param("id")
	source := c.DefaultQuery("source", "outlook")

	emails, err := emailService.GetConversation(id, source)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Convert []*models.Email to []models.Email
	emailList := make([]models.Email, len(emails))
	for i, e := range emails {
		if e != nil {
			emailList[i] = *e
		}
	}

	c.JSON(http.StatusOK, models.ConversationResponse{
		ConversationID: id,
		Emails:         emailList,
		Total:          len(emails),
	})
}

// BatchProcessRequest request for batch processing emails
type BatchProcessRequest struct {
	EmailIDs []string `json:"email_ids" binding:"required"`
	SaveToDatabase bool `json:"save_to_database"`
}

// BatchProcessEmails handles batch email processing
func BatchProcessEmails(c *gin.Context) {
	var req BatchProcessRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	ctx := c.Request.Context()
	var processedEmails []models.Email
	var errors []string
	successCount := 0
	errorCount := 0

	for _, emailID := range req.EmailIDs {
		// Get email details
		email, err := emailService.GetEmailByID(emailID, "outlook")
		if err != nil {
			errors = append(errors, fmt.Sprintf("Email %s: failed to get email: %v", emailID, err))
			errorCount++
			continue
		}

		// Classify email using AI
		classification, err := emailService.ClassifyEmail(ctx, email.Subject, email.Sender, email.Body, "")
		if err != nil {
			errors = append(errors, fmt.Sprintf("Email %s: failed to classify: %v", emailID, err))
			errorCount++
			continue
		}

		// Update email with classification results
		email.AICategory = classification.Category
		email.AIConfidence = *classification.Confidence
		email.AIReasoning = classification.Reasoning
		email.OneLineSummary = classification.OneLineSummary

		// Save to database if requested
		if req.SaveToDatabase {
			if err := emailService.SyncToDatabase([]*models.Email{email}); err != nil {
				errors = append(errors, fmt.Sprintf("Email %s: failed to save to database: %v", emailID, err))
				errorCount++
			}
		}

		processedEmails = append(processedEmails, *email)
		successCount++
	}

	c.JSON(http.StatusOK, gin.H{
		"success":        errorCount == 0,
		"emails":         processedEmails,
		"total":          len(processedEmails),
		"processed":      len(req.EmailIDs),
		"success_count":  successCount,
		"error_count":    errorCount,
		"errors":         errors,
	})
}

// ExtractTasksRequest request for extracting tasks from emails
type ExtractTasksRequest struct {
	EmailIDs        []string `json:"email_ids" binding:"required"`
	ApplyToOutlook  bool     `json:"apply_to_outlook"`
}

// ExtractTasks extracts tasks from emails
func ExtractTasks(c *gin.Context) {
	var req ExtractTasksRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	ctx := c.Request.Context()
	var extractedTasks []models.Task
	var errors []string
	successCount := 0
	errorCount := 0

	for _, emailID := range req.EmailIDs {
		// Get email details from database (already synced)
		email, err := emailService.GetEmailByID(emailID, "database")
		if err != nil {
			errors = append(errors, fmt.Sprintf("Email %s: failed to get email: %v", emailID, err))
			errorCount++
			continue
		}

		// Extract action items using AI
		actionItems, err := emailService.ExtractActionItems(ctx, email.Body, "")
		if err != nil {
			errors = append(errors, fmt.Sprintf("Email %s: failed to extract tasks: %v", emailID, err))
			errorCount++
			continue
		}

		// Create tasks from action items
		for _, item := range actionItems.ActionItems {
			priority := "medium"
			if actionItems.Urgency == "high" || actionItems.Urgency == "urgent" {
				priority = "high"
			} else if actionItems.Urgency == "low" {
				priority = "low"
			}

			task := models.TaskCreate{
				Title:       item,
				Description: fmt.Sprintf("From email: %s", email.Subject),
				Status:      "pending",
				Priority:    priority,
				EmailID:     &emailID,
				Category:    email.AICategory,
			}

			// Parse due date if available
			if actionItems.DueDate != nil && *actionItems.DueDate != "" {
				// Note: Date parsing would need to be implemented based on format
				// For now, we'll skip it
			}

			createdTask, err := taskService.CreateTask(&task)
			if err != nil {
				errors = append(errors, fmt.Sprintf("Email %s: failed to create task: %v", emailID, err))
				errorCount++
			} else {
				extractedTasks = append(extractedTasks, *createdTask)
				successCount++
			}
		}
	}

	c.JSON(http.StatusOK, gin.H{
		"success":        errorCount == 0,
		"tasks":          extractedTasks,
		"total_tasks":    len(extractedTasks),
		"emails_processed": len(req.EmailIDs),
		"success_count":  successCount,
		"error_count":    errorCount,
		"errors":         errors,
	})
}

// AnalyzeHolistically performs holistic email analysis (stub for now)
func AnalyzeHolistically(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"error": "Not implemented yet"})
}
