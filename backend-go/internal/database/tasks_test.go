package database

import (
	"sync"
	"testing"
	"time"

	"email-helper-backend/internal/models"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// createTestTask creates a sample task for testing
func createTestTask(title string) *models.TaskCreate {
	emailID := "test-email-123"
	summary := "Test summary for " + title
	dueDate := time.Now().Add(24 * time.Hour)
	
	return &models.TaskCreate{
		Title:          title,
		Description:    "Description for " + title,
		Status:         "pending",
		Priority:       "medium",
		Category:       "work",
		EmailID:        &emailID,
		OneLineSummary: &summary,
		DueDate:        &dueDate,
	}
}

func TestCreateTask(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	t.Run("CreateBasicTask", func(t *testing.T) {
		taskCreate := createTestTask("Basic Task")
		task, err := CreateTask(taskCreate)
		
		require.NoError(t, err)
		assert.NotNil(t, task)
		assert.Greater(t, task.ID, 0)
		assert.Equal(t, "Basic Task", task.Title)
		assert.Equal(t, "Description for Basic Task", task.Description)
		assert.Equal(t, "pending", task.Status)
		assert.Equal(t, "medium", task.Priority)
		assert.Equal(t, "work", task.Category)
		assert.NotNil(t, task.EmailID)
		assert.Equal(t, "test-email-123", *task.EmailID)
		assert.NotNil(t, task.OneLineSummary)
		assert.NotNil(t, task.DueDate)
		assert.NotZero(t, task.CreatedAt)
		assert.NotZero(t, task.UpdatedAt)
		assert.Nil(t, task.CompletedAt)
	})

	t.Run("CreateTaskWithDefaultStatus", func(t *testing.T) {
		taskCreate := createTestTask("Task with default status")
		taskCreate.Status = "" // Empty status should default to "pending"
		
		task, err := CreateTask(taskCreate)
		require.NoError(t, err)
		assert.Equal(t, "pending", task.Status)
	})

	t.Run("CreateTaskWithDefaultPriority", func(t *testing.T) {
		taskCreate := createTestTask("Task with default priority")
		taskCreate.Priority = "" // Empty priority should default to "medium"
		
		task, err := CreateTask(taskCreate)
		require.NoError(t, err)
		assert.Equal(t, "medium", task.Priority)
	})

	t.Run("CreateTaskWithMinimalFields", func(t *testing.T) {
		taskCreate := &models.TaskCreate{
			Title: "Minimal Task",
		}
		
		task, err := CreateTask(taskCreate)
		require.NoError(t, err)
		assert.NotNil(t, task)
		assert.Equal(t, "Minimal Task", task.Title)
		assert.Equal(t, "pending", task.Status)
		assert.Equal(t, "medium", task.Priority)
		assert.Nil(t, task.EmailID)
		assert.Nil(t, task.OneLineSummary)
		assert.Nil(t, task.DueDate)
	})

	t.Run("CreateTaskWithNullEmailID", func(t *testing.T) {
		taskCreate := createTestTask("Task without email")
		taskCreate.EmailID = nil
		
		task, err := CreateTask(taskCreate)
		require.NoError(t, err)
		assert.Nil(t, task.EmailID)
	})

	t.Run("CreateTaskWithNullDueDate", func(t *testing.T) {
		taskCreate := createTestTask("Task without due date")
		taskCreate.DueDate = nil
		
		task, err := CreateTask(taskCreate)
		require.NoError(t, err)
		assert.Nil(t, task.DueDate)
	})

	t.Run("CreateMultipleTasks", func(t *testing.T) {
		for i := 0; i < 5; i++ {
			taskCreate := createTestTask("Task " + string(rune('A'+i)))
			task, err := CreateTask(taskCreate)
			require.NoError(t, err)
			assert.Greater(t, task.ID, 0)
		}
	})

	t.Run("CreateTaskAutoGeneratesIDs", func(t *testing.T) {
		task1, err := CreateTask(createTestTask("Task 1"))
		require.NoError(t, err)
		
		task2, err := CreateTask(createTestTask("Task 2"))
		require.NoError(t, err)
		
		assert.Greater(t, task2.ID, task1.ID)
	})

	t.Run("CreateTaskWithDifferentStatuses", func(t *testing.T) {
		statuses := []string{"pending", "in_progress", "completed", "cancelled"}
		for _, status := range statuses {
			taskCreate := createTestTask("Task with " + status + " status")
			taskCreate.Status = status
			
			task, err := CreateTask(taskCreate)
			require.NoError(t, err)
			assert.Equal(t, status, task.Status)
		}
	})

	t.Run("CreateTaskWithDifferentPriorities", func(t *testing.T) {
		priorities := []string{"low", "medium", "high", "urgent"}
		for _, priority := range priorities {
			taskCreate := createTestTask("Task with " + priority + " priority")
			taskCreate.Priority = priority
			
			task, err := CreateTask(taskCreate)
			require.NoError(t, err)
			assert.Equal(t, priority, task.Priority)
		}
	})
}

func TestGetTaskByID(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	t.Run("GetExistingTask", func(t *testing.T) {
		created, err := CreateTask(createTestTask("Test Task"))
		require.NoError(t, err)
		
		retrieved, err := GetTaskByID(created.ID)
		require.NoError(t, err)
		assert.NotNil(t, retrieved)
		assert.Equal(t, created.ID, retrieved.ID)
		assert.Equal(t, created.Title, retrieved.Title)
		assert.Equal(t, created.Description, retrieved.Description)
		assert.Equal(t, created.Status, retrieved.Status)
	})

	t.Run("GetNonExistentTask", func(t *testing.T) {
		retrieved, err := GetTaskByID(999999)
		assert.Error(t, err)
		assert.Nil(t, retrieved)
		assert.Contains(t, err.Error(), "task not found")
	})

	t.Run("GetTaskWithNullFields", func(t *testing.T) {
		taskCreate := &models.TaskCreate{
			Title: "Task with nulls",
		}
		created, err := CreateTask(taskCreate)
		require.NoError(t, err)
		
		retrieved, err := GetTaskByID(created.ID)
		require.NoError(t, err)
		assert.Nil(t, retrieved.EmailID)
		assert.Nil(t, retrieved.OneLineSummary)
		assert.Nil(t, retrieved.DueDate)
		assert.Nil(t, retrieved.CompletedAt)
	})
}

func TestGetTasks(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	// Create test tasks with different properties
	tasks := []*models.TaskCreate{
		createTestTask("Task 1"),
		createTestTask("Task 2"),
		createTestTask("Task 3"),
	}
	tasks[0].Status = "pending"
	tasks[0].Priority = "high"
	tasks[1].Status = "completed"
	tasks[1].Priority = "low"
	tasks[2].Status = "pending"
	tasks[2].Priority = "medium"

	for _, tc := range tasks {
		_, err := CreateTask(tc)
		require.NoError(t, err)
	}

	t.Run("GetAllTasks", func(t *testing.T) {
		retrieved, total, err := GetTasks(1, 10, "", "", "")
		require.NoError(t, err)
		assert.Equal(t, 3, total)
		assert.Len(t, retrieved, 3)
	})

	t.Run("GetTasksWithPagination", func(t *testing.T) {
		// Page 1 with limit 2
		retrieved, total, err := GetTasks(1, 2, "", "", "")
		require.NoError(t, err)
		assert.Equal(t, 3, total)
		assert.Len(t, retrieved, 2)

		// Page 2 with limit 2
		retrieved, total, err = GetTasks(2, 2, "", "", "")
		require.NoError(t, err)
		assert.Equal(t, 3, total)
		assert.Len(t, retrieved, 1)
	})

	t.Run("GetTasksFilterByStatus", func(t *testing.T) {
		retrieved, total, err := GetTasks(1, 10, "pending", "", "")
		require.NoError(t, err)
		assert.Equal(t, 2, total)
		assert.Len(t, retrieved, 2)
		for _, task := range retrieved {
			assert.Equal(t, "pending", task.Status)
		}
	})

	t.Run("GetTasksFilterByPriority", func(t *testing.T) {
		retrieved, total, err := GetTasks(1, 10, "", "high", "")
		require.NoError(t, err)
		assert.Equal(t, 1, total)
		assert.Len(t, retrieved, 1)
		assert.Equal(t, "high", retrieved[0].Priority)
	})

	t.Run("GetTasksFilterByStatusAndPriority", func(t *testing.T) {
		retrieved, total, err := GetTasks(1, 10, "pending", "medium", "")
		require.NoError(t, err)
		assert.Equal(t, 1, total)
		assert.Len(t, retrieved, 1)
		assert.Equal(t, "pending", retrieved[0].Status)
		assert.Equal(t, "medium", retrieved[0].Priority)
	})

	t.Run("GetTasksWithSearch", func(t *testing.T) {
		retrieved, total, err := GetTasks(1, 10, "", "", "Task 1")
		require.NoError(t, err)
		assert.Equal(t, 1, total)
		assert.Len(t, retrieved, 1)
		assert.Contains(t, retrieved[0].Title, "Task 1")
	})

	t.Run("GetTasksSearchInDescription", func(t *testing.T) {
		retrieved, total, err := GetTasks(1, 10, "", "", "Description for Task 2")
		require.NoError(t, err)
		assert.Equal(t, 1, total)
		assert.Len(t, retrieved, 1)
		assert.Contains(t, retrieved[0].Description, "Description for Task 2")
	})

	t.Run("GetTasksSearchPartialMatch", func(t *testing.T) {
		retrieved, total, err := GetTasks(1, 10, "", "", "Task")
		require.NoError(t, err)
		assert.Equal(t, 3, total)
		assert.Len(t, retrieved, 3)
	})

	t.Run("GetTasksWithEmptySearch", func(t *testing.T) {
		retrieved, total, err := GetTasks(1, 10, "", "", "")
		require.NoError(t, err)
		assert.Equal(t, 3, total)
		assert.Len(t, retrieved, 3)
	})

	t.Run("GetTasksNoResults", func(t *testing.T) {
		retrieved, total, err := GetTasks(1, 10, "nonexistent", "", "")
		require.NoError(t, err)
		assert.Equal(t, 0, total)
		assert.Len(t, retrieved, 0)
	})

	t.Run("GetTasksOrderedByDate", func(t *testing.T) {
		// Create tasks with slight time delay to ensure ordering
		time.Sleep(10 * time.Millisecond)
		newTask, err := CreateTask(createTestTask("Newest Task"))
		require.NoError(t, err)

		retrieved, _, err := GetTasks(1, 10, "", "", "")
		require.NoError(t, err)
		// First task should be newest (DESC order)
		assert.Equal(t, newTask.ID, retrieved[0].ID)
	})

	t.Run("GetTasksWithLargeOffset", func(t *testing.T) {
		retrieved, total, err := GetTasks(100, 10, "", "", "")
		require.NoError(t, err)
		assert.GreaterOrEqual(t, total, 3)
		assert.Len(t, retrieved, 0) // Beyond available results
	})
}

func TestUpdateTask(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	t.Run("UpdateTaskTitle", func(t *testing.T) {
		created, err := CreateTask(createTestTask("Original Title"))
		require.NoError(t, err)

		newTitle := "Updated Title"
		update := &models.TaskUpdate{Title: &newTitle}
		updated, err := UpdateTask(created.ID, update)
		
		require.NoError(t, err)
		assert.Equal(t, "Updated Title", updated.Title)
		assert.Equal(t, created.Description, updated.Description) // Other fields unchanged
	})

	t.Run("UpdateTaskDescription", func(t *testing.T) {
		created, err := CreateTask(createTestTask("Test Task"))
		require.NoError(t, err)

		newDesc := "Updated Description"
		update := &models.TaskUpdate{Description: &newDesc}
		updated, err := UpdateTask(created.ID, update)
		
		require.NoError(t, err)
		assert.Equal(t, "Updated Description", updated.Description)
	})

	t.Run("UpdateTaskStatus", func(t *testing.T) {
		created, err := CreateTask(createTestTask("Test Task"))
		require.NoError(t, err)

		newStatus := "in_progress"
		update := &models.TaskUpdate{Status: &newStatus}
		updated, err := UpdateTask(created.ID, update)
		
		require.NoError(t, err)
		assert.Equal(t, "in_progress", updated.Status)
	})

	t.Run("UpdateTaskStatusToCompleted", func(t *testing.T) {
		created, err := CreateTask(createTestTask("Test Task"))
		require.NoError(t, err)
		assert.Nil(t, created.CompletedAt)

		newStatus := "completed"
		update := &models.TaskUpdate{Status: &newStatus}
		updated, err := UpdateTask(created.ID, update)
		
		require.NoError(t, err)
		assert.Equal(t, "completed", updated.Status)
		assert.NotNil(t, updated.CompletedAt) // CompletedAt should be set
		assert.False(t, updated.CompletedAt.IsZero())
	})

	t.Run("UpdateTaskPriority", func(t *testing.T) {
		created, err := CreateTask(createTestTask("Test Task"))
		require.NoError(t, err)

		newPriority := "urgent"
		update := &models.TaskUpdate{Priority: &newPriority}
		updated, err := UpdateTask(created.ID, update)
		
		require.NoError(t, err)
		assert.Equal(t, "urgent", updated.Priority)
	})

	t.Run("UpdateMultipleFields", func(t *testing.T) {
		created, err := CreateTask(createTestTask("Test Task"))
		require.NoError(t, err)

		newTitle := "New Title"
		newStatus := "completed"
		newPriority := "high"
		update := &models.TaskUpdate{
			Title:    &newTitle,
			Status:   &newStatus,
			Priority: &newPriority,
		}
		updated, err := UpdateTask(created.ID, update)
		
		require.NoError(t, err)
		assert.Equal(t, "New Title", updated.Title)
		assert.Equal(t, "completed", updated.Status)
		assert.Equal(t, "high", updated.Priority)
	})

	t.Run("UpdateTaskUpdatesTimestamp", func(t *testing.T) {
		created, err := CreateTask(createTestTask("Test Task"))
		require.NoError(t, err)
		originalUpdatedAt := created.UpdatedAt

		time.Sleep(10 * time.Millisecond) // Ensure timestamp difference

		newTitle := "Updated"
		update := &models.TaskUpdate{Title: &newTitle}
		updated, err := UpdateTask(created.ID, update)
		
		require.NoError(t, err)
		assert.True(t, updated.UpdatedAt.After(originalUpdatedAt))
	})

	t.Run("UpdateNonExistentTask", func(t *testing.T) {
		newTitle := "Updated"
		update := &models.TaskUpdate{Title: &newTitle}
		_, err := UpdateTask(999999, update)
		
		// GetTaskByID is called after update, so it will return error
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "task not found")
	})

	t.Run("UpdateTaskWithEmptyUpdate", func(t *testing.T) {
		created, err := CreateTask(createTestTask("Test Task"))
		require.NoError(t, err)

		update := &models.TaskUpdate{}
		updated, err := UpdateTask(created.ID, update)
		
		require.NoError(t, err)
		// Only updated_at should change
		assert.Equal(t, created.Title, updated.Title)
		assert.Equal(t, created.Status, updated.Status)
	})

	t.Run("UpdateTaskCategory", func(t *testing.T) {
		created, err := CreateTask(createTestTask("Test Task"))
		require.NoError(t, err)

		newCategory := "personal"
		update := &models.TaskUpdate{Category: &newCategory}
		updated, err := UpdateTask(created.ID, update)
		
		require.NoError(t, err)
		assert.Equal(t, "personal", updated.Category)
	})

	t.Run("UpdateTaskEmailID", func(t *testing.T) {
		created, err := CreateTask(createTestTask("Test Task"))
		require.NoError(t, err)

		newEmailID := "new-email-456"
		update := &models.TaskUpdate{EmailID: &newEmailID}
		updated, err := UpdateTask(created.ID, update)
		
		require.NoError(t, err)
		assert.NotNil(t, updated.EmailID)
		assert.Equal(t, "new-email-456", *updated.EmailID)
	})

	t.Run("UpdateTaskDueDate", func(t *testing.T) {
		created, err := CreateTask(createTestTask("Test Task"))
		require.NoError(t, err)

		newDueDate := time.Now().Add(48 * time.Hour)
		update := &models.TaskUpdate{DueDate: &newDueDate}
		updated, err := UpdateTask(created.ID, update)
		
		require.NoError(t, err)
		assert.NotNil(t, updated.DueDate)
		assert.WithinDuration(t, newDueDate, *updated.DueDate, time.Second)
	})
}

