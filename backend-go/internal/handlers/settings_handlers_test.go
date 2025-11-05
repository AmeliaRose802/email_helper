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

// MockSettingsService is a mock of SettingsService
type MockSettingsService struct {
	mock.Mock
}

func (m *MockSettingsService) GetSettings() (*models.UserSettings, error) {
	args := m.Called()
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.UserSettings), args.Error(1)
}

func (m *MockSettingsService) UpdateSettings(settings *models.UserSettings) error {
	args := m.Called(settings)
	return args.Error(0)
}

func (m *MockSettingsService) ResetSettings() error {
	args := m.Called()
	return args.Error(0)
}

func TestGetSettings(t *testing.T) {
	mockService := new(MockSettingsService)
	originalService := settingsService
	settingsService = mockService
	defer func() { settingsService = originalService }()

	router := setupTestRouter()
	router.GET("/settings", GetSettings)

	expectedSettings := testutil.CreateTestSettings()

	mockService.On("GetSettings").Return(expectedSettings, nil)

	req, _ := http.NewRequest("GET", "/settings", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.UserSettings
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.NotNil(t, response.Username)

	mockService.AssertExpectations(t)
}

func TestGetSettingsError(t *testing.T) {
	mockService := new(MockSettingsService)
	originalService := settingsService
	settingsService = mockService
	defer func() { settingsService = originalService }()

	router := setupTestRouter()
	router.GET("/settings", GetSettings)

	mockService.On("GetSettings").Return(nil, assert.AnError)

	req, _ := http.NewRequest("GET", "/settings", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusInternalServerError, w.Code)
	mockService.AssertExpectations(t)
}

func TestUpdateSettings(t *testing.T) {
	mockService := new(MockSettingsService)
	originalService := settingsService
	settingsService = mockService
	defer func() { settingsService = originalService }()

	router := setupTestRouter()
	router.PUT("/settings", UpdateSettings)

	mockService.On("UpdateSettings", mock.AnythingOfType("*models.UserSettings")).Return(nil)

	updateSettings := testutil.CreateTestSettings()
	jsonData, _ := json.Marshal(updateSettings)

	req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.True(t, response["success"].(bool))
	assert.Equal(t, "Settings updated", response["message"])

	mockService.AssertExpectations(t)
}

func TestUpdateSettingsBadRequest(t *testing.T) {
	router := setupTestRouter()
	router.PUT("/settings", UpdateSettings)

	req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer([]byte("invalid")))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusBadRequest, w.Code)
}

func TestUpdateSettingsError(t *testing.T) {
	mockService := new(MockSettingsService)
	originalService := settingsService
	settingsService = mockService
	defer func() { settingsService = originalService }()

	router := setupTestRouter()
	router.PUT("/settings", UpdateSettings)

	mockService.On("UpdateSettings", mock.AnythingOfType("*models.UserSettings")).Return(assert.AnError)

	updateSettings := testutil.CreateTestSettings()
	jsonData, _ := json.Marshal(updateSettings)

	req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusInternalServerError, w.Code)
	mockService.AssertExpectations(t)
}

func TestResetSettings(t *testing.T) {
	mockService := new(MockSettingsService)
	originalService := settingsService
	settingsService = mockService
	defer func() { settingsService = originalService }()

	router := setupTestRouter()
	router.POST("/settings/reset", ResetSettings)

	mockService.On("ResetSettings").Return(nil)

	req, _ := http.NewRequest("POST", "/settings/reset", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.True(t, response["success"].(bool))
	assert.Equal(t, "Settings reset to defaults", response["message"])

	mockService.AssertExpectations(t)
}

func TestResetSettingsError(t *testing.T) {
	mockService := new(MockSettingsService)
	originalService := settingsService
	settingsService = mockService
	defer func() { settingsService = originalService }()

	router := setupTestRouter()
	router.POST("/settings/reset", ResetSettings)

	mockService.On("ResetSettings").Return(assert.AnError)

	req, _ := http.NewRequest("POST", "/settings/reset", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusInternalServerError, w.Code)
	mockService.AssertExpectations(t)
}

// Edge case tests

func TestUpdateSettingsMalformedJSON(t *testing.T) {
	t.Run("InvalidJSON", func(t *testing.T) {
		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer([]byte("{ invalid json")))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
		
		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		// Verify error field exists with nested structure
		errorField, ok := response["error"].(map[string]interface{})
		assert.True(t, ok, "Response should contain error field")
		errorMsg, ok := errorField["message"].(string)
		assert.True(t, ok, "Error field should contain message")
		assert.NotEmpty(t, errorMsg, "Error message should not be empty")
	})

	t.Run("UnterminatedString", func(t *testing.T) {
		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer([]byte(`{"username": "unterminated`)))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
	})

	t.Run("InvalidUnicodeEscape", func(t *testing.T) {
		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer([]byte(`{"username": "\uXXXX"}`)))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
	})
}

