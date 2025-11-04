package config

import (
	"log"
	"os"
	"path/filepath"
	"strconv"

	"github.com/joho/godotenv"
)

// Config holds all application configuration
type Config struct {
	// Server settings
	Port  int
	Host  string
	Debug bool

	// Database
	DatabasePath string

	// Azure OpenAI
	AzureOpenAIEndpoint    string
	AzureOpenAIAPIKey      string
	AzureOpenAIDeployment  string
	AzureOpenAIAPIVersion  string

	// Email Provider
	UseComBackend   bool
	EmailProvider   string
	ComTimeout      int
	ComRetryAttempts int

	// Security
	SecretKey                  string
	RequireAuthentication      bool
	AccessTokenExpireMinutes   int
	RefreshTokenExpireDays     int

	// Processing
	EmailProcessingLimit int
}

var config *Config

// Load loads configuration from environment variables and .env file
func Load() *Config {
	// Try to load .env file (optional)
	_ = godotenv.Load()

	config = &Config{
		// Server
		Port:  getEnvAsInt("PORT", 8000),
		Host:  getEnv("HOST", "0.0.0.0"),
		Debug: getEnvAsBool("DEBUG", false),

		// Database
		DatabasePath: getEnv("DATABASE_PATH", getDefaultDatabasePath()),

		// Azure OpenAI - API Key is optional, uses DefaultAzureCredential (az login) if not set
		AzureOpenAIEndpoint:   getEnv("AZURE_OPENAI_ENDPOINT", ""),
		AzureOpenAIAPIKey:     getEnv("AZURE_OPENAI_API_KEY", ""), // Empty string = use az login
		AzureOpenAIDeployment: getEnv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
		AzureOpenAIAPIVersion: getEnv("AZURE_OPENAI_API_VERSION", "2024-02-01"),

		// Email Provider
		UseComBackend:    getEnvAsBool("USE_COM_BACKEND", true),
		EmailProvider:    getEnv("EMAIL_PROVIDER", "outlook"),
		ComTimeout:       getEnvAsInt("COM_CONNECTION_TIMEOUT", 30),
		ComRetryAttempts: getEnvAsInt("COM_RETRY_ATTEMPTS", 3),

		// Security
		SecretKey:                getEnv("SECRET_KEY", "your-secret-key-change-in-production"),
		RequireAuthentication:    getEnvAsBool("REQUIRE_AUTHENTICATION", false),
		AccessTokenExpireMinutes: getEnvAsInt("ACCESS_TOKEN_EXPIRE_MINUTES", 30),
		RefreshTokenExpireDays:   getEnvAsInt("REFRESH_TOKEN_EXPIRE_DAYS", 30),

		// Processing
		EmailProcessingLimit: getEnvAsInt("EMAIL_PROCESSING_LIMIT", 100),
	}

	return config
}

// Get returns the loaded configuration
func Get() *Config {
	if config == nil {
		return Load()
	}
	return config
}

// Helper functions
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvAsInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
		log.Printf("Warning: Invalid integer value for %s: %s, using default %d", key, value, defaultValue)
	}
	return defaultValue
}

func getEnvAsBool(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		if boolValue, err := strconv.ParseBool(value); err == nil {
			return boolValue
		}
		log.Printf("Warning: Invalid boolean value for %s: %s, using default %v", key, value, defaultValue)
	}
	return defaultValue
}

func getDefaultDatabasePath() string {
	// Get the directory where the executable is located
	execPath, err := os.Executable()
	if err != nil {
		execPath, _ = os.Getwd()
	}
	execDir := filepath.Dir(execPath)

	// Navigate to runtime_data/database relative to project root
	dbPath := filepath.Join(execDir, "..", "runtime_data", "database", "email_helper_history.db")

	// Ensure directory exists
	dbDir := filepath.Dir(dbPath)
	if err := os.MkdirAll(dbDir, 0755); err != nil {
		log.Printf("Warning: Failed to create database directory: %v", err)
	}

	return dbPath
}