func TestDeleteTask(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	t.Run("DeleteExistingTask", func(t *testing.T) {
		created, err := CreateTask(createTestTask("Task to Delete"))
		require.NoError(t, err)

		err = DeleteTask(created.ID)
		assert.NoError(t, err)

		// Verify task is deleted
		_, err = GetTaskByID(created.ID)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "task not found")
	})

	t.Run("DeleteNonExistentTask", func(t *testing.T) {
		err := DeleteTask(999999)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "task not found")
	})

	t.Run("DeleteTaskDoesNotAffectOthers", func(t *testing.T) {
		task1, err := CreateTask(createTestTask("Task 1"))
		require.NoError(t, err)
		
		task2, err := CreateTask(createTestTask("Task 2"))
		require.NoError(t, err)

		err = DeleteTask(task1.ID)
		require.NoError(t, err)

		// Task 2 should still exist
		retrieved, err := GetTaskByID(task2.ID)
		require.NoError(t, err)
		assert.Equal(t, task2.ID, retrieved.ID)
	})
}

func TestGetTaskStats(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	// Create diverse set of tasks
	now := time.Now()
	tasks := []*models.TaskCreate{
		createTestTask("Task 1"),
		createTestTask("Task 2"),
		createTestTask("Task 3"),
		createTestTask("Task 4"),
		createTestTask("Task 5"),
	}
	tasks[0].Status = "pending"
	tasks[0].Priority = "high"
	tasks[0].Category = "work"
	tasks[1].Status = "completed"
	tasks[1].Priority = "medium"
	tasks[1].Category = "work"
	tasks[2].Status = "pending"
	tasks[2].Priority = "low"
	tasks[2].Category = "personal"
	tasks[3].Status = "in_progress"
	tasks[3].Priority = "urgent"
	tasks[3].Category = "work"
	
	// Task 5 is overdue
	overdueDueDate := now.Add(-24 * time.Hour)
	tasks[4].Status = "pending"
	tasks[4].Priority = "high"
	tasks[4].Category = "urgent" // Add category
	tasks[4].DueDate = &overdueDueDate

	for _, tc := range tasks {
		_, err := CreateTask(tc)
		require.NoError(t, err)
	}

	t.Run("GetBasicStats", func(t *testing.T) {
		stats, err := GetTaskStats()
		require.NoError(t, err)
		assert.NotNil(t, stats)

		total := stats["total_tasks"].(int)
		assert.Equal(t, 5, total)
	})

	t.Run("GetTasksByStatus", func(t *testing.T) {
		stats, err := GetTaskStats()
		require.NoError(t, err)

		statusStats := stats["tasks_by_status"].(map[string]int)
		assert.Equal(t, 3, statusStats["pending"])
		assert.Equal(t, 1, statusStats["completed"])
		assert.Equal(t, 1, statusStats["in_progress"])

		// Check individual status counts
		assert.Equal(t, 3, stats["pending_tasks"].(int))
		assert.Equal(t, 1, stats["completed_tasks"].(int))
	})

	t.Run("GetTasksByPriority", func(t *testing.T) {
		stats, err := GetTaskStats()
		require.NoError(t, err)

		priorityStats := stats["tasks_by_priority"].(map[string]int)
		assert.Equal(t, 2, priorityStats["high"])
		assert.Equal(t, 1, priorityStats["medium"])
		assert.Equal(t, 1, priorityStats["low"])
		assert.Equal(t, 1, priorityStats["urgent"])
	})

	t.Run("GetTasksByCategory", func(t *testing.T) {
		stats, err := GetTaskStats()
		require.NoError(t, err)

		categoryStats := stats["tasks_by_category"].(map[string]int)
		assert.Equal(t, 3, categoryStats["work"])
		assert.Equal(t, 1, categoryStats["personal"])
		assert.Equal(t, 1, categoryStats["urgent"])
	})

	t.Run("GetOverdueTasks", func(t *testing.T) {
		stats, err := GetTaskStats()
		require.NoError(t, err)

		overdue := stats["overdue_tasks"].(int)
		assert.Equal(t, 1, overdue) // Only one overdue task
	})

	t.Run("CompletedTasksNotCountedAsOverdue", func(t *testing.T) {
		// Create a completed task that's past due date
		pastDue := time.Now().Add(-48 * time.Hour)
		taskCreate := createTestTask("Completed but overdue")
		taskCreate.Status = "completed"
		taskCreate.DueDate = &pastDue
		_, err := CreateTask(taskCreate)
		require.NoError(t, err)

		stats, err := GetTaskStats()
		require.NoError(t, err)

		overdue := stats["overdue_tasks"].(int)
		assert.Equal(t, 1, overdue) // Should still be 1, not counting completed task
	})

	t.Run("StatsWithNoTasks", func(t *testing.T) {
		// Clear database
		testDB, _ := GetDB()
		_, err := testDB.Exec("DELETE FROM tasks")
		require.NoError(t, err)

		stats, err := GetTaskStats()
		require.NoError(t, err)
		
		assert.Equal(t, 0, stats["total_tasks"].(int))
		assert.Equal(t, 0, stats["overdue_tasks"].(int))
	})
}