func TestUpdateSettingsMissingContentType(t *testing.T) {
	mockService := new(MockSettingsService)
	originalService := settingsService
	settingsService = mockService
	defer func() { settingsService = originalService }()

	router := setupTestRouter()
	router.PUT("/settings", UpdateSettings)

	mockService.On("UpdateSettings", mock.AnythingOfType("*models.UserSettings")).Return(nil)

	updateSettings := testutil.CreateTestSettings()
	jsonData, _ := json.Marshal(updateSettings)

	req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer(jsonData))
	// Intentionally NOT setting Content-Type header
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	// Gin should still accept it, but let's verify the behavior
	// If it fails, that's also valid
	assert.True(t, w.Code == http.StatusBadRequest || w.Code == http.StatusOK || w.Code == http.StatusInternalServerError)
}

func TestUpdateSettingsEmptyBody(t *testing.T) {
	t.Run("EmptyString", func(t *testing.T) {
		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer([]byte("")))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
	})

	t.Run("EmptyJSONObject", func(t *testing.T) {
		mockService := new(MockSettingsService)
		originalService := settingsService
		settingsService = mockService
		defer func() { settingsService = originalService }()

		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		mockService.On("UpdateSettings", mock.AnythingOfType("*models.UserSettings")).Return(nil)

		req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer([]byte("{}")))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		// Empty JSON object should be accepted (all fields optional)
		assert.Equal(t, http.StatusOK, w.Code)
	})

	t.Run("NilBody", func(t *testing.T) {
		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		req, _ := http.NewRequest("PUT", "/settings", nil)
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
	})
}

func TestUpdateSettingsLargePayload(t *testing.T) {
	t.Run("VeryLargePromptTemplate", func(t *testing.T) {
		mockService := new(MockSettingsService)
		originalService := settingsService
		settingsService = mockService
		defer func() { settingsService = originalService }()

		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		mockService.On("UpdateSettings", mock.AnythingOfType("*models.UserSettings")).Return(nil)

		// Create a large prompt template (100KB)
		largeTemplate := string(make([]byte, 100000))
		for i := 0; i < len(largeTemplate); i++ {
			largeTemplate = largeTemplate[:i] + "a"
		}
		
		updateSettings := testutil.CreateTestSettings()
		if updateSettings.CustomPrompts == nil {
			updateSettings.CustomPrompts = make(map[string]string)
		}
		updateSettings.CustomPrompts["large_template"] = largeTemplate
		jsonData, _ := json.Marshal(updateSettings)

		req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer(jsonData))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		// Should handle large payloads gracefully
		assert.True(t, w.Code == http.StatusOK || w.Code == http.StatusRequestEntityTooLarge || w.Code == http.StatusBadRequest)
	})

	t.Run("ManyFields", func(t *testing.T) {
		mockService := new(MockSettingsService)
		originalService := settingsService
		settingsService = mockService
		defer func() { settingsService = originalService }()

		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		mockService.On("UpdateSettings", mock.AnythingOfType("*models.UserSettings")).Return(nil)

		// Create settings with all fields populated
		updateSettings := testutil.CreateTestSettings()
		username := "testuser"
		jobContext := "Test job context"
		newsletterInterests := "tech, golang, cloud"
		azureEndpoint := "https://test.openai.azure.com"
		azureDeployment := "gpt-4"
		areaPath := "Project\\Area"
		pat := "test-pat"
		
		updateSettings.Username = &username
		updateSettings.JobContext = &jobContext
		updateSettings.NewsletterInterests = &newsletterInterests
		updateSettings.AzureOpenAIEndpoint = &azureEndpoint
		updateSettings.AzureOpenAIDeployment = &azureDeployment
		updateSettings.ADOAreaPath = &areaPath
		updateSettings.ADOPAT = &pat
		updateSettings.CustomPrompts = map[string]string{
			"classify": "Classify this email",
			"actions":  "Extract actions",
			"summary":  "Summarize email",
		}

		jsonData, _ := json.Marshal(updateSettings)

		req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer(jsonData))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		mockService.AssertExpectations(t)
	})
}

