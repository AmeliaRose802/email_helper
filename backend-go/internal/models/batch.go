package models

// BatchOperationResponse is the standardized response for all batch operations
// This provides consistent structure across email and task batch endpoints
type BatchOperationResponse struct {
	// Success indicates if the overall operation completed without critical errors
	Success bool `json:"success"`

	// Processed is the total number of items that were processed
	Processed int `json:"processed"`

	// Successful is the count of items that completed successfully
	Successful int `json:"successful"`

	// Failed is the count of items that failed to process
	Failed int `json:"failed"`

	// Results contains detailed results for each processed item (optional)
	// Can be empty for simple operations that only need counts
	Results []BatchItemResult `json:"results,omitempty"`

	// Errors contains any error messages from the operation (optional)
	Errors []string `json:"errors,omitempty"`

	// Message provides a human-readable summary of the operation (optional)
	Message string `json:"message,omitempty"`
}

// BatchItemResult represents the result of processing a single item in a batch
type BatchItemResult struct {
	// ItemID is the identifier of the item that was processed
	ItemID string `json:"item_id"`

	// Success indicates if this specific item was processed successfully
	Success bool `json:"success"`

	// Error contains error message if processing failed (optional)
	Error string `json:"error,omitempty"`

	// Data contains operation-specific result data (optional)
	// For emails: category, confidence, reasoning, action items, priority
	// For tasks: updated fields, status changes
	Data map[string]interface{} `json:"data,omitempty"`
}
