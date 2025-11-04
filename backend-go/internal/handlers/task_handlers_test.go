package handlers

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"email-helper-backend/internal/models"
	"email-helper-backend/internal/testutil"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// MockTaskService is a mock of TaskService
type MockTaskService struct {
	mock.Mock
}

func (m *MockTaskService) CreateTask(task *models.TaskCreate) (*models.Task, error) {
	args := m.Called(task)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.Task), args.Error(1)
}

func (m *MockTaskService) GetTask(id int) (*models.Task, error) {
	args := m.Called(id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.Task), args.Error(1)
}

func (m *MockTaskService) GetTasks(page, limit int, status, priority, search string) ([]*models.Task, int, error) {
	args := m.Called(page, limit, status, priority, search)
	if args.Get(0) == nil {
		return nil, 0, args.Error(2)
	}
	return args.Get(0).([]*models.Task), args.Int(1), args.Error(2)
}

func (m *MockTaskService) UpdateTask(id int, update *models.TaskUpdate) (*models.Task, error) {
	args := m.Called(id, update)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.Task), args.Error(1)
}

func (m *MockTaskService) DeleteTask(id int) error {
	args := m.Called(id)
	return args.Error(0)
}

func (m *MockTaskService) GetStats() (map[string]interface{}, error) {
	args := m.Called()
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(map[string]interface{}), args.Error(1)
}

func (m *MockTaskService) BulkUpdate(taskIDs []int, update *models.TaskUpdate) error {
	args := m.Called(taskIDs, update)
	return args.Error(0)
}

func (m *MockTaskService) BulkDelete(taskIDs []int) error {
	args := m.Called(taskIDs)
	return args.Error(0)
}

func (m *MockTaskService) GetTasksByEmail(emailID string) ([]*models.Task, error) {
	args := m.Called(emailID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*models.Task), args.Error(1)
}

func setupTestRouter() *gin.Engine {
	gin.SetMode(gin.TestMode)
	router := gin.New()
	return router
}

func TestGetTasks(t *testing.T) {
	mockService := new(MockTaskService)
	originalService := taskService
	taskService = mockService
	defer func() { taskService = originalService }()

	router := setupTestRouter()
	router.GET("/tasks", GetTasks)

	testTasks := testutil.CreateTestTaskList(3)

	mockService.On("GetTasks", 1, 20, "", "", "").Return(testTasks, 3, nil)

	req, _ := http.NewRequest("GET", "/tasks", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.TaskListResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, 3, response.TotalCount)
	assert.Len(t, response.Tasks, 3)

	mockService.AssertExpectations(t)
}

func TestGetTasksWithFilters(t *testing.T) {
	mockService := new(MockTaskService)
	originalService := taskService
	taskService = mockService
	defer func() { taskService = originalService }()

	router := setupTestRouter()
	router.GET("/tasks", GetTasks)

	testTasks := testutil.CreateTestTaskList(1)

	mockService.On("GetTasks", 1, 10, "pending", "high", "").Return(testTasks, 1, nil)

	req, _ := http.NewRequest("GET", "/tasks?limit=10&status=pending&priority=high", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	mockService.AssertExpectations(t)
}

func TestCreateTask(t *testing.T) {
	mockService := new(MockTaskService)
	originalService := taskService
	taskService = mockService
	defer func() { taskService = originalService }()

	router := setupTestRouter()
	router.POST("/tasks", CreateTask)

	taskCreate := models.TaskCreate{
		Title:    "Test Task",
		Priority: "high",
	}

	expectedTask := testutil.CreateTestTask(1)
	expectedTask.Title = taskCreate.Title

	mockService.On("CreateTask", mock.MatchedBy(func(tc *models.TaskCreate) bool {
		return tc.Title == taskCreate.Title
	})).Return(expectedTask, nil)

	jsonData, _ := json.Marshal(taskCreate)
	req, _ := http.NewRequest("POST", "/tasks", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusCreated, w.Code)

	var response models.Task
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, expectedTask.Title, response.Title)

	mockService.AssertExpectations(t)
}

