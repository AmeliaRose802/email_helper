package models

import "time"

// Task represents a task/action item
type Task struct {
	ID             int        `json:"id" db:"id"`
	UserID         int        `json:"user_id" db:"user_id"`
	Title          string     `json:"title" db:"title"`
	Description    string     `json:"description,omitempty" db:"description"`
	Status         string     `json:"status" db:"status"` // pending, in_progress, completed, cancelled
	Priority       string     `json:"priority" db:"priority"` // low, medium, high, urgent
	Category       string     `json:"category,omitempty" db:"category"`
	EmailID        *string    `json:"email_id,omitempty" db:"email_id"`
	OneLineSummary *string    `json:"one_line_summary,omitempty" db:"one_line_summary"`
	DueDate        *time.Time `json:"due_date,omitempty" db:"due_date"`
	CreatedAt      time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt      time.Time  `json:"updated_at" db:"updated_at"`
	CompletedAt    *time.Time `json:"completed_at,omitempty" db:"completed_at"`
}

// TaskCreate request for creating a task
type TaskCreate struct {
	Title          string     `json:"title" binding:"required"`
	Description    string     `json:"description,omitempty"`
	Status         string     `json:"status,omitempty"`
	Priority       string     `json:"priority,omitempty"`
	Category       string     `json:"category,omitempty"`
	EmailID        *string    `json:"email_id,omitempty"`
	OneLineSummary *string    `json:"one_line_summary,omitempty"`
	DueDate        *time.Time `json:"due_date,omitempty"`
}

// TaskUpdate request for updating a task
type TaskUpdate struct {
	Title          *string    `json:"title,omitempty"`
	Description    *string    `json:"description,omitempty"`
	Status         *string    `json:"status,omitempty"`
	Priority       *string    `json:"priority,omitempty"`
	Category       *string    `json:"category,omitempty"`
	EmailID        *string    `json:"email_id,omitempty"`
	OneLineSummary *string    `json:"one_line_summary,omitempty"`
	DueDate        *time.Time `json:"due_date,omitempty"`
}

// TaskListResponse paginated task list
type TaskListResponse struct {
	Tasks      []Task `json:"tasks"`
	TotalCount int    `json:"total_count"`
	Page       int    `json:"page"`
	PageSize   int    `json:"page_size"`
	HasNext    bool   `json:"has_next"`
}

// BulkTaskUpdate for bulk updates
type BulkTaskUpdate struct {
	TaskIDs []int      `json:"task_ids" binding:"required"`
	Updates TaskUpdate `json:"updates" binding:"required"`
}

// BulkTaskDelete for bulk deletions
type BulkTaskDelete struct {
	TaskIDs []int `json:"task_ids" binding:"required"`
}
