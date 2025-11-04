package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"

	"email-helper-backend/internal/database"
	"email-helper-backend/internal/models"
	"email-helper-backend/pkg/azureopenai"

	"github.com/Azure/azure-sdk-for-go/sdk/ai/azopenai"
	"github.com/Azure/azure-sdk-for-go/sdk/azcore/to"
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

// DeduplicateFYITasks deduplicates FYI tasks using AI
func DeduplicateFYITasks(c *gin.Context) {
	deduplicateTasksByCategory(c, "fyi")
}

// DeduplicateNewsletterTasks deduplicates newsletter tasks using AI
func DeduplicateNewsletterTasks(c *gin.Context) {
	deduplicateTasksByCategory(c, "newsletter")
}

// deduplicateTasksByCategory performs AI-powered task deduplication for a specific category
func deduplicateTasksByCategory(c *gin.Context, category string) {
	// Get all tasks for this category
	tasks, err := database.GetTasksByCategory(category)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to retrieve tasks: %v", err)})
		return
	}

	if len(tasks) == 0 {
		c.JSON(http.StatusOK, gin.H{
			"message":       fmt.Sprintf("No %s tasks found to deduplicate", category),
			"tasks_checked": 0,
			"duplicates":    0,
			"merged":        0,
		})
		return
	}

	// Get AI client from context
	aiClient, exists := c.Get("aiClient")
	if !exists {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "AI client not available"})
		return
	}

	client, ok := aiClient.(*azureopenai.Client)
	if !ok {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Invalid AI client type"})
		return
	}

	// Use AI to identify duplicate groups
	duplicateGroups, err := identifyDuplicateTasks(c.Request.Context(), client, tasks, category)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to identify duplicates: %v", err)})
		return
	}

	if len(duplicateGroups) == 0 {
		c.JSON(http.StatusOK, gin.H{
			"message":       fmt.Sprintf("No duplicate %s tasks found", category),
			"tasks_checked": len(tasks),
			"duplicates":    0,
			"merged":        0,
		})
		return
	}

	// Merge duplicate tasks
	mergedCount := 0
	mergedDetails := []map[string]interface{}{}

	for _, group := range duplicateGroups {
		if len(group) < 2 {
			continue
		}

		// Keep the first task (oldest) and merge content from others
		primaryTask := group[0]
		mergedContent := primaryTask.Description
		if primaryTask.OneLineSummary != nil {
			mergedContent = *primaryTask.OneLineSummary + "\n\n" + mergedContent
		}

		// Collect email IDs from all duplicate tasks
		emailIDs := []string{}
		if primaryTask.EmailID != nil {
			emailIDs = append(emailIDs, *primaryTask.EmailID)
		}

		for i := 1; i < len(group); i++ {
			task := group[i]
			// Add content from duplicate
			if task.OneLineSummary != nil && *task.OneLineSummary != "" {
				mergedContent += "\n• " + *task.OneLineSummary
			}
			if task.EmailID != nil {
				emailIDs = append(emailIDs, *task.EmailID)
			}
		}

		// Update primary task with merged content
		updatedDesc := fmt.Sprintf("[Merged from %d tasks]\n%s\n\nRelated emails: %d", 
			len(group), mergedContent, len(emailIDs))
		update := &models.TaskUpdate{
			Description: &updatedDesc,
		}

		_, err := database.UpdateTask(primaryTask.ID, update)
		if err != nil {
			log.Printf("Warning: Failed to update merged task %d: %v", primaryTask.ID, err)
			continue
		}

		// Delete duplicate tasks
		for i := 1; i < len(group); i++ {
			err := database.DeleteTask(group[i].ID)
			if err != nil {
				log.Printf("Warning: Failed to delete duplicate task %d: %v", group[i].ID, err)
			}
		}

		mergedCount += len(group) - 1
		mergedDetails = append(mergedDetails, map[string]interface{}{
			"primary_task_id": primaryTask.ID,
			"primary_title":   primaryTask.Title,
			"merged_count":    len(group) - 1,
			"email_count":     len(emailIDs),
		})
	}

	c.JSON(http.StatusOK, gin.H{
		"message":        fmt.Sprintf("Successfully deduplicated %s tasks", category),
		"tasks_checked":  len(tasks),
		"duplicate_groups": len(duplicateGroups),
		"tasks_merged":   mergedCount,
		"merged_details": mergedDetails,
	})
}