func TestGetTasksByEmailID(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	emailID1 := "email-123"
	emailID2 := "email-456"

	// Create tasks linked to different emails
	task1 := createTestTask("Task 1")
	task1.EmailID = &emailID1
	_, err := CreateTask(task1)
	require.NoError(t, err)

	task2 := createTestTask("Task 2")
	task2.EmailID = &emailID1
	_, err = CreateTask(task2)
	require.NoError(t, err)

	task3 := createTestTask("Task 3")
	task3.EmailID = &emailID2
	_, err = CreateTask(task3)
	require.NoError(t, err)

	t.Run("GetTasksForEmail", func(t *testing.T) {
		tasks, err := GetTasksByEmailID(emailID1)
		require.NoError(t, err)
		assert.Len(t, tasks, 2)
		for _, task := range tasks {
			assert.NotNil(t, task.EmailID)
			assert.Equal(t, emailID1, *task.EmailID)
		}
	})

	t.Run("GetTasksForDifferentEmail", func(t *testing.T) {
		tasks, err := GetTasksByEmailID(emailID2)
		require.NoError(t, err)
		assert.Len(t, tasks, 1)
		assert.Equal(t, emailID2, *tasks[0].EmailID)
	})

	t.Run("GetTasksForNonExistentEmail", func(t *testing.T) {
		tasks, err := GetTasksByEmailID("nonexistent-email")
		require.NoError(t, err)
		assert.Len(t, tasks, 0)
	})

	t.Run("TasksOrderedByCreatedDate", func(t *testing.T) {
		emailID := "email-ordered"
		
		// Create tasks with time delay
		for i := 0; i < 3; i++ {
			taskCreate := createTestTask("Ordered Task " + string(rune('A'+i)))
			taskCreate.EmailID = &emailID
			_, err := CreateTask(taskCreate)
			require.NoError(t, err)
			time.Sleep(10 * time.Millisecond)
		}

		tasks, err := GetTasksByEmailID(emailID)
		require.NoError(t, err)
		assert.Len(t, tasks, 3)
		
		// Should be in DESC order (newest first)
		assert.Contains(t, tasks[0].Title, "Ordered Task C")
	})
}

