package handlers

import (
	"github.com/gin-gonic/gin"
)

// StartProcessing starts a processing pipeline
func StartProcessing(c *gin.Context) {
	// TODO: Implement processing pipeline
	NotImplemented(c, "Processing pipeline not implemented yet")
}

// GetProcessingStatus retrieves pipeline status
func GetProcessingStatus(c *gin.Context) {
	NotImplemented(c, "Processing status not implemented yet")
}

// GetPipelineJobs retrieves pipeline jobs
func GetPipelineJobs(c *gin.Context) {
	NotImplemented(c, "Pipeline jobs not implemented yet")
}

// CancelProcessing cancels a processing pipeline
func CancelProcessing(c *gin.Context) {
	NotImplemented(c, "Pipeline cancellation not implemented yet")
}

// GetProcessingStats retrieves processing statistics
func GetProcessingStats(c *gin.Context) {
	NotImplemented(c, "Processing statistics not implemented yet")
}

// WebSocketPipeline handles WebSocket for specific pipeline
func WebSocketPipeline(c *gin.Context) {
	NotImplemented(c, "WebSocket support not implemented yet")
}

// WebSocketGeneral handles general WebSocket endpoint
func WebSocketGeneral(c *gin.Context) {
	NotImplemented(c, "WebSocket support not implemented yet")
}
