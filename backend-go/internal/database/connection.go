package database

import (
	"database/sql"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"sync"

	_ "modernc.org/sqlite"
)

var (
	db   *sql.DB
	once sync.Once
	mu   sync.RWMutex
)

// ResetForTesting resets the database connection for testing purposes
// This should only be called from test code
func ResetForTesting() {
	mu.Lock()
	defer mu.Unlock()
	if db != nil {
		db.Close()
	}
	db = nil
	once = sync.Once{}
}

// InitDB initializes the database connection and schema
func InitDB(dbPath string) error {
	var initErr error

	once.Do(func() {
		// Ensure directory exists
		dbDir := filepath.Dir(dbPath)
		if err := os.MkdirAll(dbDir, 0755); err != nil {
			initErr = fmt.Errorf("failed to create database directory: %w", err)
			return
		}

		// Open database connection
		var err error
		db, err = sql.Open("sqlite", dbPath)
		if err != nil {
			initErr = fmt.Errorf("failed to open database: %w", err)
			return
		}

		// Set connection pool settings
		db.SetMaxOpenConns(1) // SQLite only supports one writer
		db.SetMaxIdleConns(1)

		// Test connection
		if err := db.Ping(); err != nil {
			initErr = fmt.Errorf("failed to ping database: %w", err)
			return
		}

		// Initialize schema
		if err := initializeSchema(); err != nil {
			initErr = fmt.Errorf("failed to initialize schema: %w", err)
			return
		}

		log.Printf("Database initialized successfully: %s", dbPath)
	})

	return initErr
}

// GetDB returns the database connection
func GetDB() (*sql.DB, error) {
	if db == nil {
		return nil, fmt.Errorf("database not initialized")
	}
	return db, nil
}

// Close closes the database connection
func Close() error {
	if db != nil {
		return db.Close()
	}
	return nil
}

// initializeSchema creates all necessary tables and indexes
func initializeSchema() error {
	// Begin transaction
	tx, err := db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// Create emails table
	_, err = tx.Exec(`
		CREATE TABLE IF NOT EXISTS emails (
			id TEXT PRIMARY KEY,
			user_id INTEGER DEFAULT 1,
			subject TEXT,
			sender TEXT,
			recipient TEXT,
			content TEXT,
			body TEXT,
			date TIMESTAMP,
			received_date TIMESTAMP,
			category TEXT,
			ai_category TEXT,
			confidence REAL,
			ai_confidence REAL,
			ai_reasoning TEXT,
			one_line_summary TEXT,
			conversation_id TEXT,
			processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)
	`)
	if err != nil {
		return fmt.Errorf("failed to create emails table: %w", err)
	}

	// Create indexes for emails
	indexes := []string{
		"CREATE INDEX IF NOT EXISTS idx_emails_user_id ON emails(user_id)",
		"CREATE INDEX IF NOT EXISTS idx_emails_ai_category ON emails(ai_category)",
		"CREATE INDEX IF NOT EXISTS idx_emails_date ON emails(date DESC)",
		"CREATE INDEX IF NOT EXISTS idx_emails_conversation_id ON emails(conversation_id)",
	}

	for _, idx := range indexes {
		if _, err := tx.Exec(idx); err != nil {
			return fmt.Errorf("failed to create index: %w", err)
		}
	}

	// Create tasks table
	_, err = tx.Exec(`
		CREATE TABLE IF NOT EXISTS tasks (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			user_id INTEGER DEFAULT 1,
			title TEXT NOT NULL,
			description TEXT,
			status TEXT DEFAULT 'pending',
			priority TEXT DEFAULT 'medium',
			category TEXT,
			email_id TEXT,
			one_line_summary TEXT,
			due_date TIMESTAMP,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			completed_at TIMESTAMP,
			FOREIGN KEY (email_id) REFERENCES emails(id)
		)
	`)
	if err != nil {
		return fmt.Errorf("failed to create tasks table: %w", err)
	}

	// Create indexes for tasks
	taskIndexes := []string{
		"CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)",
		"CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
		"CREATE INDEX IF NOT EXISTS idx_tasks_email_id ON tasks(email_id)",
		"CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks(category)",
	}

	for _, idx := range taskIndexes {
		if _, err := tx.Exec(idx); err != nil {
			return fmt.Errorf("failed to create task index: %w", err)
		}
	}

	// Create user_settings table
	_, err = tx.Exec(`
		CREATE TABLE IF NOT EXISTS user_settings (
			user_id INTEGER PRIMARY KEY DEFAULT 1,
			username TEXT,
			job_context TEXT,
			newsletter_interests TEXT,
			azure_openai_endpoint TEXT,
			azure_openai_deployment TEXT,
			custom_prompts TEXT,
			ado_area_path TEXT,
			ado_pat TEXT,
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)
	`)
	if err != nil {
		return fmt.Errorf("failed to create user_settings table: %w", err)
	}

	// Insert default user settings if not exists
	_, err = tx.Exec("INSERT OR IGNORE INTO user_settings (user_id) VALUES (1)")
	if err != nil {
		return fmt.Errorf("failed to insert default user settings: %w", err)
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit schema: %w", err)
	}

	return nil
}