func TestBulkUpdateTasks(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	// Create multiple tasks
	var taskIDs []int
	for i := 0; i < 3; i++ {
		task, err := CreateTask(createTestTask("Bulk Task " + string(rune('A'+i))))
		require.NoError(t, err)
		taskIDs = append(taskIDs, task.ID)
	}

	t.Run("BulkUpdateStatus", func(t *testing.T) {
		newStatus := "completed"
		update := &models.TaskUpdate{Status: &newStatus}
		
		err := BulkUpdateTasks(taskIDs, update)
		require.NoError(t, err)

		// Verify all tasks updated
		for _, id := range taskIDs {
			task, err := GetTaskByID(id)
			require.NoError(t, err)
			assert.Equal(t, "completed", task.Status)
			assert.NotNil(t, task.CompletedAt)
		}
	})

	t.Run("BulkUpdatePriority", func(t *testing.T) {
		newPriority := "urgent"
		update := &models.TaskUpdate{Priority: &newPriority}
		
		err := BulkUpdateTasks(taskIDs, update)
		require.NoError(t, err)

		for _, id := range taskIDs {
			task, err := GetTaskByID(id)
			require.NoError(t, err)
			assert.Equal(t, "urgent", task.Priority)
		}
	})

	t.Run("BulkUpdateMultipleFields", func(t *testing.T) {
		newStatus := "in_progress"
		newPriority := "high"
		newCategory := "urgent-work"
		update := &models.TaskUpdate{
			Status:   &newStatus,
			Priority: &newPriority,
			Category: &newCategory,
		}
		
		err := BulkUpdateTasks(taskIDs, update)
		require.NoError(t, err)

		for _, id := range taskIDs {
			task, err := GetTaskByID(id)
			require.NoError(t, err)
			assert.Equal(t, "in_progress", task.Status)
			assert.Equal(t, "high", task.Priority)
			assert.Equal(t, "urgent-work", task.Category)
		}
	})

	t.Run("BulkUpdateWithEmptyList", func(t *testing.T) {
		newStatus := "completed"
		update := &models.TaskUpdate{Status: &newStatus}
		
		err := BulkUpdateTasks([]int{}, update)
		assert.NoError(t, err) // Should not error
	})

	t.Run("BulkUpdateDoesNotAffectOtherTasks", func(t *testing.T) {
		// Create a task not in the bulk update list
		otherTask, err := CreateTask(createTestTask("Other Task"))
		require.NoError(t, err)
		originalStatus := otherTask.Status

		// Update only the bulk task IDs
		newStatus := "cancelled"
		update := &models.TaskUpdate{Status: &newStatus}
		err = BulkUpdateTasks(taskIDs, update)
		require.NoError(t, err)

		// Verify other task unchanged
		retrieved, err := GetTaskByID(otherTask.ID)
		require.NoError(t, err)
		assert.Equal(t, originalStatus, retrieved.Status)
	})
}

