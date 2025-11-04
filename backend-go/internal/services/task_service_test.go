package services

import (
	"os"
	"path/filepath"
	"testing"
	"time"

	"email-helper-backend/internal/database"
	"email-helper-backend/internal/models"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/suite"
)

type TaskServiceTestSuite struct {
	suite.Suite
	service *TaskService
	testDB  string
}

func (suite *TaskServiceTestSuite) SetupSuite() {
	// Reset database for this test suite
	database.ResetForTesting()
	
	// Create temp database for testing
	suite.testDB = filepath.Join(os.TempDir(), "test_tasks.db")
	
	// Remove existing test database
	os.Remove(suite.testDB)
	
	// Initialize database
	err := database.InitDB(suite.testDB)
	suite.Require().NoError(err)
	
	// Tables are already created by InitDB
	suite.service = NewTaskService()
}

func (suite *TaskServiceTestSuite) TearDownSuite() {
	// Close and reset database for next test suite
	database.Close()
	database.ResetForTesting()
	os.Remove(suite.testDB)
}

func (suite *TaskServiceTestSuite) TearDownTest() {
	db, _ := database.GetDB()
	db.Exec("DELETE FROM tasks")
}

func (suite *TaskServiceTestSuite) TestCreateTask() {
	dueDate := time.Now().Add(7 * 24 * time.Hour)
	emailID := "email-123"
	
	taskCreate := &models.TaskCreate{
		Title:       "Test Task",
		Description: "Test Description",
		Status:      "pending",
		Priority:    "high",
		Category:    "work",
		EmailID:     &emailID,
		DueDate:     &dueDate,
	}
	
	task, err := suite.service.CreateTask(taskCreate)
	
	assert.NoError(suite.T(), err)
	assert.NotNil(suite.T(), task)
	assert.Greater(suite.T(), task.ID, 0)
	assert.Equal(suite.T(), taskCreate.Title, task.Title)
	assert.Equal(suite.T(), taskCreate.Status, task.Status)
	assert.Equal(suite.T(), taskCreate.Priority, task.Priority)
	assert.NotNil(suite.T(), task.EmailID)
	assert.Equal(suite.T(), *taskCreate.EmailID, *task.EmailID)
}

func (suite *TaskServiceTestSuite) TestCreateTaskWithDefaults() {
	taskCreate := &models.TaskCreate{
		Title: "Minimal Task",
	}
	
	task, err := suite.service.CreateTask(taskCreate)
	
	assert.NoError(suite.T(), err)
	assert.NotNil(suite.T(), task)
	assert.Equal(suite.T(), "pending", task.Status)
	assert.Equal(suite.T(), "medium", task.Priority)
}

func (suite *TaskServiceTestSuite) TestGetTask() {
	// Create a task first
	taskCreate := &models.TaskCreate{
		Title:    "Find Me",
		Priority: "low",
	}
	created, _ := suite.service.CreateTask(taskCreate)
	
	// Retrieve it
	task, err := suite.service.GetTask(created.ID)
	
	assert.NoError(suite.T(), err)
	assert.NotNil(suite.T(), task)
	assert.Equal(suite.T(), created.ID, task.ID)
	assert.Equal(suite.T(), created.Title, task.Title)
}

func (suite *TaskServiceTestSuite) TestGetTaskNotFound() {
	task, err := suite.service.GetTask(99999)
	
	assert.Error(suite.T(), err)
	assert.Nil(suite.T(), task)
}

func (suite *TaskServiceTestSuite) TestGetTasks() {
	// Create multiple tasks
	for i := 0; i < 5; i++ {
		suite.service.CreateTask(&models.TaskCreate{
			Title:    "Task " + string(rune('A'+i)),
			Priority: "medium",
		})
	}
	
	// Get all tasks
	tasks, total, err := suite.service.GetTasks(1, 10, "", "", "")
	
	assert.NoError(suite.T(), err)
	assert.Equal(suite.T(), 5, total)
	assert.Len(suite.T(), tasks, 5)
}

func (suite *TaskServiceTestSuite) TestGetTasksWithFilter() {
	// Create tasks with different statuses
	suite.service.CreateTask(&models.TaskCreate{
		Title:  "Pending Task",
		Status: "pending",
	})
	suite.service.CreateTask(&models.TaskCreate{
		Title:  "Completed Task",
		Status: "completed",
	})
	
	// Filter by status
	tasks, total, err := suite.service.GetTasks(1, 10, "pending", "", "")
	
	assert.NoError(suite.T(), err)
	assert.Equal(suite.T(), 1, total)
	assert.Len(suite.T(), tasks, 1)
	assert.Equal(suite.T(), "pending", tasks[0].Status)
}

func (suite *TaskServiceTestSuite) TestGetTasksWithSearch() {
	suite.service.CreateTask(&models.TaskCreate{
		Title:       "Important Meeting",
		Description: "Discuss project timeline",
	})
	suite.service.CreateTask(&models.TaskCreate{
		Title:       "Code Review",
		Description: "Review pull request",
	})
	
	// Search for "Meeting"
	tasks, total, err := suite.service.GetTasks(1, 10, "", "", "Meeting")
	
	assert.NoError(suite.T(), err)
	assert.Equal(suite.T(), 1, total)
	assert.Contains(suite.T(), tasks[0].Title, "Meeting")
}

