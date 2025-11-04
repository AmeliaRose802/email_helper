package handlers

import (
	"net/http"
	"strconv"

	"email-helper-backend/internal/models"

	"github.com/gin-gonic/gin"
)

// GetTasks retrieves paginated list of tasks
func GetTasks(c *gin.Context) {
	pageStr := c.DefaultQuery("page", "1")
	limitStr := c.DefaultQuery("limit", "20")
	status := c.Query("status")
	priority := c.Query("priority")
	search := c.Query("search")

	page, _ := strconv.Atoi(pageStr)
	limit, _ := strconv.Atoi(limitStr)

	if page < 1 {
		page = 1
	}
	if limit < 1 || limit > 100 {
		limit = 20
	}

	tasks, total, err := taskService.GetTasks(page, limit, status, priority, search)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	hasNext := page*limit < total

	// Convert []*models.Task to []models.Task
	taskList := make([]models.Task, len(tasks))
	for i, t := range tasks {
		if t != nil {
			taskList[i] = *t
		}
	}

	c.JSON(http.StatusOK, models.TaskListResponse{
		Tasks:      taskList,
		TotalCount: total,
		Page:       page,
		PageSize:   limit,
		HasNext:    hasNext,
	})
}

// CreateTask creates a new task
func CreateTask(c *gin.Context) {
	var req models.TaskCreate
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	task, err := taskService.CreateTask(&req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, task)
}

// GetTask retrieves a task by ID
func GetTask(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid task ID"})
		return
	}

	task, err := taskService.GetTask(id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Task not found"})
		return
	}

	c.JSON(http.StatusOK, task)
}

// UpdateTask updates a task
func UpdateTask(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid task ID"})
		return
	}

	var req models.TaskUpdate
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	task, err := taskService.UpdateTask(id, &req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, task)
}

// DeleteTask deletes a task
func DeleteTask(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid task ID"})
		return
	}

	if err := taskService.DeleteTask(id); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Task deleted",
	})
}

// GetTaskStats retrieves task statistics
func GetTaskStats(c *gin.Context) {
	stats, err := taskService.GetStats()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, stats)
}

// UpdateTaskStatus updates task status
func UpdateTaskStatus(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid task ID"})
		return
	}

	var req struct {
		Status string `json:"status" binding:"required"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	update := models.TaskUpdate{
		Status: &req.Status,
	}

	task, err := taskService.UpdateTask(id, &update)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, task)
}

// LinkEmailToTask links an email to a task
func LinkEmailToTask(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid task ID"})
		return
	}

	var req struct {
		EmailID string `json:"email_id" binding:"required"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	update := models.TaskUpdate{
		EmailID: &req.EmailID,
	}

	task, err := taskService.UpdateTask(id, &update)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, task)
}

// BulkUpdateTasks updates multiple tasks
func BulkUpdateTasks(c *gin.Context) {
	var req models.BulkTaskUpdate
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if err := taskService.BulkUpdate(req.TaskIDs, &req.Updates); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Tasks updated",
		"count":   len(req.TaskIDs),
	})
}

// BulkDeleteTasks deletes multiple tasks
func BulkDeleteTasks(c *gin.Context) {
	var req models.BulkTaskDelete
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if err := taskService.BulkDelete(req.TaskIDs); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Tasks deleted",
		"count":   len(req.TaskIDs),
	})
}

// DeduplicateFYITasks deduplicates FYI tasks (stub for now)
func DeduplicateFYITasks(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"error": "Not implemented yet"})
}

// DeduplicateNewsletterTasks deduplicates newsletter tasks (stub for now)
func DeduplicateNewsletterTasks(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{"error": "Not implemented yet"})
}
