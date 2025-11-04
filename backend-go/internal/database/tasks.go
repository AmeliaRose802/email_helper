package database

import (
	"database/sql"
	"fmt"
	"time"

	"email-helper-backend/internal/models"
)

// CreateTask creates a new task
func CreateTask(task *models.TaskCreate) (*models.Task, error) {
	db, err := GetDB()
	if err != nil {
		return nil, err
	}

	query := `
		INSERT INTO tasks (
			user_id, title, description, status, priority, category, email_id, one_line_summary, due_date, created_at, updated_at
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`

	now := time.Now()
	status := task.Status
	if status == "" {
		status = "pending"
	}
	priority := task.Priority
	if priority == "" {
		priority = "medium"
	}

	result, err := db.Exec(query,
		1, // Default user_id
		task.Title,
		task.Description,
		status,
		priority,
		task.Category,
		task.EmailID,
		task.OneLineSummary,
		task.DueDate,
		now,
		now,
	)
	if err != nil {
		return nil, err
	}

	id, err := result.LastInsertId()
	if err != nil {
		return nil, err
	}

	return GetTaskByID(int(id))
}

// GetTaskByID retrieves a task by ID
func GetTaskByID(id int) (*models.Task, error) {
	db, err := GetDB()
	if err != nil {
		return nil, err
	}

	query := `
		SELECT id, user_id, title, description, status, priority, category, email_id,
		       one_line_summary, due_date, created_at, updated_at, completed_at
		FROM tasks
		WHERE id = ?
	`

	task := &models.Task{}
	var description sql.NullString
	var category sql.NullString
	var emailID sql.NullString
	var oneLineSummary sql.NullString
	var dueDate sql.NullTime
	var completedAt sql.NullTime
	
	err = db.QueryRow(query, id).Scan(
		&task.ID,
		&task.UserID,
		&task.Title,
		&description,
		&task.Status,
		&task.Priority,
		&category,
		&emailID,
		&oneLineSummary,
		&dueDate,
		&task.CreatedAt,
		&task.UpdatedAt,
		&completedAt,
	)

	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("task not found")
	}
	if err != nil {
		return nil, err
	}

	// Map nullable fields
	task.Description = description.String
	task.Category = category.String
	if emailID.Valid {
		task.EmailID = &emailID.String
	}
	if oneLineSummary.Valid {
		task.OneLineSummary = &oneLineSummary.String
	}
	if dueDate.Valid {
		task.DueDate = &dueDate.Time
	}
	if completedAt.Valid {
		task.CompletedAt = &completedAt.Time
	}

	return task, nil
}

