package models

import (
	"time"
)

// ErrorResponse represents a standardized error response
type ErrorResponse struct {
	Error ErrorDetails `json:"error"`
}

// ErrorDetails contains detailed error information
type ErrorDetails struct {
	Code      string    `json:"code"`                // Machine-readable error code
	Message   string    `json:"message"`             // Human-readable error message
	Details   string    `json:"details,omitempty"`   // Additional error context
	RequestID string    `json:"request_id,omitempty"` // Request ID for tracking
	Timestamp time.Time `json:"timestamp"`           // Error timestamp
}

// Common error codes
const (
	ErrorCodeBadRequest          = "BAD_REQUEST"
	ErrorCodeUnauthorized        = "UNAUTHORIZED"
	ErrorCodeForbidden           = "FORBIDDEN"
	ErrorCodeNotFound            = "NOT_FOUND"
	ErrorCodeConflict            = "CONFLICT"
	ErrorCodeInternalError       = "INTERNAL_ERROR"
	ErrorCodeServiceUnavailable  = "SERVICE_UNAVAILABLE"
	ErrorCodeValidationFailed    = "VALIDATION_FAILED"
	ErrorCodeDatabaseError       = "DATABASE_ERROR"
	ErrorCodeOutlookError        = "OUTLOOK_ERROR"
	ErrorCodeAIServiceError      = "AI_SERVICE_ERROR"
	ErrorCodeEmailNotFound       = "EMAIL_NOT_FOUND"
	ErrorCodeFolderNotFound      = "FOLDER_NOT_FOUND"
	ErrorCodeTaskNotFound        = "TASK_NOT_FOUND"
	ErrorCodeInvalidCategory     = "INVALID_CATEGORY"
	ErrorCodeInvalidStatus       = "INVALID_STATUS"
	ErrorCodeProcessingError     = "PROCESSING_ERROR"
)

// NewErrorResponse creates a new standardized error response
func NewErrorResponse(code, message string) ErrorResponse {
	return ErrorResponse{
		Error: ErrorDetails{
			Code:      code,
			Message:   message,
			Timestamp: time.Now(),
		},
	}
}

// WithDetails adds additional error details
func (e ErrorResponse) WithDetails(details string) ErrorResponse {
	e.Error.Details = details
	return e
}

// WithRequestID adds a request ID for tracking
func (e ErrorResponse) WithRequestID(requestID string) ErrorResponse {
	e.Error.RequestID = requestID
	return e
}