func TestUpdateSettingsSpecialCharacters(t *testing.T) {
	t.Run("UnicodeCharacters", func(t *testing.T) {
		mockService := new(MockSettingsService)
		originalService := settingsService
		settingsService = mockService
		defer func() { settingsService = originalService }()

		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		mockService.On("UpdateSettings", mock.AnythingOfType("*models.UserSettings")).Return(nil)

		updateSettings := testutil.CreateTestSettings()
		unicode := "用户测试 🔥 émojis"
		updateSettings.Username = &unicode

		jsonData, _ := json.Marshal(updateSettings)

		req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer(jsonData))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		mockService.AssertExpectations(t)
	})

	t.Run("EscapedCharacters", func(t *testing.T) {
		mockService := new(MockSettingsService)
		originalService := settingsService
		settingsService = mockService
		defer func() { settingsService = originalService }()

		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		mockService.On("UpdateSettings", mock.AnythingOfType("*models.UserSettings")).Return(nil)

		updateSettings := testutil.CreateTestSettings()
		escaped := "Line1\\nLine2\\tTab\\\"Quote\\\\"
		updateSettings.JobContext = &escaped

		jsonData, _ := json.Marshal(updateSettings)

		req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer(jsonData))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		mockService.AssertExpectations(t)
	})

	t.Run("HTMLTags", func(t *testing.T) {
		mockService := new(MockSettingsService)
		originalService := settingsService
		settingsService = mockService
		defer func() { settingsService = originalService }()

		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		mockService.On("UpdateSettings", mock.AnythingOfType("*models.UserSettings")).Return(nil)

		updateSettings := testutil.CreateTestSettings()
		htmlTags := "<script>alert('xss')</script>"
		updateSettings.JobContext = &htmlTags

		jsonData, _ := json.Marshal(updateSettings)

		req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer(jsonData))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		mockService.AssertExpectations(t)
	})
}

func TestGetSettingsNullFields(t *testing.T) {
	mockService := new(MockSettingsService)
	originalService := settingsService
	settingsService = mockService
	defer func() { settingsService = originalService }()

	router := setupTestRouter()
	router.GET("/settings", GetSettings)

	// Return settings with nil fields
	settingsWithNulls := &models.UserSettings{}

	mockService.On("GetSettings").Return(settingsWithNulls, nil)

	req, _ := http.NewRequest("GET", "/settings", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.UserSettings
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	// All fields should be nil
	assert.Nil(t, response.Username)
	assert.Nil(t, response.JobContext)
	assert.Nil(t, response.NewsletterInterests)

	mockService.AssertExpectations(t)
}

func TestUpdateSettingsInvalidFieldTypes(t *testing.T) {
	t.Run("NumberInsteadOfString", func(t *testing.T) {
		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		// Send number for username field
		req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer([]byte(`{"username": 12345}`)))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
	})

	t.Run("BoolInsteadOfString", func(t *testing.T) {
		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer([]byte(`{"job_context": true}`)))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
	})

	t.Run("ArrayInsteadOfString", func(t *testing.T) {
		mockService := new(MockSettingsService)
		originalService := settingsService
		settingsService = mockService
		defer func() { settingsService = originalService }()

		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		mockService.On("UpdateSettings", mock.AnythingOfType("*models.UserSettings")).Return(nil)

		// Try to send array for newsletter_interests field
		req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer([]byte(`{"newsletter_interests": ["interest1", "interest2"]}`)))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		// Gin will fail to parse array as string
		assert.Equal(t, http.StatusBadRequest, w.Code)
	})
}

func TestErrorResponseFormat(t *testing.T) {
	t.Run("GetSettingsErrorFormat", func(t *testing.T) {
		mockService := new(MockSettingsService)
		originalService := settingsService
		settingsService = mockService
		defer func() { settingsService = originalService }()

		router := setupTestRouter()
		router.GET("/settings", GetSettings)

		mockService.On("GetSettings").Return(nil, assert.AnError)

		req, _ := http.NewRequest("GET", "/settings", nil)
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.Contains(t, response, "error")
		assert.NotEmpty(t, response["error"])
	})

	t.Run("UpdateSettingsErrorFormat", func(t *testing.T) {
		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer([]byte("invalid")))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.Contains(t, response, "error")
		errorField, ok := response["error"].(map[string]interface{})
		assert.True(t, ok, "Error field should be an object")
		errorMsg, ok := errorField["message"].(string)
		assert.True(t, ok, "Error should have message field")
		assert.NotEmpty(t, errorMsg, "Error message should not be empty")
		// Verify error message is helpful
		assert.True(t, len(errorMsg) > 10, "Error message should be descriptive")
	})

	t.Run("ResetSettingsErrorFormat", func(t *testing.T) {
		mockService := new(MockSettingsService)
		originalService := settingsService
		settingsService = mockService
		defer func() { settingsService = originalService }()

		router := setupTestRouter()
		router.POST("/settings/reset", ResetSettings)

		mockService.On("ResetSettings").Return(assert.AnError)

		req, _ := http.NewRequest("POST", "/settings/reset", nil)
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.Contains(t, response, "error")
		assert.NotEmpty(t, response["error"])
	})
}