// GetTasks retrieves tasks with pagination and filtering
func GetTasks(page, limit int, status, priority, search string) ([]*models.Task, int, error) {
	db, err := GetDB()
	if err != nil {
		return nil, 0, err
	}

	offset := (page - 1) * limit

	// Build where clause - exclude test data by default
	whereClause := `WHERE user_id = 1 
		AND (category IS NULL OR category != 'test')
		AND title NOT LIKE '%Test Task%'
		AND title NOT LIKE '%Bulk Update%'
		AND title NOT LIKE '%Random Task%'
		AND title NOT LIKE '%Specific Task%'
		AND title NOT LIKE '%Pagination Test%'
		AND title NOT LIKE '%Email-linked Task%'
		AND title NOT LIKE '%Minimal Task%'`
	args := []interface{}{}

	if status != "" {
		whereClause += " AND status = ?"
		args = append(args, status)
	}

	if priority != "" {
		whereClause += " AND priority = ?"
		args = append(args, priority)
	}

	if search != "" {
		whereClause += " AND (title LIKE ? OR description LIKE ?)"
		searchPattern := "%" + search + "%"
		args = append(args, searchPattern, searchPattern)
	}

	// Count total
	countQuery := fmt.Sprintf("SELECT COUNT(*) FROM tasks %s", whereClause)
	var total int
	err = db.QueryRow(countQuery, args...).Scan(&total)
	if err != nil {
		return nil, 0, err
	}

	// Get tasks
	query := fmt.Sprintf(`
		SELECT id, user_id, title, description, status, priority, category, email_id,
		       one_line_summary, due_date, created_at, updated_at, completed_at
		FROM tasks
		%s
		ORDER BY created_at DESC
		LIMIT ? OFFSET ?
	`, whereClause)

	args = append(args, limit, offset)
	rows, err := db.Query(query, args...)
	if err != nil {
		return nil, 0, err
	}
	defer rows.Close()

	var tasks []*models.Task
	for rows.Next() {
		task := &models.Task{}
		var description sql.NullString
		var category sql.NullString
		var emailID sql.NullString
		var oneLineSummary sql.NullString
		var dueDate sql.NullTime
		var completedAt sql.NullTime
		
		err := rows.Scan(
			&task.ID,
			&task.UserID,
			&task.Title,
			&description,
			&task.Status,
			&task.Priority,
			&category,
			&emailID,
			&oneLineSummary,
			&dueDate,
			&task.CreatedAt,
			&task.UpdatedAt,
			&completedAt,
		)
		if err != nil {
			return nil, 0, err
		}
		
		// Map nullable fields
		task.Description = description.String
		task.Category = category.String
		if emailID.Valid {
			task.EmailID = &emailID.String
		}
		if oneLineSummary.Valid {
			task.OneLineSummary = &oneLineSummary.String
		}
		if dueDate.Valid {
			task.DueDate = &dueDate.Time
		}
		if completedAt.Valid {
			task.CompletedAt = &completedAt.Time
		}
		
		tasks = append(tasks, task)
	}

	return tasks, total, nil
}

// UpdateTask updates an existing task
func UpdateTask(id int, update *models.TaskUpdate) (*models.Task, error) {
	db, err := GetDB()
	if err != nil {
		return nil, err
	}

	// Build dynamic update query
	setClause := "updated_at = ?"
	args := []interface{}{time.Now()}

	if update.Title != nil {
		setClause += ", title = ?"
		args = append(args, *update.Title)
	}
	if update.Description != nil {
		setClause += ", description = ?"
		args = append(args, *update.Description)
	}
	if update.Status != nil {
		setClause += ", status = ?"
		args = append(args, *update.Status)
		// Set completed_at if status is completed
		if *update.Status == "completed" {
			setClause += ", completed_at = ?"
			args = append(args, time.Now())
		}
	}
	if update.Priority != nil {
		setClause += ", priority = ?"
		args = append(args, *update.Priority)
	}
	if update.Category != nil {
		setClause += ", category = ?"
		args = append(args, *update.Category)
	}
	if update.EmailID != nil {
		setClause += ", email_id = ?"
		args = append(args, *update.EmailID)
	}
	if update.OneLineSummary != nil {
		setClause += ", one_line_summary = ?"
		args = append(args, *update.OneLineSummary)
	}
	if update.DueDate != nil {
		setClause += ", due_date = ?"
		args = append(args, *update.DueDate)
	}

	args = append(args, id)
	query := fmt.Sprintf("UPDATE tasks SET %s WHERE id = ?", setClause)

	_, err = db.Exec(query, args...)
	if err != nil {
		return nil, err
	}

	return GetTaskByID(id)
}

// DeleteTask deletes a task
func DeleteTask(id int) error {
	db, err := GetDB()
	if err != nil {
		return err
	}

	query := "DELETE FROM tasks WHERE id = ?"
	result, err := db.Exec(query, id)
	if err != nil {
		return err
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return err
	}

	if rows == 0 {
		return fmt.Errorf("task not found")
	}

	return nil
}

