package handlers

import (
	"net/http"

	"email-helper-backend/internal/models"

	"github.com/gin-gonic/gin"
)

// respondWithError sends a standardized error response
func respondWithError(c *gin.Context, statusCode int, code, message string) {
	errorResp := models.NewErrorResponse(code, message)
	
	// Add request ID if available
	if requestID, exists := c.Get("request_id"); exists {
		if id, ok := requestID.(string); ok {
			errorResp = errorResp.WithRequestID(id)
		}
	}
	
	c.JSON(statusCode, errorResp)
}

// respondWithErrorDetails sends an error response with additional details
func respondWithErrorDetails(c *gin.Context, statusCode int, code, message, details string) {
	errorResp := models.NewErrorResponse(code, message).WithDetails(details)
	
	// Add request ID if available
	if requestID, exists := c.Get("request_id"); exists {
		if id, ok := requestID.(string); ok {
			errorResp = errorResp.WithRequestID(id)
		}
	}
	
	c.JSON(statusCode, errorResp)
}

// Common error responses

func BadRequest(c *gin.Context, message string) {
	respondWithError(c, http.StatusBadRequest, models.ErrorCodeBadRequest, message)
}

func BadRequestWithDetails(c *gin.Context, message, details string) {
	respondWithErrorDetails(c, http.StatusBadRequest, models.ErrorCodeBadRequest, message, details)
}

func NotFound(c *gin.Context, code, message string) {
	respondWithError(c, http.StatusNotFound, code, message)
}

func InternalError(c *gin.Context, message string) {
	respondWithError(c, http.StatusInternalServerError, models.ErrorCodeInternalError, message)
}

func InternalErrorWithDetails(c *gin.Context, message, details string) {
	respondWithErrorDetails(c, http.StatusInternalServerError, models.ErrorCodeInternalError, message, details)
}

func ServiceUnavailable(c *gin.Context, service, message string) {
	respondWithErrorDetails(c, http.StatusServiceUnavailable, models.ErrorCodeServiceUnavailable, message, "Service: "+service)
}

func ValidationError(c *gin.Context, message, details string) {
	respondWithErrorDetails(c, http.StatusBadRequest, models.ErrorCodeValidationFailed, message, details)
}

func DatabaseError(c *gin.Context, message string) {
	respondWithError(c, http.StatusInternalServerError, models.ErrorCodeDatabaseError, message)
}

func OutlookError(c *gin.Context, message string) {
	respondWithError(c, http.StatusInternalServerError, models.ErrorCodeOutlookError, message)
}

func AIServiceError(c *gin.Context, message string) {
	respondWithError(c, http.StatusInternalServerError, models.ErrorCodeAIServiceError, message)
}
