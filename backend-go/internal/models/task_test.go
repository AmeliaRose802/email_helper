package models

import (
	"encoding/json"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestTaskSerialization(t *testing.T) {
	now := time.Now()
	dueDate := now.Add(7 * 24 * time.Hour)
	emailID := "email-123"
	summary := "Task summary"

	task := Task{
		ID:             1,
		UserID:         1,
		Title:          "Test Task",
		Description:    "Task description",
		Status:         "pending",
		Priority:       "high",
		Category:       "work",
		EmailID:        &emailID,
		OneLineSummary: &summary,
		DueDate:        &dueDate,
		CreatedAt:      now,
		UpdatedAt:      now,
		CompletedAt:    nil,
	}

	// Test JSON serialization
	jsonData, err := json.Marshal(task)
	assert.NoError(t, err)
	assert.NotEmpty(t, jsonData)

	// Test JSON deserialization
	var decoded Task
	err = json.Unmarshal(jsonData, &decoded)
	assert.NoError(t, err)
	assert.Equal(t, task.ID, decoded.ID)
	assert.Equal(t, task.Title, decoded.Title)
	assert.Equal(t, task.Status, decoded.Status)
	assert.NotNil(t, decoded.EmailID)
	assert.Equal(t, *task.EmailID, *decoded.EmailID)
}

func TestTaskCreate(t *testing.T) {
	dueDate := time.Now().Add(7 * 24 * time.Hour)
	emailID := "email-456"

	taskCreate := TaskCreate{
		Title:       "New Task",
		Description: "New task description",
		Status:      "pending",
		Priority:    "medium",
		Category:    "personal",
		EmailID:     &emailID,
		DueDate:     &dueDate,
	}

	jsonData, err := json.Marshal(taskCreate)
	assert.NoError(t, err)
	assert.Contains(t, string(jsonData), "New Task")
	assert.Contains(t, string(jsonData), "email-456")
}

func TestTaskUpdate(t *testing.T) {
	newStatus := "completed"
	newPriority := "low"
	newTitle := "Updated Task"

	taskUpdate := TaskUpdate{
		Title:    &newTitle,
		Status:   &newStatus,
		Priority: &newPriority,
	}

	jsonData, err := json.Marshal(taskUpdate)
	assert.NoError(t, err)
	assert.Contains(t, string(jsonData), "completed")
	assert.Contains(t, string(jsonData), "Updated Task")

	// Test partial update
	partialUpdate := TaskUpdate{
		Status: &newStatus,
	}

	jsonData, err = json.Marshal(partialUpdate)
	assert.NoError(t, err)
	assert.Contains(t, string(jsonData), "completed")
}

func TestTaskListResponse(t *testing.T) {
	tasks := []Task{
		{ID: 1, Title: "Task 1", Status: "pending"},
		{ID: 2, Title: "Task 2", Status: "completed"},
	}

	response := TaskListResponse{
		Tasks:      tasks,
		TotalCount: 20,
		Page:       1,
		PageSize:   2,
		HasNext:    true,
	}

	jsonData, err := json.Marshal(response)
	assert.NoError(t, err)
	assert.Contains(t, string(jsonData), "Task 1")
	assert.Contains(t, string(jsonData), "has_next")
}

func TestBulkTaskOperations(t *testing.T) {
	// Test bulk update
	newStatus := "completed"
	bulkUpdate := BulkTaskUpdate{
		TaskIDs: []int{1, 2, 3},
		Updates: TaskUpdate{
			Status: &newStatus,
		},
	}

	jsonData, err := json.Marshal(bulkUpdate)
	assert.NoError(t, err)
	assert.Contains(t, string(jsonData), "task_ids")
	assert.Contains(t, string(jsonData), "completed")

	// Test bulk delete
	bulkDelete := BulkTaskDelete{
		TaskIDs: []int{4, 5, 6},
	}

	jsonData, err = json.Marshal(bulkDelete)
	assert.NoError(t, err)
	assert.Contains(t, string(jsonData), "task_ids")
}
