package handlers

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"email-helper-backend/internal/models"
	"email-helper-backend/internal/testutil"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// MockEmailService is a mock of EmailService
type MockEmailService struct {
	mock.Mock
}

func (m *MockEmailService) GetEmails(folder string, limit, offset int, source, category string) ([]*models.Email, int, error) {
	args := m.Called(folder, limit, offset, source, category)
	if args.Get(0) == nil {
		return nil, 0, args.Error(2)
	}
	return args.Get(0).([]*models.Email), args.Int(1), args.Error(2)
}

func (m *MockEmailService) GetEmailByID(id, source string) (*models.Email, error) {
	args := m.Called(id, source)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.Email), args.Error(1)
}

func (m *MockEmailService) SearchEmails(query string, page, perPage int) ([]*models.Email, int, error) {
	args := m.Called(query, page, perPage)
	if args.Get(0) == nil {
		return nil, 0, args.Error(2)
	}
	return args.Get(0).([]*models.Email), args.Int(1), args.Error(2)
}

func (m *MockEmailService) MarkAsRead(id string, read bool) error {
	args := m.Called(id, read)
	return args.Error(0)
}

func (m *MockEmailService) MoveToFolder(id, folder string) error {
	args := m.Called(id, folder)
	return args.Error(0)
}

func (m *MockEmailService) UpdateClassification(id, category string, applyToOutlook bool) error {
	args := m.Called(id, category, applyToOutlook)
	return args.Error(0)
}

func (m *MockEmailService) BulkApplyToOutlook(emailIDs []string) (int, int, []string, error) {
	args := m.Called(emailIDs)
	return args.Int(0), args.Int(1), args.Get(2).([]string), args.Error(3)
}

func (m *MockEmailService) SyncToDatabase(emails []*models.Email) error {
	args := m.Called(emails)
	return args.Error(0)
}

func (m *MockEmailService) GetFolders() ([]models.EmailFolder, error) {
	args := m.Called()
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]models.EmailFolder), args.Error(1)
}

func (m *MockEmailService) GetConversation(conversationID, source string) ([]*models.Email, error) {
	args := m.Called(conversationID, source)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*models.Email), args.Error(1)
}

func (m *MockEmailService) GetStats(limit int) (map[string]interface{}, error) {
	args := m.Called(limit)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(map[string]interface{}), args.Error(1)
}

func (m *MockEmailService) GetAccuracyStats() (map[string]interface{}, error) {
	args := m.Called()
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(map[string]interface{}), args.Error(1)
}

func (m *MockEmailService) GetCategoryMappings() []models.CategoryFolderMapping {
	args := m.Called()
	return args.Get(0).([]models.CategoryFolderMapping)
}

func (m *MockEmailService) ClassifyEmail(ctx context.Context, subject, sender, content, userContext string) (*models.AIClassificationResponse, error) {
	args := m.Called(ctx, subject, sender, content, userContext)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.AIClassificationResponse), args.Error(1)
}

func (m *MockEmailService) ExtractActionItems(ctx context.Context, emailContent, userContext string) (*models.ActionItemResponse, error) {
	args := m.Called(ctx, emailContent, userContext)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.ActionItemResponse), args.Error(1)
}

func (m *MockEmailService) SummarizeEmail(ctx context.Context, emailContent, summaryType string) (*models.SummaryResponse, error) {
	args := m.Called(ctx, emailContent, summaryType)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.SummaryResponse), args.Error(1)
}

func (m *MockEmailService) CheckAIHealth(ctx context.Context) error {
	args := m.Called(ctx)
	return args.Error(0)
}

func (m *MockEmailService) AnalyzeHolistically(ctx context.Context, emailIDs []string) (*models.HolisticAnalysisResponse, error) {
	args := m.Called(ctx, emailIDs)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.HolisticAnalysisResponse), args.Error(1)
}

func (m *MockEmailService) Close() error {
	args := m.Called()
	return args.Error(0)
}

// Test GetEmails
func TestGetEmails(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.GET("/emails", GetEmails)

	testEmails := []*models.Email{
		testutil.CreateTestEmail("email-1"),
		testutil.CreateTestEmail("email-2"),
	}

	mockService.On("GetEmails", "Inbox", 50, 0, "outlook", "").Return(testEmails, 2, nil)

	req, _ := http.NewRequest("GET", "/emails", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.EmailListResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, 2, response.Total)
	assert.Len(t, response.Emails, 2)
	assert.False(t, response.HasMore)

	mockService.AssertExpectations(t)
}