// GetTaskStats retrieves task statistics
func GetTaskStats() (map[string]interface{}, error) {
	db, err := GetDB()
	if err != nil {
		return nil, err
	}

	stats := make(map[string]interface{})

	// Total tasks
	var total int
	err = db.QueryRow("SELECT COUNT(*) FROM tasks WHERE user_id = 1").Scan(&total)
	if err != nil {
		return nil, err
	}
	stats["total_tasks"] = total

	// Tasks by status
	statusQuery := `
		SELECT status, COUNT(*) as count
		FROM tasks
		WHERE user_id = 1
		GROUP BY status
	`
	rows, err := db.Query(statusQuery)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	tasksByStatus := make(map[string]int)
	for rows.Next() {
		var status string
		var count int
		if err := rows.Scan(&status, &count); err != nil {
			return nil, err
		}
		tasksByStatus[status] = count
		// Also set individual counts
		if status == "pending" {
			stats["pending_tasks"] = count
		} else if status == "completed" {
			stats["completed_tasks"] = count
		}
	}
	stats["tasks_by_status"] = tasksByStatus

	// Tasks by priority
	priorityQuery := `
		SELECT priority, COUNT(*) as count
		FROM tasks
		WHERE user_id = 1
		GROUP BY priority
	`
	rows, err = db.Query(priorityQuery)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	tasksByPriority := make(map[string]int)
	for rows.Next() {
		var priority string
		var count int
		if err := rows.Scan(&priority, &count); err != nil {
			return nil, err
		}
		tasksByPriority[priority] = count
	}
	stats["tasks_by_priority"] = tasksByPriority

	// Tasks by category
	categoryQuery := `
		SELECT category, COUNT(*) as count
		FROM tasks
		WHERE user_id = 1 AND category IS NOT NULL AND category != ''
		GROUP BY category
	`
	rows, err = db.Query(categoryQuery)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	tasksByCategory := make(map[string]int)
	for rows.Next() {
		var category string
		var count int
		if err := rows.Scan(&category, &count); err != nil {
			return nil, err
		}
		tasksByCategory[category] = count
	}
	stats["tasks_by_category"] = tasksByCategory

	// Overdue tasks
	overdueQuery := `
		SELECT COUNT(*)
		FROM tasks
		WHERE user_id = 1
		  AND status != 'completed'
		  AND due_date IS NOT NULL
		  AND due_date < ?
	`
	var overdue int
	err = db.QueryRow(overdueQuery, time.Now()).Scan(&overdue)
	if err != nil {
		return nil, err
	}
	stats["overdue_tasks"] = overdue

	return stats, nil
}

// BulkUpdateTasks updates multiple tasks at once
func BulkUpdateTasks(taskIDs []int, update *models.TaskUpdate) error {
	if len(taskIDs) == 0 {
		return nil
	}

	db, err := GetDB()
	if err != nil {
		return err
	}

	tx, err := db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// Build the SET clause dynamically based on provided fields
	setClause := "updated_at = CURRENT_TIMESTAMP"
	args := []interface{}{}
	
	if update.Title != nil {
		setClause += ", title = ?"
		args = append(args, *update.Title)
	}
	if update.Description != nil {
		setClause += ", description = ?"
		args = append(args, *update.Description)
	}
	if update.Status != nil {
		setClause += ", status = ?"
		args = append(args, *update.Status)
		// Set completed_at if status is completed
		if *update.Status == "completed" {
			setClause += ", completed_at = CURRENT_TIMESTAMP"
		}
	}
	if update.Priority != nil {
		setClause += ", priority = ?"
		args = append(args, *update.Priority)
	}
	if update.Category != nil {
		setClause += ", category = ?"
		args = append(args, *update.Category)
	}
	if update.EmailID != nil {
		setClause += ", email_id = ?"
		args = append(args, *update.EmailID)
	}
	if update.OneLineSummary != nil {
		setClause += ", one_line_summary = ?"
		args = append(args, *update.OneLineSummary)
	}
	if update.DueDate != nil {
		setClause += ", due_date = ?"
		args = append(args, *update.DueDate)
	}

	// Update each task within the transaction
	for _, id := range taskIDs {
		taskArgs := append([]interface{}{}, args...)
		taskArgs = append(taskArgs, id)
		query := fmt.Sprintf("UPDATE tasks SET %s WHERE id = ?", setClause)
		
		if _, err := tx.Exec(query, taskArgs...); err != nil {
			return err
		}
	}

	return tx.Commit()
}

