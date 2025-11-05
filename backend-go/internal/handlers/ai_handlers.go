package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"email-helper-backend/internal/models"
	"email-helper-backend/pkg/azureopenai"

	"github.com/gin-gonic/gin"
)

// ClassifyEmail handles email classification (deprecated: use ClassifyEmailSingular instead)
func ClassifyEmail(c *gin.Context) {
	// Add deprecation header
	c.Header("X-Deprecation-Warning", "This endpoint is deprecated. Use POST /api/ai/classification instead")
	c.Header("X-Sunset", "2025-05-01")
	
	ClassifyEmailSingular(c)
}

// ClassifyEmailSingular handles single email classification (new consistent naming)
func ClassifyEmailSingular(c *gin.Context) {
	var req models.AIClassificationRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	result, err := emailService.ClassifyEmail(ctx, req.Subject, req.Sender, req.Content, req.Context)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, result)
}

// ExtractActionItems handles action item extraction
func ExtractActionItems(c *gin.Context) {
	var req models.ActionItemRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	result, err := emailService.ExtractActionItems(ctx, req.EmailContent, req.Context)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, result)
}

// SummarizeEmail handles email summarization (deprecated: use SummarizeEmailSingular instead)
func SummarizeEmail(c *gin.Context) {
	// Add deprecation header
	c.Header("X-Deprecation-Warning", "This endpoint is deprecated. Use POST /api/ai/summary instead")
	c.Header("X-Sunset", "2025-05-01")
	
	SummarizeEmailSingular(c)
}

// SummarizeEmailSingular handles single email summarization (new consistent naming)
func SummarizeEmailSingular(c *gin.Context) {
	var req models.SummaryRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	summaryType := req.SummaryType
	if summaryType == "" {
		summaryType = "brief"
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	result, err := emailService.SummarizeEmail(ctx, req.EmailContent, summaryType)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, result)
}

// GetAvailableTemplates returns available prompt templates
func GetAvailableTemplates(c *gin.Context) {
	templates := azureopenai.GetAvailableTemplates()
	
	c.JSON(http.StatusOK, gin.H{
		"templates":    []string{"classification", "action_items", "summarization"},
		"descriptions": templates,
	})
}

// AIHealthCheck checks AI service health
func AIHealthCheck(c *gin.Context) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := emailService.CheckAIHealth(ctx); err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "AI service unavailable"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "healthy"})
}

// ClassifyBatchStreamRequest request for batch streaming classification
type ClassifyBatchStreamRequest struct {
	EmailIDs []string `json:"email_ids" binding:"required"`
	Context  string   `json:"context"`
}

// ClassifyBatchStreamEvent represents a single SSE event during batch classification
type ClassifyBatchStreamEvent struct {
	Current  int     `json:"current"`
	Total    int     `json:"total"`
	Status   string  `json:"status"` // 'processing', 'completed', 'error'
	EmailID  string  `json:"email_id,omitempty"`
	Category string  `json:"category,omitempty"`
	Message  string  `json:"message,omitempty"`
	Error    string  `json:"error,omitempty"`
	Progress float64 `json:"progress,omitempty"` // 0-100
}

// ClassifyBatchStream handles batch classification with Server-Sent Events (SSE) streaming (deprecated)
func ClassifyBatchStream(c *gin.Context) {
	// Add deprecation header
	c.Header("X-Deprecation-Warning", "This endpoint is deprecated. Use POST /api/ai/classifications/stream instead")
	c.Header("X-Sunset", "2025-05-01")
	
	ClassifyBatchStreamNew(c)
}

// ClassifyBatchStreamNew handles batch classification with Server-Sent Events (SSE) streaming
func ClassifyBatchStreamNew(c *gin.Context) {
	var req ClassifyBatchStreamRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if len(req.EmailIDs) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "email_ids cannot be empty"})
		return
	}

	// Set headers for SSE
	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")
	c.Header("Transfer-Encoding", "chunked")
	c.Header("X-Accel-Buffering", "no") // Disable nginx buffering

	ctx := c.Request.Context()
	total := len(req.EmailIDs)
	successCount := 0
	errorCount := 0

	// Helper function to write SSE events
	writeEvent := func(event ClassifyBatchStreamEvent) {
		data, _ := json.Marshal(event)
		fmt.Fprintf(c.Writer, "data: %s\n\n", data)
		c.Writer.Flush()
	}

	// Send start event
	writeEvent(ClassifyBatchStreamEvent{
		Current:  0,
		Total:    total,
		Status:   "processing",
		Message:  fmt.Sprintf("Starting batch classification of %d emails...", total),
		Progress: 0,
	})

	// Process each email
	for idx, emailID := range req.EmailIDs {
		current := idx + 1
		progress := float64(current) / float64(total) * 100

		// Send processing event
		writeEvent(ClassifyBatchStreamEvent{
			Current:  current,
			Total:    total,
			Status:   "processing",
			EmailID:  emailID,
			Message:  fmt.Sprintf("Classifying email %d/%d...", current, total),
			Progress: progress,
		})

		// Get email details
		email, err := emailService.GetEmailByID(emailID, "outlook")
		if err != nil {
			errorCount++
			writeEvent(ClassifyBatchStreamEvent{
				Current:  current,
				Total:    total,
				Status:   "error",
				EmailID:  emailID,
				Error:    fmt.Sprintf("Failed to get email: %v", err),
				Message:  fmt.Sprintf("Error classifying email %d/%d", current, total),
				Progress: progress,
			})
			continue
		}

		// Classify email using AI
		classification, err := emailService.ClassifyEmail(ctx, email.Subject, email.Sender, email.Content, req.Context)
		if err != nil {
			errorCount++
			writeEvent(ClassifyBatchStreamEvent{
				Current:  current,
				Total:    total,
				Status:   "error",
				EmailID:  emailID,
				Error:    fmt.Sprintf("Failed to classify: %v", err),
				Message:  fmt.Sprintf("Error classifying email %d/%d", current, total),
				Progress: progress,
			})
			continue
		}

		successCount++

		// Send success event
		writeEvent(ClassifyBatchStreamEvent{
			Current:  current,
			Total:    total,
			Status:   "completed",
			EmailID:  emailID,
			Category: classification.Category,
			Message:  fmt.Sprintf("Classified email %d/%d as '%s'", current, total, classification.Category),
			Progress: progress,
		})
	}

	// Send final completion event
	writeEvent(ClassifyBatchStreamEvent{
		Current:  total,
		Total:    total,
		Status:   "completed",
		Message:  fmt.Sprintf("Batch classification complete: %d successful, %d failed", successCount, errorCount),
		Progress: 100,
	})
}

