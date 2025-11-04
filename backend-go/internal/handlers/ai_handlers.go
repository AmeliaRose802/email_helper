package handlers

import (
	"context"
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

// ClassifyBatchStream handles batch classification with streaming (stub for now)
func ClassifyBatchStream(c *gin.Context) {
	// TODO: Implement streaming batch classification
	c.JSON(http.StatusNotImplemented, gin.H{"error": "Streaming not yet implemented"})
}