func TestBulkDeleteTasks(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	t.Run("BulkDeleteMultipleTasks", func(t *testing.T) {
		// Create tasks to delete
		var taskIDs []int
		for i := 0; i < 3; i++ {
			task, err := CreateTask(createTestTask("Delete Task " + string(rune('A'+i))))
			require.NoError(t, err)
			taskIDs = append(taskIDs, task.ID)
		}

		err := BulkDeleteTasks(taskIDs)
		require.NoError(t, err)

		// Verify all tasks deleted
		for _, id := range taskIDs {
			_, err := GetTaskByID(id)
			assert.Error(t, err)
			assert.Contains(t, err.Error(), "task not found")
		}
	})

	t.Run("BulkDeleteWithEmptyList", func(t *testing.T) {
		err := BulkDeleteTasks([]int{})
		assert.NoError(t, err) // Should not error
	})

	t.Run("BulkDeleteDoesNotAffectOtherTasks", func(t *testing.T) {
		// Create tasks to delete
		var taskIDs []int
		for i := 0; i < 2; i++ {
			task, err := CreateTask(createTestTask("Bulk Delete " + string(rune('A'+i))))
			require.NoError(t, err)
			taskIDs = append(taskIDs, task.ID)
		}

		// Create a task to keep
		keepTask, err := CreateTask(createTestTask("Keep Task"))
		require.NoError(t, err)

		err = BulkDeleteTasks(taskIDs)
		require.NoError(t, err)

		// Verify keep task still exists
		retrieved, err := GetTaskByID(keepTask.ID)
		require.NoError(t, err)
		assert.Equal(t, keepTask.ID, retrieved.ID)
	})
}