func (suite *TaskServiceTestSuite) TestUpdateTask() {
	// Create a task
	created, _ := suite.service.CreateTask(&models.TaskCreate{
		Title:    "Original Title",
		Status:   "pending",
		Priority: "low",
	})
	
	// Update it
	newTitle := "Updated Title"
	newStatus := "in_progress"
	newPriority := "high"
	
	update := &models.TaskUpdate{
		Title:    &newTitle,
		Status:   &newStatus,
		Priority: &newPriority,
	}
	
	updated, err := suite.service.UpdateTask(created.ID, update)
	
	assert.NoError(suite.T(), err)
	assert.NotNil(suite.T(), updated)
	assert.Equal(suite.T(), newTitle, updated.Title)
	assert.Equal(suite.T(), newStatus, updated.Status)
	assert.Equal(suite.T(), newPriority, updated.Priority)
}

func (suite *TaskServiceTestSuite) TestUpdateTaskToCompleted() {
	// Create a task
	created, _ := suite.service.CreateTask(&models.TaskCreate{
		Title:  "Task to Complete",
		Status: "pending",
	})
	
	// Mark as completed
	newStatus := "completed"
	update := &models.TaskUpdate{
		Status: &newStatus,
	}
	
	updated, err := suite.service.UpdateTask(created.ID, update)
	
	assert.NoError(suite.T(), err)
	assert.Equal(suite.T(), "completed", updated.Status)
	assert.NotNil(suite.T(), updated.CompletedAt)
}

func (suite *TaskServiceTestSuite) TestDeleteTask() {
	// Create a task
	created, _ := suite.service.CreateTask(&models.TaskCreate{
		Title: "Task to Delete",
	})
	
	// Delete it
	err := suite.service.DeleteTask(created.ID)
	assert.NoError(suite.T(), err)
	
	// Verify it's gone
	task, err := suite.service.GetTask(created.ID)
	assert.Error(suite.T(), err)
	assert.Nil(suite.T(), task)
}

func (suite *TaskServiceTestSuite) TestDeleteTaskNotFound() {
	err := suite.service.DeleteTask(99999)
	assert.Error(suite.T(), err)
}

func (suite *TaskServiceTestSuite) TestGetStats() {
	// Create tasks with various statuses and priorities
	suite.service.CreateTask(&models.TaskCreate{
		Title:    "Task 1",
		Status:   "pending",
		Priority: "high",
		Category: "work",
	})
	suite.service.CreateTask(&models.TaskCreate{
		Title:    "Task 2",
		Status:   "completed",
		Priority: "low",
		Category: "work",
	})
	suite.service.CreateTask(&models.TaskCreate{
		Title:    "Task 3",
		Status:   "pending",
		Priority: "medium",
		Category: "personal",
	})
	
	stats, err := suite.service.GetStats()
	
	assert.NoError(suite.T(), err)
	assert.NotNil(suite.T(), stats)
	assert.Equal(suite.T(), 3, stats["total_tasks"])
	assert.NotNil(suite.T(), stats["tasks_by_status"])
	assert.NotNil(suite.T(), stats["tasks_by_priority"])
	assert.NotNil(suite.T(), stats["tasks_by_category"])
}

func (suite *TaskServiceTestSuite) TestBulkUpdate() {
	// Create multiple tasks
	task1, _ := suite.service.CreateTask(&models.TaskCreate{Title: "Task 1", Status: "pending"})
	task2, _ := suite.service.CreateTask(&models.TaskCreate{Title: "Task 2", Status: "pending"})
	task3, _ := suite.service.CreateTask(&models.TaskCreate{Title: "Task 3", Status: "pending"})
	
	// Bulk update status
	newStatus := "in_progress"
	update := &models.TaskUpdate{
		Status: &newStatus,
	}
	
	err := suite.service.BulkUpdate([]int{task1.ID, task2.ID, task3.ID}, update)
	assert.NoError(suite.T(), err)
	
	// Verify all were updated
	updated1, _ := suite.service.GetTask(task1.ID)
	updated2, _ := suite.service.GetTask(task2.ID)
	updated3, _ := suite.service.GetTask(task3.ID)
	
	assert.Equal(suite.T(), "in_progress", updated1.Status)
	assert.Equal(suite.T(), "in_progress", updated2.Status)
	assert.Equal(suite.T(), "in_progress", updated3.Status)
}

func (suite *TaskServiceTestSuite) TestBulkDelete() {
	// Create multiple tasks
	task1, _ := suite.service.CreateTask(&models.TaskCreate{Title: "Task 1"})
	task2, _ := suite.service.CreateTask(&models.TaskCreate{Title: "Task 2"})
	
	// Bulk delete
	err := suite.service.BulkDelete([]int{task1.ID, task2.ID})
	assert.NoError(suite.T(), err)
	
	// Verify all were deleted
	_, err1 := suite.service.GetTask(task1.ID)
	_, err2 := suite.service.GetTask(task2.ID)
	
	assert.Error(suite.T(), err1)
	assert.Error(suite.T(), err2)
}

func (suite *TaskServiceTestSuite) TestGetTasksByEmail() {
	emailID := "email-xyz"
	
	// Create tasks linked to email
	suite.service.CreateTask(&models.TaskCreate{
		Title:   "Email Task 1",
		EmailID: &emailID,
	})
	suite.service.CreateTask(&models.TaskCreate{
		Title:   "Email Task 2",
		EmailID: &emailID,
	})
	
	// Create unrelated task
	otherEmailID := "other-email"
	suite.service.CreateTask(&models.TaskCreate{
		Title:   "Other Task",
		EmailID: &otherEmailID,
	})
	
	// Get tasks for specific email
	tasks, err := suite.service.GetTasksByEmail(emailID)
	
	assert.NoError(suite.T(), err)
	assert.Len(suite.T(), tasks, 2)
	for _, task := range tasks {
		assert.Equal(suite.T(), emailID, *task.EmailID)
	}
}

func TestTaskServiceTestSuite(t *testing.T) {
	suite.Run(t, new(TaskServiceTestSuite))
}
