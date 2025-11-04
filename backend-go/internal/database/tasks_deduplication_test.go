package database

import (
	"testing"

	"email-helper-backend/internal/models"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestGetTasksByCategory(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	// Create test tasks with different categories
	task1 := &models.TaskCreate{
		Title:       "FYI Task 1",
		Description: "First FYI task",
		Category:    "fyi",
		Status:      "pending",
		Priority:    "medium",
	}
	task2 := &models.TaskCreate{
		Title:       "Newsletter Task 1",
		Description: "First newsletter task",
		Category:    "newsletter",
		Status:      "pending",
		Priority:    "low",
	}
	task3 := &models.TaskCreate{
		Title:       "FYI Task 2",
		Description: "Second FYI task",
		Category:    "fyi",
		Status:      "completed",
		Priority:    "high",
	}
	task4 := &models.TaskCreate{
		Title:       "Action Task",
		Description: "Action item task",
		Category:    "action_item",
		Status:      "pending",
		Priority:    "urgent",
	}

	created1, err := CreateTask(task1)
	require.NoError(t, err)
	require.NotNil(t, created1)

	created2, err := CreateTask(task2)
	require.NoError(t, err)
	require.NotNil(t, created2)

	created3, err := CreateTask(task3)
	require.NoError(t, err)
	require.NotNil(t, created3)

	created4, err := CreateTask(task4)
	require.NoError(t, err)
	require.NotNil(t, created4)

	t.Run("Get FYI tasks", func(t *testing.T) {
		fyiTasks, err := GetTasksByCategory("fyi")
		require.NoError(t, err)
		assert.Len(t, fyiTasks, 2, "Should have 2 FYI tasks")
		
		// Tasks should be ordered by created_at DESC (most recent first)
		// Since they're created in quick succession, order may vary
		// Just verify both tasks are present with correct category
		titles := make(map[string]bool)
		for _, task := range fyiTasks {
			titles[task.Title] = true
			assert.Equal(t, "fyi", task.Category)
		}
		assert.True(t, titles["FYI Task 1"], "Should have FYI Task 1")
		assert.True(t, titles["FYI Task 2"], "Should have FYI Task 2")
	})

	t.Run("Get newsletter tasks", func(t *testing.T) {
		newsletterTasks, err := GetTasksByCategory("newsletter")
		require.NoError(t, err)
		assert.Len(t, newsletterTasks, 1, "Should have 1 newsletter task")
		assert.Equal(t, "Newsletter Task 1", newsletterTasks[0].Title)
		assert.Equal(t, "newsletter", newsletterTasks[0].Category)
	})

	t.Run("Get action_item tasks", func(t *testing.T) {
		actionTasks, err := GetTasksByCategory("action_item")
		require.NoError(t, err)
		assert.Len(t, actionTasks, 1, "Should have 1 action item task")
		assert.Equal(t, "Action Task", actionTasks[0].Title)
	})

	t.Run("Get non-existent category", func(t *testing.T) {
		emptyTasks, err := GetTasksByCategory("nonexistent")
		require.NoError(t, err)
		assert.Len(t, emptyTasks, 0, "Should have 0 tasks for non-existent category")
	})

	t.Run("Get empty string category", func(t *testing.T) {
		emptyTasks, err := GetTasksByCategory("")
		require.NoError(t, err)
		assert.Len(t, emptyTasks, 0, "Should have 0 tasks for empty category")
	})

	t.Run("Verify task properties", func(t *testing.T) {
		fyiTasks, err := GetTasksByCategory("fyi")
		require.NoError(t, err)
		require.Len(t, fyiTasks, 2)

		// Find the task we want to verify (don't assume order)
		var targetTask *models.Task
		for _, task := range fyiTasks {
			if task.Title == "FYI Task 2" {
				targetTask = task
				break
			}
		}
		require.NotNil(t, targetTask, "FYI Task 2 should exist")

		// Check task properties
		assert.Equal(t, "FYI Task 2", targetTask.Title)
		assert.Equal(t, "Second FYI task", targetTask.Description)
		assert.Equal(t, "completed", targetTask.Status)
		assert.Equal(t, "high", targetTask.Priority)
		assert.Equal(t, "fyi", targetTask.Category)
		assert.Equal(t, 1, targetTask.UserID)
		assert.NotZero(t, targetTask.ID)
		assert.False(t, targetTask.CreatedAt.IsZero())
		assert.False(t, targetTask.UpdatedAt.IsZero())
	})
}

func TestGetTasksByCategoryWithNullableFields(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	// Create task with nullable fields populated
	emailID := "email-123"
	oneLineSummary := "Quick summary"
	task1 := &models.TaskCreate{
		Title:          "Task with optional fields",
		Description:    "Task description",
		Category:       "fyi",
		EmailID:        &emailID,
		OneLineSummary: &oneLineSummary,
	}

	created1, err := CreateTask(task1)
	require.NoError(t, err)
	require.NotNil(t, created1)

	// Create task without nullable fields
	task2 := &models.TaskCreate{
		Title:       "Task without optional fields",
		Description: "Simple task",
		Category:    "fyi",
	}

	created2, err := CreateTask(task2)
	require.NoError(t, err)
	require.NotNil(t, created2)

	// Retrieve tasks
	fyiTasks, err := GetTasksByCategory("fyi")
	require.NoError(t, err)
	assert.Len(t, fyiTasks, 2)

	// Find tasks by title (order might vary)
	var taskWithFields, taskWithoutFields *models.Task
	for _, task := range fyiTasks {
		if task.Title == "Task with optional fields" {
			taskWithFields = task
		} else if task.Title == "Task without optional fields" {
			taskWithoutFields = task
		}
	}

	require.NotNil(t, taskWithFields, "Task with optional fields should exist")
	require.NotNil(t, taskWithoutFields, "Task without optional fields should exist")

	// Verify task with nullable fields
	assert.NotNil(t, taskWithFields.EmailID)
	assert.Equal(t, "email-123", *taskWithFields.EmailID)
	assert.NotNil(t, taskWithFields.OneLineSummary)
	assert.Equal(t, "Quick summary", *taskWithFields.OneLineSummary)

	// Verify task without nullable fields
	assert.Nil(t, taskWithoutFields.EmailID)
	assert.Nil(t, taskWithoutFields.OneLineSummary)
}
