package handlers

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"email-helper-backend/internal/models"
	"email-helper-backend/internal/testutil"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

func TestClassifyEmail(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.POST("/ai/classify", ClassifyEmail)

	expectedResponse := testutil.CreateTestAIClassification()

	mockService.On("ClassifyEmail", 
		mock.AnythingOfType("*context.timerCtx"),
		"Test Subject",
		"sender@example.com",
		"Test email body",
		"user context",
	).Return(expectedResponse, nil)

	classifyReq := models.AIClassificationRequest{
		Subject: "Test Subject",
		Sender:  "sender@example.com",
		Content: "Test email body",
		Context: "user context",
	}
	jsonData, _ := json.Marshal(classifyReq)

	req, _ := http.NewRequest("POST", "/ai/classify", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.AIClassificationResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, expectedResponse.Category, response.Category)
	assert.NotNil(t, response.Confidence)

	mockService.AssertExpectations(t)
}

func TestClassifyEmailBadRequest(t *testing.T) {
	router := setupTestRouter()
	router.POST("/ai/classify", ClassifyEmail)

	req, _ := http.NewRequest("POST", "/ai/classify", bytes.NewBuffer([]byte("invalid json")))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusBadRequest, w.Code)
}

func TestExtractActionItems(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.POST("/ai/action-items", ExtractActionItems)

	expectedResponse := testutil.CreateTestActionItems()

	mockService.On("ExtractActionItems",
		mock.AnythingOfType("*context.timerCtx"),
		"Test email content",
		"user context",
	).Return(expectedResponse, nil)

	actionReq := models.ActionItemRequest{
		EmailContent: "Test email content",
		Context:      "user context",
	}
	jsonData, _ := json.Marshal(actionReq)

	req, _ := http.NewRequest("POST", "/ai/action-items", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.ActionItemResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Len(t, response.ActionItems, 3)
	assert.Equal(t, "high", response.Urgency)

	mockService.AssertExpectations(t)
}

func TestExtractActionItemsBadRequest(t *testing.T) {
	router := setupTestRouter()
	router.POST("/ai/action-items", ExtractActionItems)

	req, _ := http.NewRequest("POST", "/ai/action-items", bytes.NewBuffer([]byte("{invalid")))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusBadRequest, w.Code)
}

func TestSummarizeEmail(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.POST("/ai/summarize", SummarizeEmail)

	expectedResponse := testutil.CreateTestSummary()

	mockService.On("SummarizeEmail",
		mock.AnythingOfType("*context.timerCtx"),
		"Test email content",
		"detailed",
	).Return(expectedResponse, nil)

	summaryReq := models.SummaryRequest{
		EmailContent: "Test email content",
		SummaryType:  "detailed",
	}
	jsonData, _ := json.Marshal(summaryReq)

	req, _ := http.NewRequest("POST", "/ai/summarize", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.SummaryResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.NotEmpty(t, response.Summary)
	assert.Len(t, response.KeyPoints, 3)

	mockService.AssertExpectations(t)
}

func TestSummarizeEmailDefaultType(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.POST("/ai/summarize", SummarizeEmail)

	expectedResponse := testutil.CreateTestSummary()

	mockService.On("SummarizeEmail",
		mock.AnythingOfType("*context.timerCtx"),
		"Test email content",
		"brief",
	).Return(expectedResponse, nil)

	summaryReq := models.SummaryRequest{
		EmailContent: "Test email content",
		// SummaryType not specified, should default to "brief"
	}
	jsonData, _ := json.Marshal(summaryReq)

	req, _ := http.NewRequest("POST", "/ai/summarize", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	mockService.AssertExpectations(t)
}

func TestSummarizeEmailBadRequest(t *testing.T) {
	router := setupTestRouter()
	router.POST("/ai/summarize", SummarizeEmail)

	req, _ := http.NewRequest("POST", "/ai/summarize", bytes.NewBuffer([]byte("not json")))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusBadRequest, w.Code)
}

func TestGetAvailableTemplates(t *testing.T) {
	router := setupTestRouter()
	router.GET("/ai/templates", GetAvailableTemplates)

	req, _ := http.NewRequest("GET", "/ai/templates", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Contains(t, response, "templates")
	assert.Contains(t, response, "descriptions")
}

func TestAIHealthCheck(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.GET("/ai/health", AIHealthCheck)

	mockService.On("CheckAIHealth", mock.AnythingOfType("*context.timerCtx")).Return(nil)

	req, _ := http.NewRequest("GET", "/ai/health", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "healthy", response["status"])

	mockService.AssertExpectations(t)
}

func TestAIHealthCheckUnavailable(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.GET("/ai/health", AIHealthCheck)

	mockService.On("CheckAIHealth", mock.AnythingOfType("*context.timerCtx")).Return(assert.AnError)

	req, _ := http.NewRequest("GET", "/ai/health", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusServiceUnavailable, w.Code)
	mockService.AssertExpectations(t)
}

func TestClassifyBatchStreamRequiresEmailIDs(t *testing.T) {
	router := setupTestRouter()
	router.POST("/ai/classify/batch/stream", ClassifyBatchStream)

	// Test with no body
	req, _ := http.NewRequest("POST", "/ai/classify/batch/stream", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusBadRequest, w.Code)
}