func TestTasksSQLInjectionPrevention(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	t.Run("SearchWithSQLInjectionAttempt", func(t *testing.T) {
		// Create a normal task
		_, err := CreateTask(createTestTask("Normal Task"))
		require.NoError(t, err)

		// Try SQL injection in search
		maliciousSearch := "'; DROP TABLE tasks; --"
		tasks, total, err := GetTasks(1, 10, "", "", maliciousSearch)
		
		// Should not error and should not execute injection
		require.NoError(t, err)
		assert.Equal(t, 0, total)
		assert.Len(t, tasks, 0)

		// Verify table still exists by querying
		allTasks, _, err := GetTasks(1, 10, "", "", "")
		require.NoError(t, err)
		assert.GreaterOrEqual(t, len(allTasks), 1)
	})

	t.Run("UpdateWithSQLInjectionAttempt", func(t *testing.T) {
		task, err := CreateTask(createTestTask("Test Task"))
		require.NoError(t, err)

		maliciousTitle := "'; DROP TABLE tasks; --"
		update := &models.TaskUpdate{Title: &maliciousTitle}
		_, err = UpdateTask(task.ID, update)
		
		// Should not error
		require.NoError(t, err)

		// Verify the malicious string was stored as literal text
		updated, err := GetTaskByID(task.ID)
		require.NoError(t, err)
		assert.Equal(t, maliciousTitle, updated.Title)
	})
}

