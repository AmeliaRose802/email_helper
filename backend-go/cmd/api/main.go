package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"email-helper-backend/config"
	"email-helper-backend/internal/database"
	"email-helper-backend/internal/handlers"
	"email-helper-backend/internal/services"
	
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

var (
	Version   = "dev"
	BuildTime = "unknown"
)

func main() {
	// Load configuration
	cfg := config.Load()

	// Initialize database
	if err := database.InitDB(cfg.DatabasePath); err != nil {
		log.Fatalf("Failed to initialize database: %v", err)
	}
	defer database.Close()

	// Initialize services
	emailService, err := services.NewEmailService(cfg)
	if err != nil {
		log.Fatalf("Failed to initialize email service: %v", err)
	}
	defer emailService.Close()

	taskService := services.NewTaskService()
	settingsService := services.NewSettingsService()

	// Initialize handlers with services
	handlers.InitializeServices(emailService, taskService, settingsService)

	// Set Gin mode
	if !cfg.Debug {
		gin.SetMode(gin.ReleaseMode)
	}

	// Create router
	router := gin.Default()

	// CORS middleware
	router.Use(cors.New(cors.Config{
		AllowAllOrigins:  true,
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Accept", "Authorization"},
		ExposeHeaders:    []string{"Content-Length"},
		AllowCredentials: false,
		MaxAge:           12 * time.Hour,
	}))

	// Setup routes
	setupRoutes(router, cfg)

	// Server info
	addr := fmt.Sprintf("%s:%d", cfg.Host, cfg.Port)
	log.Printf("Starting Email Helper API v%s (built: %s)", Version, BuildTime)
	log.Printf("Server listening on %s", addr)
	log.Printf("Database: %s", cfg.DatabasePath)
	log.Printf("Debug mode: %v", cfg.Debug)
	log.Printf("COM Backend: %v", cfg.UseComBackend)

	// Graceful shutdown
	go func() {
		if err := router.Run(addr); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Server failed to start: %v", err)
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down server...")
	log.Println("Server stopped")
}

func setupRoutes(router *gin.Engine, cfg *config.Config) {
	// Health check
	router.GET("/health", handlers.HealthCheck)
	router.GET("/", handlers.Root)

	// API routes
	api := router.Group("/api")
	{
		// AI endpoints
		ai := api.Group("/ai")
		{
			ai.POST("/classify", handlers.ClassifyEmail)
			ai.POST("/action-items", handlers.ExtractActionItems)
			ai.POST("/summarize", handlers.SummarizeEmail)
			ai.GET("/templates", handlers.GetAvailableTemplates)
			ai.GET("/health", handlers.AIHealthCheck)
			ai.POST("/classify-batch-stream", handlers.ClassifyBatchStream)
		}

		// Email endpoints
		emails := api.Group("/emails")
		{
			emails.GET("", handlers.GetEmails) // Deprecated: Use /outlook or /database
			emails.GET("/outlook", handlers.GetOutlookEmails)  // New: Get emails from live Outlook
			emails.GET("/database", handlers.GetDatabaseEmails) // New: Get emails from database
			emails.GET("/search", handlers.SearchEmails)
			emails.GET("/stats", handlers.GetEmailStats)
			emails.GET("/category-mappings", handlers.GetCategoryMappings)
			emails.GET("/accuracy-stats", handlers.GetAccuracyStats)
			emails.POST("/prefetch", handlers.PrefetchEmails)
			emails.POST("/bulk-apply-to-outlook", handlers.BulkApplyToOutlook)
			emails.POST("/batch-process", handlers.BatchProcessEmails)
			emails.POST("/extract-tasks", handlers.ExtractTasks)
			emails.POST("/sync-to-database", handlers.SyncToDatabase)
			emails.POST("/analyze-holistically", handlers.AnalyzeHolistically)
			
			emails.GET("/:id", handlers.GetEmail)
			emails.PUT("/:id/read", handlers.UpdateEmailReadStatus)
			emails.POST("/:id/mark-read", handlers.MarkEmailAsRead)
			emails.POST("/:id/move", handlers.MoveEmail)
			emails.PUT("/:id/classification", handlers.UpdateEmailClassification)
		}

		// Folder and conversation endpoints
		api.GET("/folders", handlers.GetFolders)
		api.GET("/conversations/:id", handlers.GetConversationThread)

		// Task endpoints
		tasks := api.Group("/tasks")
		{
			tasks.GET("", handlers.GetTasks)
			tasks.POST("", handlers.CreateTask)
			tasks.GET("/stats", handlers.GetTaskStats)
			tasks.POST("/bulk-update", handlers.BulkUpdateTasks)
			tasks.POST("/bulk-delete", handlers.BulkDeleteTasks)
			tasks.POST("/deduplicate/fyi", handlers.DeduplicateFYITasks)
			tasks.POST("/deduplicate/newsletters", handlers.DeduplicateNewsletterTasks)
			
			tasks.GET("/:id", handlers.GetTask)
			tasks.PUT("/:id", handlers.UpdateTask)
			tasks.DELETE("/:id", handlers.DeleteTask)
			tasks.PUT("/:id/status", handlers.UpdateTaskStatus)
			tasks.POST("/:id/link-email", handlers.LinkEmailToTask)
		}

		// Settings endpoints
		settings := api.Group("/settings")
		{
			settings.GET("", handlers.GetSettings)
			settings.PUT("", handlers.UpdateSettings)
			settings.DELETE("", handlers.ResetSettings)
		}

		// Processing endpoints
		processing := api.Group("/processing")
		{
			processing.POST("/start", handlers.StartProcessing)
			processing.GET("/stats", handlers.GetProcessingStats)
			processing.GET("/:id/status", handlers.GetProcessingStatus)
			processing.GET("/:id/jobs", handlers.GetPipelineJobs)
			processing.POST("/:id/cancel", handlers.CancelProcessing)
			
			// WebSocket endpoints
			processing.GET("/ws/:id", handlers.WebSocketPipeline)
			processing.GET("/ws", handlers.WebSocketGeneral)
		}
	}
}