// BulkDeleteTasks deletes multiple tasks at once
func BulkDeleteTasks(taskIDs []int) error {
	if len(taskIDs) == 0 {
		return nil
	}

	db, err := GetDB()
	if err != nil {
		return err
	}

	tx, err := db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// Build IN clause
	query := fmt.Sprintf("DELETE FROM tasks WHERE id IN (?%s)", repeatPlaceholder(len(taskIDs)-1))
	args := make([]interface{}, len(taskIDs))
	for i, id := range taskIDs {
		args[i] = id
	}

	_, err = tx.Exec(query, args...)
	if err != nil {
		return err
	}

	return tx.Commit()
}

// GetTasksByEmailID retrieves all tasks linked to an email
func GetTasksByEmailID(emailID string) ([]*models.Task, error) {
	db, err := GetDB()
	if err != nil {
		return nil, err
	}

	query := `
		SELECT id, user_id, title, description, status, priority, category, email_id,
		       one_line_summary, due_date, created_at, updated_at, completed_at
		FROM tasks
		WHERE email_id = ?
		ORDER BY created_at DESC
	`

	rows, err := db.Query(query, emailID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var tasks []*models.Task
	for rows.Next() {
		task := &models.Task{}
		var description sql.NullString
		var category sql.NullString
		var emailID sql.NullString
		var oneLineSummary sql.NullString
		var dueDate sql.NullTime
		var completedAt sql.NullTime
		
		err := rows.Scan(
			&task.ID,
			&task.UserID,
			&task.Title,
			&description,
			&task.Status,
			&task.Priority,
			&category,
			&emailID,
			&oneLineSummary,
			&dueDate,
			&task.CreatedAt,
			&task.UpdatedAt,
			&completedAt,
		)
		if err != nil {
			return nil, err
		}
		
		// Map nullable fields
		task.Description = description.String
		task.Category = category.String
		if emailID.Valid {
			task.EmailID = &emailID.String
		}
		if oneLineSummary.Valid {
			task.OneLineSummary = &oneLineSummary.String
		}
		if dueDate.Valid {
			task.DueDate = &dueDate.Time
		}
		if completedAt.Valid {
			task.CompletedAt = &completedAt.Time
		}
		
		tasks = append(tasks, task)
	}

	return tasks, nil
}

// GetTasksByCategory retrieves all tasks with a specific category
func GetTasksByCategory(category string) ([]*models.Task, error) {
	db, err := GetDB()
	if err != nil {
		return nil, err
	}

	query := `
		SELECT id, user_id, title, description, status, priority, category, email_id,
		       one_line_summary, due_date, created_at, updated_at, completed_at
		FROM tasks
		WHERE category = ? AND user_id = 1
		ORDER BY created_at DESC
	`

	rows, err := db.Query(query, category)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var tasks []*models.Task
	for rows.Next() {
		task := &models.Task{}
		var description sql.NullString
		var categoryDB sql.NullString
		var emailID sql.NullString
		var oneLineSummary sql.NullString
		var dueDate sql.NullTime
		var completedAt sql.NullTime
		
		err := rows.Scan(
			&task.ID,
			&task.UserID,
			&task.Title,
			&description,
			&task.Status,
			&task.Priority,
			&categoryDB,
			&emailID,
			&oneLineSummary,
			&dueDate,
			&task.CreatedAt,
			&task.UpdatedAt,
			&completedAt,
		)
		if err != nil {
			return nil, err
		}
		
		// Map nullable fields
		task.Description = description.String
		task.Category = categoryDB.String
		if emailID.Valid {
			task.EmailID = &emailID.String
		}
		if oneLineSummary.Valid {
			task.OneLineSummary = &oneLineSummary.String
		}
		if dueDate.Valid {
			task.DueDate = &dueDate.Time
		}
		if completedAt.Valid {
			task.CompletedAt = &completedAt.Time
		}
		
		tasks = append(tasks, task)
	}

	return tasks, nil
}

// Helper function to repeat SQL placeholders
func repeatPlaceholder(count int) string {
	if count <= 0 {
		return ""
	}
	result := ""
	for i := 0; i < count; i++ {
		result += ", ?"
	}
	return result
}