func TestTasksConcurrentAccess(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	t.Run("ConcurrentTaskCreation", func(t *testing.T) {
		var wg sync.WaitGroup
		taskCount := 10

		for i := 0; i < taskCount; i++ {
			wg.Add(1)
			go func(index int) {
				defer wg.Done()
				taskCreate := createTestTask("Concurrent Task " + string(rune('A'+index)))
				_, err := CreateTask(taskCreate)
				assert.NoError(t, err)
			}(i)
		}

		wg.Wait()

		// Verify all tasks created
		tasks, total, err := GetTasks(1, 20, "", "", "")
		require.NoError(t, err)
		assert.GreaterOrEqual(t, total, taskCount)
		assert.GreaterOrEqual(t, len(tasks), taskCount)
	})

	t.Run("ConcurrentTaskUpdates", func(t *testing.T) {
		task, err := CreateTask(createTestTask("Update Test"))
		require.NoError(t, err)

		var wg sync.WaitGroup
		updateCount := 5

		for i := 0; i < updateCount; i++ {
			wg.Add(1)
			go func(index int) {
				defer wg.Done()
				newTitle := "Updated " + string(rune('A'+index))
				update := &models.TaskUpdate{Title: &newTitle}
				_, err := UpdateTask(task.ID, update)
				assert.NoError(t, err)
			}(i)
		}

		wg.Wait()

		// Task should exist and have one of the updated titles
		updated, err := GetTaskByID(task.ID)
		require.NoError(t, err)
		assert.Contains(t, updated.Title, "Updated")
	})
}