// identifyDuplicateTasks uses AI to identify groups of duplicate/similar tasks
func identifyDuplicateTasks(ctx context.Context, client *azureopenai.Client, tasks []*models.Task, category string) ([][]*models.Task, error) {
	if len(tasks) < 2 {
		return nil, nil
	}

	// Build task descriptions for AI analysis
	taskDescriptions := make([]string, len(tasks))
	for i, task := range tasks {
		summary := task.Title
		if task.OneLineSummary != nil && *task.OneLineSummary != "" {
			summary = *task.OneLineSummary
		}
		taskDescriptions[i] = fmt.Sprintf("Task %d: %s", task.ID, summary)
	}

	// Create prompt for AI to identify duplicates
	systemPrompt := fmt.Sprintf(`You are an expert at identifying duplicate or highly similar tasks.
Analyze the following %s tasks and identify groups of duplicates that should be merged.

Rules:
1. Tasks are duplicates if they convey essentially the same information or action
2. Minor wording differences don't make tasks unique
3. Group tasks that are about the same topic/email thread
4. Only group tasks that are truly redundant
5. A task can only be in one group

Respond with valid JSON only:
{
  "duplicate_groups": [
    [task_id1, task_id2, task_id3],
    [task_id4, task_id5]
  ],
  "reasoning": "Brief explanation of groupings"
}`, category)

	userPrompt := "Tasks to analyze:\n" + strings.Join(taskDescriptions, "\n")

	// Call AI
	messages := []azopenai.ChatRequestMessageClassification{
		&azopenai.ChatRequestSystemMessage{Content: to.Ptr(systemPrompt)},
		&azopenai.ChatRequestUserMessage{Content: azopenai.NewChatRequestUserMessageContent(userPrompt)},
	}

	resp, err := client.GetChatCompletions(ctx, azopenai.ChatCompletionsOptions{
		Messages:       messages,
		DeploymentName: to.Ptr(os.Getenv("AZURE_OPENAI_DEPLOYMENT")),
		MaxTokens:      to.Ptr[int32](1000),
		Temperature:    to.Ptr[float32](0.3),
	}, nil)

	if err != nil {
		return nil, fmt.Errorf("AI call failed: %w", err)
	}

	if len(resp.Choices) == 0 {
		return nil, fmt.Errorf("no response from AI")
	}

	responseText := *resp.Choices[0].Message.Content
	responseText = strings.TrimPrefix(responseText, "```json")
	responseText = strings.TrimPrefix(responseText, "```")
	responseText = strings.TrimSuffix(responseText, "```")
	responseText = strings.TrimSpace(responseText)

	// Parse AI response
	var result struct {
		DuplicateGroups [][]int `json:"duplicate_groups"`
		Reasoning       string  `json:"reasoning"`
	}

	if err := json.Unmarshal([]byte(responseText), &result); err != nil {
		return nil, fmt.Errorf("failed to parse AI response: %w", err)
	}

	log.Printf("AI identified %d duplicate groups: %s", len(result.DuplicateGroups), result.Reasoning)

	// Convert task IDs to task pointers
	taskMap := make(map[int]*models.Task)
	for _, task := range tasks {
		taskMap[task.ID] = task
	}

	duplicateGroups := [][]*models.Task{}
	for _, idGroup := range result.DuplicateGroups {
		if len(idGroup) < 2 {
			continue
		}

		group := []*models.Task{}
		for _, id := range idGroup {
			if task, exists := taskMap[id]; exists {
				group = append(group, task)
			}
		}

		if len(group) >= 2 {
			duplicateGroups = append(duplicateGroups, group)
		}
	}

	return duplicateGroups, nil
}