// BatchClassificationRequest request for batch classification (non-streaming)
type BatchClassificationRequest struct {
	EmailIDs []string `json:"email_ids" binding:"required"`
	Context  string   `json:"context"`
}

// BatchClassificationResult represents a single classification result in batch
type BatchClassificationResult struct {
	EmailID        string                            `json:"email_id"`
	Success        bool                              `json:"success"`
	Classification *models.AIClassificationResponse  `json:"classification,omitempty"`
	Error          string                            `json:"error,omitempty"`
}

// BatchClassificationResponse response for batch classification
type BatchClassificationResponse struct {
	Total        int                          `json:"total"`
	Successful   int                          `json:"successful"`
	Failed       int                          `json:"failed"`
	Results      []BatchClassificationResult  `json:"results"`
}

// ClassifyEmailsBatch handles batch classification (non-streaming) - returns all results at once
func ClassifyEmailsBatch(c *gin.Context) {
	var req BatchClassificationRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if len(req.EmailIDs) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "email_ids cannot be empty"})
		return
	}

	ctx := c.Request.Context()
	results := make([]BatchClassificationResult, 0, len(req.EmailIDs))
	successCount := 0
	failedCount := 0

	for _, emailID := range req.EmailIDs {
		result := BatchClassificationResult{
			EmailID: emailID,
			Success: false,
		}

		// Get email details
		email, err := emailService.GetEmailByID(emailID, "outlook")
		if err != nil {
			result.Error = fmt.Sprintf("Failed to get email: %v", err)
			results = append(results, result)
			failedCount++
			continue
		}

		// Classify email using AI
		classification, err := emailService.ClassifyEmail(ctx, email.Subject, email.Sender, email.Content, req.Context)
		if err != nil {
			result.Error = fmt.Sprintf("Failed to classify: %v", err)
			results = append(results, result)
			failedCount++
			continue
		}

		result.Success = true
		result.Classification = classification
		results = append(results, result)
		successCount++
	}

	response := BatchClassificationResponse{
		Total:      len(req.EmailIDs),
		Successful: successCount,
		Failed:     failedCount,
		Results:    results,
	}

	c.JSON(http.StatusOK, response)
}

// BatchSummaryRequest request for batch summarization
type BatchSummaryRequest struct {
	EmailIDs    []string `json:"email_ids" binding:"required"`
	SummaryType string   `json:"summary_type"` // brief, detailed, or key_points
}

// BatchSummaryResult represents a single summary result in batch
type BatchSummaryResult struct {
	EmailID string                   `json:"email_id"`
	Success bool                     `json:"success"`
	Summary *models.SummaryResponse  `json:"summary,omitempty"`
	Error   string                   `json:"error,omitempty"`
}

// BatchSummaryResponse response for batch summarization
type BatchSummaryResponse struct {
	Total      int                  `json:"total"`
	Successful int                  `json:"successful"`
	Failed     int                  `json:"failed"`
	Results    []BatchSummaryResult `json:"results"`
}

// SummarizeEmailsBatch handles batch email summarization - returns all results at once
func SummarizeEmailsBatch(c *gin.Context) {
	var req BatchSummaryRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if len(req.EmailIDs) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "email_ids cannot be empty"})
		return
	}

	summaryType := req.SummaryType
	if summaryType == "" {
		summaryType = "brief"
	}

	ctx := c.Request.Context()
	results := make([]BatchSummaryResult, 0, len(req.EmailIDs))
	successCount := 0
	failedCount := 0

	for _, emailID := range req.EmailIDs {
		result := BatchSummaryResult{
			EmailID: emailID,
			Success: false,
		}

		// Get email details
		email, err := emailService.GetEmailByID(emailID, "outlook")
		if err != nil {
			result.Error = fmt.Sprintf("Failed to get email: %v", err)
			results = append(results, result)
			failedCount++
			continue
		}

		// Summarize email using AI
		summary, err := emailService.SummarizeEmail(ctx, email.Content, summaryType)
		if err != nil {
			result.Error = fmt.Sprintf("Failed to summarize: %v", err)
			results = append(results, result)
			failedCount++
			continue
		}

		result.Success = true
		result.Summary = summary
		results = append(results, result)
		successCount++
	}

	response := BatchSummaryResponse{
		Total:      len(req.EmailIDs),
		Successful: successCount,
		Failed:     failedCount,
		Results:    results,
	}

	c.JSON(http.StatusOK, response)
}

