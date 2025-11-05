package handlers

import (
	"fmt"
	"log"
	"net/http"
	"strconv"

	"email-helper-backend/internal/models"

	"github.com/gin-gonic/gin"
)

// GetEmails retrieves paginated list of emails
// Intelligently chooses data source based on query parameters:
// - If folder is explicitly specified: use Outlook (live folder data)
// - If category is specified: use database (filtered by AI classification)
// - Default: use Outlook for inbox browsing
func GetEmails(c *gin.Context) {
	folderProvided := c.Query("folder") != ""
	folder := c.DefaultQuery("folder", "Inbox")
	limitStr := c.DefaultQuery("limit", "50")
	offsetStr := c.DefaultQuery("offset", "0")
	category := c.Query("category")

	limit, _ := strconv.Atoi(limitStr)
	offset, _ := strconv.Atoi(offsetStr)

	if limit <= 0 || limit > 50000 {
		limit = 50
	}

	// Intelligently choose data source:
	// Priority: folder parameter > category parameter > default (outlook)
	// - If folder explicitly specified: use Outlook (live folder browsing)
	// - Else if category specified: use database (has AI classifications)
	// - Else: use Outlook (default inbox)
	source := "outlook"
	if !folderProvided && category != "" {
		source = "database"
	}

	emails, total, err := emailService.GetEmails(folder, limit, offset, source, category)
	if err != nil {
		DatabaseError(c, "Failed to retrieve emails: "+err.Error())
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
		NotFound(c, models.ErrorCodeEmailNotFound, "Email not found: "+id)
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
		DatabaseError(c, "Search failed: "+err.Error())
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
		DatabaseError(c, "Failed to retrieve statistics: "+err.Error())
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
		DatabaseError(c, "Failed to retrieve accuracy statistics: "+err.Error())
		return
	}

	c.JSON(http.StatusOK, stats)
}

// PrefetchEmails prefetches multiple emails
func PrefetchEmails(c *gin.Context) {
	var emailIDs []string
	if err := c.ShouldBindJSON(&emailIDs); err != nil {
		BadRequest(c, "Invalid request body: "+err.Error())
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
		OutlookError(c, "Failed to update read status: "+err.Error())
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
		OutlookError(c, "Failed to mark as read: "+err.Error())
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
		ValidationError(c, "Missing required parameter", "destination_folder is required")
		return
	}

	if err := emailService.MoveToFolder(id, destination); err != nil {
		OutlookError(c, "Failed to move email: "+err.Error())
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
		BadRequest(c, "Invalid request body: "+err.Error())
		return
	}

	if err := emailService.UpdateClassification(id, req.Category, req.ApplyToOutlook); err != nil {
		DatabaseError(c, "Failed to update classification: "+err.Error())
		return
	}

	c.JSON(http.StatusOK, models.EmailOperationResponse{
		Success: true,
		Message: "Classification updated",
		EmailID: id,
	})
}

// ApplyClassifications applies classifications to multiple emails (new plural naming)
func ApplyClassifications(c *gin.Context) {
	var req models.BulkApplyRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		BadRequest(c, "Invalid request body: "+err.Error())
		return
	}

	successful, failed, errors, err := emailService.BulkApplyToOutlook(req.EmailIDs)
	if err != nil {
		OutlookError(c, "Failed to apply classifications: "+err.Error())
		return
	}

	c.JSON(http.StatusOK, models.BatchOperationResponse{
		Success:    failed == 0,
		Processed:  len(req.EmailIDs),
		Successful: successful,
		Failed:     failed,
		Errors:     errors,
	})
}