func TestTasksDatabaseNotInitialized(t *testing.T) {
	// Reset DB to nil
	db = nil
	once = sync.Once{}

	t.Run("CreateTaskWithoutDB", func(t *testing.T) {
		_, err := CreateTask(createTestTask("Test"))
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "database not initialized")
	})

	t.Run("GetTasksWithoutDB", func(t *testing.T) {
		_, _, err := GetTasks(1, 10, "", "", "")
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "database not initialized")
	})

	t.Run("GetTaskByIDWithoutDB", func(t *testing.T) {
		_, err := GetTaskByID(1)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "database not initialized")
	})

	t.Run("UpdateTaskWithoutDB", func(t *testing.T) {
		newTitle := "Test"
		update := &models.TaskUpdate{Title: &newTitle}
		_, err := UpdateTask(1, update)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "database not initialized")
	})

	t.Run("DeleteTaskWithoutDB", func(t *testing.T) {
		err := DeleteTask(1)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "database not initialized")
	})

	t.Run("GetTaskStatsWithoutDB", func(t *testing.T) {
		_, err := GetTaskStats()
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "database not initialized")
	})

	t.Run("GetTasksByEmailIDWithoutDB", func(t *testing.T) {
		_, err := GetTasksByEmailID("test")
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "database not initialized")
	})
}
