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

// ClassifyEmail handles email classification
func ClassifyEmail(c *gin.Context) {
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

// SummarizeEmail handles email summarization
func SummarizeEmail(c *gin.Context) {
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

// ClassifyBatchStream handles batch classification with Server-Sent Events (SSE) streaming
func ClassifyBatchStream(c *gin.Context) {
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