func TestGetEmailsWithFilters(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.GET("/emails", GetEmails)

	testEmails := []*models.Email{testutil.CreateTestEmail("email-1")}

	mockService.On("GetEmails", "Sent", 10, 20, "outlook", "fyi").Return(testEmails, 50, nil)

	req, _ := http.NewRequest("GET", "/emails?folder=Sent&limit=10&offset=20&category=fyi", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.EmailListResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, 50, response.Total)
	assert.True(t, response.HasMore) // offset 20 + limit 10 = 30 < 50

	mockService.AssertExpectations(t)
}

func TestGetEmail(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.GET("/emails/:id", GetEmail)

	expectedEmail := testutil.CreateTestEmail("test-123")

	mockService.On("GetEmailByID", "test-123", "outlook").Return(expectedEmail, nil)

	req, _ := http.NewRequest("GET", "/emails/test-123", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.Email
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "test-123", response.ID)

	mockService.AssertExpectations(t)
}

func TestGetEmailNotFound(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.GET("/emails/:id", GetEmail)

	mockService.On("GetEmailByID", "nonexistent", "outlook").Return(nil, assert.AnError)

	req, _ := http.NewRequest("GET", "/emails/nonexistent", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusNotFound, w.Code)
	mockService.AssertExpectations(t)
}

func TestSearchEmails(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.GET("/emails/search", SearchEmails)

	testEmails := []*models.Email{testutil.CreateTestEmail("search-1")}

	mockService.On("SearchEmails", "urgent", 1, 20).Return(testEmails, 1, nil)

	req, _ := http.NewRequest("GET", "/emails/search?q=urgent", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.EmailListResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, 1, response.Total)

	mockService.AssertExpectations(t)
}

func TestGetEmailStats(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.GET("/emails/stats", GetEmailStats)

	expectedStats := map[string]interface{}{
		"total_emails": 100,
		"unread":       20,
	}

	mockService.On("GetStats", 100).Return(expectedStats, nil)

	req, _ := http.NewRequest("GET", "/emails/stats", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, float64(100), response["total_emails"])

	mockService.AssertExpectations(t)
}