// BulkApplyToOutlook applies classifications to multiple emails
// Deprecated: Use POST /api/emails/classifications/apply instead
func BulkApplyToOutlook(c *gin.Context) {
	// Add deprecation header
	c.Header("X-Deprecated", "true")
	c.Header("X-Deprecated-Message", "Use POST /api/emails/classifications/apply instead")
	
	var req models.BulkApplyRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		BadRequest(c, "Invalid request body: "+err.Error())
		return
	}

	successful, failed, errors, err := emailService.BulkApplyToOutlook(req.EmailIDs)
	if err != nil {
		OutlookError(c, "Failed to apply classifications: "+err.Error())
		return
	}

	c.JSON(http.StatusOK, models.BatchOperationResponse{
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
		BadRequest(c, "Invalid request body: "+err.Error())
		return
	}

	// Convert []models.Email to []*models.Email
	emails := make([]*models.Email, len(req.Emails))
	for i := range req.Emails {
		emails[i] = &req.Emails[i]
	}

	if err := emailService.SyncToDatabase(emails); err != nil {
		DatabaseError(c, "Failed to sync emails to database: "+err.Error())
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
		OutlookError(c, "Failed to retrieve folders: "+err.Error())
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
		DatabaseError(c, "Failed to retrieve conversation thread: "+err.Error())
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
	EmailIDs       []string `json:"email_ids" binding:"required"`
	SaveToDatabase bool     `json:"save_to_database"`
}

// BatchProcessEmails handles batch email processing with AI classification and action items extraction
// Deprecated: Use POST /api/ai/classifications instead
func BatchProcessEmails(c *gin.Context) {
	// Add deprecation header
	c.Header("X-Deprecated", "true")
	c.Header("X-Deprecated-Message", "Use POST /api/ai/classifications instead")
	
	var req BatchProcessRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		BadRequest(c, "Invalid request body: "+err.Error())
		return
	}

	ctx := c.Request.Context()
	results := make([]models.BatchItemResult, 0, len(req.EmailIDs))
	successCount := 0
	failedCount := 0

	// Categories that should extract action items
	actionableCategories := map[string]bool{
		"required_personal_action": true,
		"team_action":              true,
	}

	for _, emailID := range req.EmailIDs {
		itemResult := models.BatchItemResult{
			ItemID:  emailID,
			Success: false,
			Data:    make(map[string]interface{}),
		}

		// Get email details
		email, err := emailService.GetEmailByID(emailID, "outlook")
		if err != nil {
			itemResult.Error = fmt.Sprintf("Failed to get email: %v", err)
			results = append(results, itemResult)
			failedCount++
			continue
		}

		itemResult.Data["subject"] = email.Subject

		// Classify email using AI
		classification, err := emailService.ClassifyEmail(ctx, email.Subject, email.Sender, email.Content, "")
		if err != nil {
			itemResult.Error = fmt.Sprintf("Failed to classify: %v", err)
			results = append(results, itemResult)
			failedCount++
			continue
		}

		// Update result with classification
		itemResult.Data["category"] = classification.Category
		if classification.Confidence != nil {
			itemResult.Data["confidence"] = *classification.Confidence
		}
		itemResult.Data["one_line_summary"] = classification.OneLineSummary
		itemResult.Data["reasoning"] = classification.Reasoning

		// Calculate priority based on category and confidence
		confidence := 0.0
		if classification.Confidence != nil {
			confidence = *classification.Confidence
		}
		priority := calculateEmailPriority(classification.Category, confidence)
		itemResult.Data["priority"] = priority

		// Extract action items for actionable categories
		if actionableCategories[classification.Category] {
			actionItems, err := emailService.ExtractActionItems(ctx, email.Content, "")
			if err == nil && len(actionItems.ActionItems) > 0 {
				itemResult.Data["action_items"] = actionItems.ActionItems
			}
		}

		// Update email with classification results
		email.AICategory = classification.Category
		email.AIConfidence = confidence
		email.AIReasoning = classification.Reasoning
		email.OneLineSummary = classification.OneLineSummary

		// Save to database if requested
		if req.SaveToDatabase {
			if err := emailService.SyncToDatabase([]*models.Email{email}); err != nil {
				log.Printf("Warning: Failed to save email %s to database: %v", emailID, err)
				// Don't fail the whole operation if DB save fails
			}
		}

		itemResult.Success = true
		results = append(results, itemResult)
		successCount++
	}

	// Build standardized response
	response := models.BatchOperationResponse{
		Success:    failedCount == 0,
		Processed:  len(req.EmailIDs),
		Successful: successCount,
		Failed:     failedCount,
		Results:    results,
	}

	// Return 200 OK even with partial failures (partial success pattern)
	c.JSON(http.StatusOK, response)
}

// calculateEmailPriority determines priority based on category and confidence
func calculateEmailPriority(category string, confidence float64) string {
	// High priority categories
	if category == "required_personal_action" && confidence > 0.8 {
		return "high"
	}
	if category == "team_action" && confidence > 0.75 {
		return "high"
	}

	// Medium priority categories
	if category == "required_personal_action" || category == "team_action" {
		return "medium"
	}
	if category == "optional_event" && confidence > 0.7 {
		return "medium"
	}

	// Low priority categories
	if category == "fyi" || category == "newsletter" || category == "optional_event" {
		return "low"
	}

	// Spam and job listings are lowest priority
	if category == "spam_to_delete" || category == "job_listing" {
		return "low"
	}

	return "medium" // default
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
		BadRequest(c, "Invalid request body: "+err.Error())
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
		actionItems, err := emailService.ExtractActionItems(ctx, email.Content, "")
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

// AnalyzeHolistically performs holistic email analysis across multiple emails
// Identifies truly relevant actions, superseded items, duplicates, and expired deadlines
func AnalyzeHolistically(c *gin.Context) {
	var req models.HolisticAnalysisRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		BadRequest(c, "Invalid request body: "+err.Error())
		return
	}

	if len(req.EmailIDs) == 0 {
		ValidationError(c, "Invalid request", "email_ids cannot be empty")
		return
	}

	// Get email service
	if emailService == nil {
		InternalError(c, "Email service not initialized")
		return
	}

	// Call email service to perform holistic analysis
	result, err := emailService.AnalyzeHolistically(c.Request.Context(), req.EmailIDs)
	if err != nil {
		log.Printf("Holistic analysis failed: %v", err)
		AIServiceError(c, "AI analysis failed: "+err.Error())
		return
	}

	c.JSON(http.StatusOK, result)
}