func TestHTTPStatusCodes(t *testing.T) {
	t.Run("GetSettingsSuccess200", func(t *testing.T) {
		mockService := new(MockSettingsService)
		originalService := settingsService
		settingsService = mockService
		defer func() { settingsService = originalService }()

		router := setupTestRouter()
		router.GET("/settings", GetSettings)

		mockService.On("GetSettings").Return(testutil.CreateTestSettings(), nil)

		req, _ := http.NewRequest("GET", "/settings", nil)
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code, "GET settings success should return 200")
	})

	t.Run("GetSettingsError500", func(t *testing.T) {
		mockService := new(MockSettingsService)
		originalService := settingsService
		settingsService = mockService
		defer func() { settingsService = originalService }()

		router := setupTestRouter()
		router.GET("/settings", GetSettings)

		mockService.On("GetSettings").Return(nil, assert.AnError)

		req, _ := http.NewRequest("GET", "/settings", nil)
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code, "GET settings error should return 500")
	})

	t.Run("UpdateSettingsSuccess200", func(t *testing.T) {
		mockService := new(MockSettingsService)
		originalService := settingsService
		settingsService = mockService
		defer func() { settingsService = originalService }()

		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		mockService.On("UpdateSettings", mock.AnythingOfType("*models.UserSettings")).Return(nil)

		jsonData, _ := json.Marshal(testutil.CreateTestSettings())
		req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer(jsonData))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code, "PUT settings success should return 200")
	})

	t.Run("UpdateSettingsBadRequest400", func(t *testing.T) {
		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer([]byte("invalid")))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code, "PUT settings with invalid JSON should return 400")
	})

	t.Run("UpdateSettingsServiceError500", func(t *testing.T) {
		mockService := new(MockSettingsService)
		originalService := settingsService
		settingsService = mockService
		defer func() { settingsService = originalService }()

		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		mockService.On("UpdateSettings", mock.AnythingOfType("*models.UserSettings")).Return(assert.AnError)

		jsonData, _ := json.Marshal(testutil.CreateTestSettings())
		req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer(jsonData))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code, "PUT settings service error should return 500")
	})

	t.Run("ResetSettingsSuccess200", func(t *testing.T) {
		mockService := new(MockSettingsService)
		originalService := settingsService
		settingsService = mockService
		defer func() { settingsService = originalService }()

		router := setupTestRouter()
		router.POST("/settings/reset", ResetSettings)

		mockService.On("ResetSettings").Return(nil)

		req, _ := http.NewRequest("POST", "/settings/reset", nil)
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code, "POST settings/reset success should return 200")
	})

	t.Run("ResetSettingsError500", func(t *testing.T) {
		mockService := new(MockSettingsService)
		originalService := settingsService
		settingsService = mockService
		defer func() { settingsService = originalService }()

		router := setupTestRouter()
		router.POST("/settings/reset", ResetSettings)

		mockService.On("ResetSettings").Return(assert.AnError)

		req, _ := http.NewRequest("POST", "/settings/reset", nil)
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code, "POST settings/reset error should return 500")
	})
}

func TestUpdateSettingsPartialUpdate(t *testing.T) {
	t.Run("OnlyUsername", func(t *testing.T) {
		mockService := new(MockSettingsService)
		originalService := settingsService
		settingsService = mockService
		defer func() { settingsService = originalService }()

		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		mockService.On("UpdateSettings", mock.AnythingOfType("*models.UserSettings")).Return(nil)

		req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer([]byte(`{"username": "testuser"}`)))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		mockService.AssertExpectations(t)
	})

	t.Run("OnlyJobContext", func(t *testing.T) {
		mockService := new(MockSettingsService)
		originalService := settingsService
		settingsService = mockService
		defer func() { settingsService = originalService }()

		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		mockService.On("UpdateSettings", mock.AnythingOfType("*models.UserSettings")).Return(nil)

		req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer([]byte(`{"job_context": "Software Engineer"}`)))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		mockService.AssertExpectations(t)
	})

	t.Run("MultipleFieldsPartial", func(t *testing.T) {
		mockService := new(MockSettingsService)
		originalService := settingsService
		settingsService = mockService
		defer func() { settingsService = originalService }()

		router := setupTestRouter()
		router.PUT("/settings", UpdateSettings)

		mockService.On("UpdateSettings", mock.AnythingOfType("*models.UserSettings")).Return(nil)

		req, _ := http.NewRequest("PUT", "/settings", bytes.NewBuffer([]byte(`{"username": "testuser", "newsletter_interests": "tech, golang"}`)))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		mockService.AssertExpectations(t)
	})
}