func TestGetTask(t *testing.T) {
	mockService := new(MockTaskService)
	originalService := taskService
	taskService = mockService
	defer func() { taskService = originalService }()

	router := setupTestRouter()
	router.GET("/tasks/:id", GetTask)

	expectedTask := testutil.CreateTestTask(1)

	mockService.On("GetTask", 1).Return(expectedTask, nil)

	req, _ := http.NewRequest("GET", "/tasks/1", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.Task
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, expectedTask.ID, response.ID)

	mockService.AssertExpectations(t)
}

func TestGetTaskNotFound(t *testing.T) {
	mockService := new(MockTaskService)
	originalService := taskService
	taskService = mockService
	defer func() { taskService = originalService }()

	router := setupTestRouter()
	router.GET("/tasks/:id", GetTask)

	mockService.On("GetTask", 999).Return(nil, assert.AnError)

	req, _ := http.NewRequest("GET", "/tasks/999", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusNotFound, w.Code)
	mockService.AssertExpectations(t)
}

func TestUpdateTask(t *testing.T) {
	mockService := new(MockTaskService)
	originalService := taskService
	taskService = mockService
	defer func() { taskService = originalService }()

	router := setupTestRouter()
	router.PUT("/tasks/:id", UpdateTask)

	newTitle := "Updated Task"
	taskUpdate := models.TaskUpdate{
		Title: &newTitle,
	}

	expectedTask := testutil.CreateTestTask(1)
	expectedTask.Title = newTitle

	mockService.On("UpdateTask", 1, mock.MatchedBy(func(tu *models.TaskUpdate) bool {
		return tu.Title != nil && *tu.Title == newTitle
	})).Return(expectedTask, nil)

	jsonData, _ := json.Marshal(taskUpdate)
	req, _ := http.NewRequest("PUT", "/tasks/1", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response models.Task
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, newTitle, response.Title)

	mockService.AssertExpectations(t)
}

func TestDeleteTask(t *testing.T) {
	mockService := new(MockTaskService)
	originalService := taskService
	taskService = mockService
	defer func() { taskService = originalService }()

	router := setupTestRouter()
	router.DELETE("/tasks/:id", DeleteTask)

	mockService.On("DeleteTask", 1).Return(nil)

	req, _ := http.NewRequest("DELETE", "/tasks/1", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.True(t, response["success"].(bool))

	mockService.AssertExpectations(t)
}

func TestGetTaskStats(t *testing.T) {
	mockService := new(MockTaskService)
	originalService := taskService
	taskService = mockService
	defer func() { taskService = originalService }()

	router := setupTestRouter()
	router.GET("/tasks/stats", GetTaskStats)

	expectedStats := map[string]interface{}{
		"total_tasks":   10,
		"pending_tasks": 5,
	}

	mockService.On("GetStats").Return(expectedStats, nil)

	req, _ := http.NewRequest("GET", "/tasks/stats", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, float64(10), response["total_tasks"])

	mockService.AssertExpectations(t)
}

func TestBulkUpdateTasks(t *testing.T) {
	mockService := new(MockTaskService)
	originalService := taskService
	taskService = mockService
	defer func() { taskService = originalService }()

	router := setupTestRouter()
	router.POST("/tasks/bulk/update", BulkUpdateTasks)

	newStatus := "completed"
	bulkUpdate := models.BulkTaskUpdate{
		TaskIDs: []int{1, 2, 3},
		Updates: models.TaskUpdate{
			Status: &newStatus,
		},
	}

	mockService.On("BulkUpdate", bulkUpdate.TaskIDs, mock.AnythingOfType("*models.TaskUpdate")).Return(nil)

	jsonData, _ := json.Marshal(bulkUpdate)
	req, _ := http.NewRequest("POST", "/tasks/bulk/update", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.True(t, response["success"].(bool))

	mockService.AssertExpectations(t)
}

func TestBulkDeleteTasks(t *testing.T) {
	mockService := new(MockTaskService)
	originalService := taskService
	taskService = mockService
	defer func() { taskService = originalService }()

	router := setupTestRouter()
	router.POST("/tasks/bulk/delete", BulkDeleteTasks)

	bulkDelete := models.BulkTaskDelete{
		TaskIDs: []int{1, 2, 3},
	}

	mockService.On("BulkDelete", bulkDelete.TaskIDs).Return(nil)

	jsonData, _ := json.Marshal(bulkDelete)
	req, _ := http.NewRequest("POST", "/tasks/bulk/delete", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.True(t, response["success"].(bool))

	mockService.AssertExpectations(t)
}