func TestGetCategoryMappings(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.GET("/emails/categories/mappings", GetCategoryMappings)

	expectedMappings := []models.CategoryFolderMapping{
		{Category: "fyi", FolderName: "Inbox", StaysInInbox: true},
		{Category: "spam_to_delete", FolderName: "Junk", StaysInInbox: false},
	}

	mockService.On("GetCategoryMappings").Return(expectedMappings)

	req, _ := http.NewRequest("GET", "/emails/categories/mappings", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response []models.CategoryFolderMapping
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Len(t, response, 2)
	assert.Equal(t, "fyi", response[0].Category)

	mockService.AssertExpectations(t)
}

func TestGetAccuracyStats(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.GET("/emails/accuracy", GetAccuracyStats)

	expectedStats := map[string]interface{}{
		"accuracy": 0.95,
		"samples":  100,
	}

	mockService.On("GetAccuracyStats").Return(expectedStats, nil)

	req, _ := http.NewRequest("GET", "/emails/accuracy", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, 0.95, response["accuracy"])

	mockService.AssertExpectations(t)
}

func TestPrefetchEmails(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.POST("/emails/prefetch", PrefetchEmails)

	email1 := testutil.CreateTestEmail("email-1")
	email2 := testutil.CreateTestEmail("email-2")

	mockService.On("GetEmailByID", "email-1", "outlook").Return(email1, nil)
	mockService.On("GetEmailByID", "email-2", "outlook").Return(email2, nil)

	emailIDs := []string{"email-1", "email-2"}
	jsonData, _ := json.Marshal(emailIDs)

	req, _ := http.NewRequest("POST", "/emails/prefetch", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, float64(2), response["success_count"])
	assert.Equal(t, float64(0), response["error_count"])

	mockService.AssertExpectations(t)
}

func TestUpdateEmailReadStatus(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.PUT("/emails/:id/read", UpdateEmailReadStatus)

	mockService.On("MarkAsRead", "email-1", true).Return(nil)

	req, _ := http.NewRequest("PUT", "/emails/email-1/read?read=true", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.EmailOperationResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.True(t, response.Success)
	assert.Equal(t, "email-1", response.EmailID)

	mockService.AssertExpectations(t)
}

func TestMarkEmailAsRead(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.POST("/emails/:id/read", MarkEmailAsRead)

	mockService.On("MarkAsRead", "email-1", true).Return(nil)

	req, _ := http.NewRequest("POST", "/emails/email-1/read", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.EmailOperationResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.True(t, response.Success)

	mockService.AssertExpectations(t)
}

func TestMoveEmail(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.POST("/emails/:id/move", MoveEmail)

	mockService.On("MoveToFolder", "email-1", "Archive").Return(nil)

	req, _ := http.NewRequest("POST", "/emails/email-1/move?destination_folder=Archive", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.EmailOperationResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.True(t, response.Success)

	mockService.AssertExpectations(t)
}

func TestMoveEmailMissingDestination(t *testing.T) {
	router := setupTestRouter()
	router.POST("/emails/:id/move", MoveEmail)

	req, _ := http.NewRequest("POST", "/emails/email-1/move", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusBadRequest, w.Code)
}

func TestUpdateEmailClassification(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.PUT("/emails/:id/classification", UpdateEmailClassification)

	mockService.On("UpdateClassification", "email-1", "fyi", true).Return(nil)

	classificationUpdate := models.UpdateClassificationRequest{
		Category:       "fyi",
		ApplyToOutlook: true,
	}
	jsonData, _ := json.Marshal(classificationUpdate)

	req, _ := http.NewRequest("PUT", "/emails/email-1/classification", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.EmailOperationResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.True(t, response.Success)

	mockService.AssertExpectations(t)
}

func TestBulkApplyToOutlook(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.POST("/emails/bulk/apply", BulkApplyToOutlook)

	emailIDs := []string{"email-1", "email-2", "email-3"}
	mockService.On("BulkApplyToOutlook", emailIDs).Return(3, 0, []string{}, nil)

	bulkApplyReq := models.BulkApplyRequest{EmailIDs: emailIDs}
	jsonData, _ := json.Marshal(bulkApplyReq)

	req, _ := http.NewRequest("POST", "/emails/bulk/apply", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.BulkApplyResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.True(t, response.Success)
	assert.Equal(t, 3, response.Successful)
	assert.Equal(t, 0, response.Failed)

	mockService.AssertExpectations(t)
}

func TestSyncToDatabase(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.POST("/emails/sync", SyncToDatabase)

	mockService.On("SyncToDatabase", mock.AnythingOfType("[]*models.Email")).Return(nil)

	syncReq := models.SyncEmailRequest{
		Emails: []models.Email{
			*testutil.CreateTestEmail("email-1"),
			*testutil.CreateTestEmail("email-2"),
		},
	}
	jsonData, _ := json.Marshal(syncReq)

	req, _ := http.NewRequest("POST", "/emails/sync", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.True(t, response["success"].(bool))
	assert.Equal(t, float64(2), response["count"])

	mockService.AssertExpectations(t)
}

func TestGetFolders(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.GET("/emails/folders", GetFolders)

	expectedFolders := []models.EmailFolder{
		{Name: "Inbox", TotalCount: 10, UnreadCount: 2},
		{Name: "Sent", TotalCount: 5, UnreadCount: 0},
	}

	mockService.On("GetFolders").Return(expectedFolders, nil)

	req, _ := http.NewRequest("GET", "/emails/folders", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.EmailFolderResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, 2, response.Total)
	assert.Len(t, response.Folders, 2)

	mockService.AssertExpectations(t)
}

func TestGetConversationThread(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.GET("/emails/:id/conversation", GetConversationThread)

	testEmails := []*models.Email{
		testutil.CreateTestEmail("email-1"),
		testutil.CreateTestEmail("email-2"),
	}

	mockService.On("GetConversation", "conv-123", "outlook").Return(testEmails, nil)

	req, _ := http.NewRequest("GET", "/emails/conv-123/conversation", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.ConversationResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "conv-123", response.ConversationID)
	assert.Equal(t, 2, response.Total)
	assert.Len(t, response.Emails, 2)

	mockService.AssertExpectations(t)
}

func TestBatchProcessEmailsRequiresBody(t *testing.T) {
	router := setupTestRouter()
	router.POST("/emails/batch/process", BatchProcessEmails)

	req, _ := http.NewRequest("POST", "/emails/batch/process", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	// Now returns 400 Bad Request since endpoint is implemented and requires a body
	assert.Equal(t, http.StatusBadRequest, w.Code)
}

func TestExtractTasksRequiresBody(t *testing.T) {
	router := setupTestRouter()
	router.POST("/emails/extract-tasks", ExtractTasks)

	req, _ := http.NewRequest("POST", "/emails/extract-tasks", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	// Now returns 400 Bad Request since endpoint is implemented and requires a body
	assert.Equal(t, http.StatusBadRequest, w.Code)
}

func TestAnalyzeHolistically(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.POST("/emails/analyze", AnalyzeHolistically)

	// Setup mock expectation
	expectedResponse := &models.HolisticAnalysisResponse{
		TrulyRelevantActions: []models.TrulyRelevantAction{
			{
				ActionType:       "required_personal_action",
				Priority:         "high",
				Topic:            "Project Deadline",
				CanonicalEmailID: "email-1",
				RelatedEmailIDs:  []string{},
				Deadline:         "2025-11-10",
				WhyRelevant:      "Requires immediate attention",
				BlockingOthers:   false,
			},
		},
		SupersededActions: []models.SupersededAction{},
		DuplicateGroups:   []models.DuplicateGroup{},
		ExpiredItems:      []models.ExpiredItem{},
		EmailsAnalyzed:    2,
		ProcessingTime:    0.5,
	}

	mockService.On("AnalyzeHolistically", mock.Anything, []string{"email-1", "email-2"}).
		Return(expectedResponse, nil)

	// Create request
	reqBody := models.HolisticAnalysisRequest{
		EmailIDs: []string{"email-1", "email-2"},
	}
	jsonBytes, _ := json.Marshal(reqBody)
	req, _ := http.NewRequest("POST", "/emails/analyze", bytes.NewBuffer(jsonBytes))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.HolisticAnalysisResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, 2, response.EmailsAnalyzed)
	assert.Equal(t, 1, len(response.TrulyRelevantActions))
}

func TestAnalyzeHolisticallyBadRequest(t *testing.T) {
	router := setupTestRouter()
	router.POST("/emails/analyze", AnalyzeHolistically)

	// Test with no email IDs
	reqBody := models.HolisticAnalysisRequest{
		EmailIDs: []string{},
	}
	jsonBytes, _ := json.Marshal(reqBody)
	req, _ := http.NewRequest("POST", "/emails/analyze", bytes.NewBuffer(jsonBytes))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusBadRequest, w.Code)
}

// Test intelligent data source selection
func TestGetEmailsSelectsOutlookByDefault(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.GET("/emails", GetEmails)

	testEmails := []*models.Email{
		testutil.CreateTestEmail("email-1"),
		testutil.CreateTestEmail("email-2"),
	}

	// Should use outlook source when no category specified
	mockService.On("GetEmails", "Inbox", 50, 0, "outlook", "").Return(testEmails, 2, nil)

	req, _ := http.NewRequest("GET", "/emails", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.EmailListResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, 2, response.Total)
	assert.Len(t, response.Emails, 2)

	mockService.AssertExpectations(t)
}

func TestGetEmailsSelectsDatabaseWhenCategorySpecified(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.GET("/emails", GetEmails)

	testEmails := []*models.Email{testutil.CreateTestEmail("email-1")}

	// Should use database source when category is specified
	mockService.On("GetEmails", "Inbox", 50, 0, "database", "fyi").Return(testEmails, 1, nil)

	req, _ := http.NewRequest("GET", "/emails?category=fyi", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.EmailListResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, 1, response.Total)

	mockService.AssertExpectations(t)
}

func TestGetEmailsWithFolderUsesOutlook(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.GET("/emails", GetEmails)

	testEmails := []*models.Email{testutil.CreateTestEmail("email-1")}

	// Should use outlook source for folder browsing
	mockService.On("GetEmails", "Sent", 10, 20, "outlook", "").Return(testEmails, 50, nil)

	req, _ := http.NewRequest("GET", "/emails?folder=Sent&limit=10&offset=20", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.EmailListResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, 50, response.Total)
	assert.True(t, response.HasMore)

	mockService.AssertExpectations(t)
}

func TestApplyClassifications(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.POST("/emails/classifications/apply", ApplyClassifications)

	emailIDs := []string{"email-1", "email-2", "email-3"}
	mockService.On("BulkApplyToOutlook", emailIDs).Return(3, 0, []string{}, nil)

	bulkApplyReq := models.BulkApplyRequest{EmailIDs: emailIDs}
	jsonData, _ := json.Marshal(bulkApplyReq)

	req, _ := http.NewRequest("POST", "/emails/classifications/apply", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.BatchOperationResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.True(t, response.Success)
	assert.Equal(t, 3, response.Successful)
	assert.Equal(t, 0, response.Failed)

	mockService.AssertExpectations(t)
}

func TestBulkApplyToOutlook_Deprecated(t *testing.T) {
	mockService := new(MockEmailService)
	originalService := emailService
	emailService = mockService
	defer func() { emailService = originalService }()

	router := setupTestRouter()
	router.POST("/emails/bulk/apply", BulkApplyToOutlook)

	emailIDs := []string{"email-1", "email-2"}
	mockService.On("BulkApplyToOutlook", emailIDs).Return(2, 0, []string{}, nil)

	bulkApplyReq := models.BulkApplyRequest{EmailIDs: emailIDs}
	jsonData, _ := json.Marshal(bulkApplyReq)

	req, _ := http.NewRequest("POST", "/emails/bulk/apply", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	// Check deprecation headers
	assert.Equal(t, "true", w.Header().Get("X-Deprecated"))
	assert.Equal(t, "Use POST /api/emails/classifications/apply instead", w.Header().Get("X-Deprecated-Message"))

	var response models.BatchOperationResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.True(t, response.Success)

	mockService.AssertExpectations(t)
}


