package services

import (
	"email-helper-backend/internal/database"
	"email-helper-backend/internal/models"
)

// TaskService handles task-related operations
type TaskService struct{}

// NewTaskService creates a new task service
func NewTaskService() *TaskService {
	return &TaskService{}
}

// CreateTask creates a new task
func (s *TaskService) CreateTask(task *models.TaskCreate) (*models.Task, error) {
	return database.CreateTask(task)
}

// GetTask retrieves a task by ID
func (s *TaskService) GetTask(id int) (*models.Task, error) {
	return database.GetTaskByID(id)
}

// GetTasks retrieves tasks with pagination and filtering
func (s *TaskService) GetTasks(page, limit int, status, priority, search string) ([]*models.Task, int, error) {
	return database.GetTasks(page, limit, status, priority, search)
}

// UpdateTask updates a task
func (s *TaskService) UpdateTask(id int, update *models.TaskUpdate) (*models.Task, error) {
	return database.UpdateTask(id, update)
}

// DeleteTask deletes a task
func (s *TaskService) DeleteTask(id int) error {
	return database.DeleteTask(id)
}

// GetStats retrieves task statistics
func (s *TaskService) GetStats() (map[string]interface{}, error) {
	return database.GetTaskStats()
}

// BulkUpdate updates multiple tasks
func (s *TaskService) BulkUpdate(taskIDs []int, update *models.TaskUpdate) error {
	return database.BulkUpdateTasks(taskIDs, update)
}

// BulkDelete deletes multiple tasks
func (s *TaskService) BulkDelete(taskIDs []int) error {
	return database.BulkDeleteTasks(taskIDs)
}

// GetTasksByEmail retrieves tasks linked to an email
func (s *TaskService) GetTasksByEmail(emailID string) ([]*models.Task, error) {
	return database.GetTasksByEmailID(emailID)
}
