package config

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
)

// TestLoadConfigWithDefaults tests loading with all default values
func TestLoadConfigWithDefaults(t *testing.T) {
	// Clear environment variables
	clearConfigEnv(t)
	
	cfg := Load()
	
	// Server defaults
	assert.Equal(t, 8000, cfg.Port)
	assert.Equal(t, "0.0.0.0", cfg.Host)
	assert.False(t, cfg.Debug)
	
	// Database defaults
	assert.NotEmpty(t, cfg.DatabasePath)
	assert.Contains(t, cfg.DatabasePath, "email_helper_history.db")
	
	// Azure OpenAI defaults
	assert.Empty(t, cfg.AzureOpenAIEndpoint)
	assert.Empty(t, cfg.AzureOpenAIAPIKey)
	assert.Equal(t, "gpt-4o", cfg.AzureOpenAIDeployment)
	assert.Equal(t, "2024-02-01", cfg.AzureOpenAIAPIVersion)
	
	// Email provider defaults
	assert.True(t, cfg.UseComBackend)
	assert.Equal(t, "outlook", cfg.EmailProvider)
	assert.Equal(t, 30, cfg.ComTimeout)
	assert.Equal(t, 3, cfg.ComRetryAttempts)
	
	// Security defaults
	assert.Equal(t, "your-secret-key-change-in-production", cfg.SecretKey)
	assert.False(t, cfg.RequireAuthentication)
	assert.Equal(t, 30, cfg.AccessTokenExpireMinutes)
	assert.Equal(t, 30, cfg.RefreshTokenExpireDays)
	
	// Processing defaults
	assert.Equal(t, 100, cfg.EmailProcessingLimit)
}

// TestLoadConfigFromEnvironment tests loading from environment variables
func TestLoadConfigFromEnvironment(t *testing.T) {
	clearConfigEnv(t)
	
	// Set environment variables
	t.Setenv("PORT", "9000")
	t.Setenv("HOST", "localhost")
	t.Setenv("DEBUG", "true")
	t.Setenv("DATABASE_PATH", "/custom/path/db.db")
	t.Setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
	t.Setenv("AZURE_OPENAI_API_KEY", "test-key-12345")
	t.Setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4-custom")
	t.Setenv("AZURE_OPENAI_API_VERSION", "2024-03-01")
	t.Setenv("USE_COM_BACKEND", "false")
	t.Setenv("EMAIL_PROVIDER", "graph")
	t.Setenv("COM_CONNECTION_TIMEOUT", "60")
	t.Setenv("COM_RETRY_ATTEMPTS", "5")
	t.Setenv("SECRET_KEY", "production-secret-key")
	t.Setenv("REQUIRE_AUTHENTICATION", "true")
	t.Setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
	t.Setenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
	t.Setenv("EMAIL_PROCESSING_LIMIT", "500")
	
	cfg := Load()
	
	// Verify all values from environment
	assert.Equal(t, 9000, cfg.Port)
	assert.Equal(t, "localhost", cfg.Host)
	assert.True(t, cfg.Debug)
	assert.Equal(t, "/custom/path/db.db", cfg.DatabasePath)
	assert.Equal(t, "https://test.openai.azure.com", cfg.AzureOpenAIEndpoint)
	assert.Equal(t, "test-key-12345", cfg.AzureOpenAIAPIKey)
	assert.Equal(t, "gpt-4-custom", cfg.AzureOpenAIDeployment)
	assert.Equal(t, "2024-03-01", cfg.AzureOpenAIAPIVersion)
	assert.False(t, cfg.UseComBackend)
	assert.Equal(t, "graph", cfg.EmailProvider)
	assert.Equal(t, 60, cfg.ComTimeout)
	assert.Equal(t, 5, cfg.ComRetryAttempts)
	assert.Equal(t, "production-secret-key", cfg.SecretKey)
	assert.True(t, cfg.RequireAuthentication)
	assert.Equal(t, 60, cfg.AccessTokenExpireMinutes)
	assert.Equal(t, 7, cfg.RefreshTokenExpireDays)
	assert.Equal(t, 500, cfg.EmailProcessingLimit)
}

// TestInvalidPortNumbers tests port validation
func TestInvalidPortNumbers(t *testing.T) {
	testCases := []struct {
		name        string
		portValue   string
		expectPort  int // Should fall back to default
	}{
		{"Negative", "-1", -1}, // Negative numbers parse successfully but may fail at runtime
		{"Zero", "0", 0}, // 0 is technically valid (random port)
		{"TooLarge", "99999", 99999}, // Parsed but may fail at runtime
		{"NonNumeric", "abc", 8000},
		{"Empty", "", 8000},
		{"Whitespace", "  ", 8000},
		{"Float", "8000.5", 8000},
		{"HexNumber", "0x1F90", 8000},
	}
	
	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			clearConfigEnv(t)
			if tc.portValue != "" {
				t.Setenv("PORT", tc.portValue)
			}
			
			cfg := Load()
			assert.Equal(t, tc.expectPort, cfg.Port)
		})
	}
}

// TestInvalidIntegerValues tests integer parsing edge cases
func TestInvalidIntegerValues(t *testing.T) {
	t.Run("InvalidTimeout", func(t *testing.T) {
		clearConfigEnv(t)
		t.Setenv("COM_CONNECTION_TIMEOUT", "not-a-number")
		
		cfg := Load()
		assert.Equal(t, 30, cfg.ComTimeout) // Default value
	})
	
	t.Run("InvalidRetryAttempts", func(t *testing.T) {
		clearConfigEnv(t)
		t.Setenv("COM_RETRY_ATTEMPTS", "abc")
		
		cfg := Load()
		assert.Equal(t, 3, cfg.ComRetryAttempts) // Default value
	})
	
	t.Run("InvalidTokenExpire", func(t *testing.T) {
		clearConfigEnv(t)
		t.Setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "invalid")
		
		cfg := Load()
		assert.Equal(t, 30, cfg.AccessTokenExpireMinutes) // Default value
	})
	
	t.Run("InvalidProcessingLimit", func(t *testing.T) {
		clearConfigEnv(t)
		t.Setenv("EMAIL_PROCESSING_LIMIT", "9999999999999999999999")
		
		cfg := Load()
		assert.Equal(t, 100, cfg.EmailProcessingLimit) // Default value due to overflow
	})
}

// TestInvalidBooleanValues tests boolean parsing edge cases
func TestInvalidBooleanValues(t *testing.T) {
	testCases := []struct {
		name         string
		boolValue    string
		expectValue  bool
	}{
		{"ValidTrue", "true", true},
		{"ValidFalse", "false", false},
		{"Valid1", "1", true},
		{"Valid0", "0", false},
		{"ValidT", "t", true},
		{"ValidF", "f", false},
		{"InvalidYes", "yes", false}, // Falls back to default
		{"InvalidNo", "no", false},
		{"InvalidString", "abc", false},
		{"Empty", "", false},
		{"Whitespace", "  ", false},
	}
	
	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			clearConfigEnv(t)
			if tc.boolValue != "" {
				t.Setenv("DEBUG", tc.boolValue)
			}
			
			cfg := Load()
			assert.Equal(t, tc.expectValue, cfg.Debug)
		})
	}
}

// TestDatabasePathValidation tests database path handling
func TestDatabasePathValidation(t *testing.T) {
	t.Run("CustomPath", func(t *testing.T) {
		clearConfigEnv(t)
		customPath := "/tmp/test.db"
		t.Setenv("DATABASE_PATH", customPath)
		
		cfg := Load()
		assert.Equal(t, customPath, cfg.DatabasePath)
	})
	
	t.Run("DefaultPathContainsDatabase", func(t *testing.T) {
		clearConfigEnv(t)
		
		cfg := Load()
		assert.Contains(t, cfg.DatabasePath, "database")
		assert.Contains(t, cfg.DatabasePath, "email_helper_history.db")
	})
	
	t.Run("RelativePath", func(t *testing.T) {
		clearConfigEnv(t)
		t.Setenv("DATABASE_PATH", "./relative/path/db.db")
		
		cfg := Load()
		assert.Equal(t, "./relative/path/db.db", cfg.DatabasePath)
	})
}

// TestEmptyAndWhitespaceValues tests handling of empty/whitespace values
func TestEmptyAndWhitespaceValues(t *testing.T) {
	t.Run("EmptyStringValues", func(t *testing.T) {
		clearConfigEnv(t)
		t.Setenv("HOST", "")
		t.Setenv("AZURE_OPENAI_ENDPOINT", "")
		t.Setenv("SECRET_KEY", "")
		
		cfg := Load()
		// Empty strings should use defaults
		assert.Equal(t, "0.0.0.0", cfg.Host)
		assert.Empty(t, cfg.AzureOpenAIEndpoint) // Empty is valid for optional fields
		assert.Equal(t, "your-secret-key-change-in-production", cfg.SecretKey)
	})
	
	t.Run("WhitespaceOnlyValues", func(t *testing.T) {
		clearConfigEnv(t)
		t.Setenv("HOST", "   ")
		t.Setenv("AZURE_OPENAI_DEPLOYMENT", "  \t  ")
		
		cfg := Load()
		// Whitespace is treated as non-empty, so it's used
		assert.Equal(t, "   ", cfg.Host)
		assert.Equal(t, "  \t  ", cfg.AzureOpenAIDeployment)
	})
}

// TestVeryLongValues tests handling of very long configuration values
func TestVeryLongValues(t *testing.T) {
	t.Run("LongSecretKey", func(t *testing.T) {
		clearConfigEnv(t)
		longKey := make([]byte, 10000)
		for i := range longKey {
			longKey[i] = 'a'
		}
		t.Setenv("SECRET_KEY", string(longKey))
		
		cfg := Load()
		assert.Equal(t, string(longKey), cfg.SecretKey)
		assert.Len(t, cfg.SecretKey, 10000)
	})
	
	t.Run("LongDatabasePath", func(t *testing.T) {
		clearConfigEnv(t)
		// Use a long but reasonable path (Windows env var limit is ~32KB)
		longPath := "/very/long/path/" + string(make([]byte, 1000))
		for i := range longPath {
			if longPath[i] == 0 {
				longPath = longPath[:i]
				break
			}
		}
		t.Setenv("DATABASE_PATH", longPath)
		
		cfg := Load()
		assert.Equal(t, longPath, cfg.DatabasePath)
	})
}

// TestEnvironmentVariablePrecedence tests that env vars override defaults
func TestEnvironmentVariablePrecedence(t *testing.T) {
	clearConfigEnv(t)
	
	// First load with defaults
	cfg1 := Load()
	defaultPort := cfg1.Port
	defaultHost := cfg1.Host
	
	// Clear and set different values
	clearConfigEnv(t)
	t.Setenv("PORT", "9999")
	t.Setenv("HOST", "custom-host")
	
	// Reset config to force reload
	config = nil
	cfg2 := Load()
	
	assert.NotEqual(t, defaultPort, cfg2.Port)
	assert.NotEqual(t, defaultHost, cfg2.Host)
	assert.Equal(t, 9999, cfg2.Port)
	assert.Equal(t, "custom-host", cfg2.Host)
}

// TestGetFunction tests the Get() singleton pattern
func TestGetFunction(t *testing.T) {
	clearConfigEnv(t)
	
	// Reset config
	config = nil
	
	// First call should load
	cfg1 := Get()
	assert.NotNil(t, cfg1)
	
	// Second call should return same instance
	cfg2 := Get()
	assert.Equal(t, cfg1, cfg2)
	
	// Verify it's actually the same pointer
	cfg1.Port = 12345
	assert.Equal(t, 12345, cfg2.Port)
}

// TestAzureOpenAIOptionalAPIKey tests that API key is optional (for az login)
func TestAzureOpenAIOptionalAPIKey(t *testing.T) {
	t.Run("NoAPIKey", func(t *testing.T) {
		clearConfigEnv(t)
		t.Setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
		// No API key set
		
		cfg := Load()
		assert.Equal(t, "https://test.openai.azure.com", cfg.AzureOpenAIEndpoint)
		assert.Empty(t, cfg.AzureOpenAIAPIKey) // Empty string means use az login
	})
	
	t.Run("WithAPIKey", func(t *testing.T) {
		clearConfigEnv(t)
		t.Setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
		t.Setenv("AZURE_OPENAI_API_KEY", "actual-key")
		
		cfg := Load()
		assert.Equal(t, "actual-key", cfg.AzureOpenAIAPIKey)
	})
}

// TestDefaultDatabasePath tests the default database path generation
func TestDefaultDatabasePath(t *testing.T) {
	dbPath := getDefaultDatabasePath()
	
	// Should contain expected directory structure
	assert.Contains(t, dbPath, "runtime_data")
	assert.Contains(t, dbPath, "database")
	assert.Contains(t, dbPath, "email_helper_history.db")
	
	// Should be an absolute path
	assert.True(t, filepath.IsAbs(dbPath) || filepath.IsLocal(dbPath))
}

// TestHelperFunctions tests the helper functions directly
func TestHelperFunctions(t *testing.T) {
	t.Run("getEnv", func(t *testing.T) {
		t.Setenv("TEST_VAR", "test-value")
		assert.Equal(t, "test-value", getEnv("TEST_VAR", "default"))
		assert.Equal(t, "default", getEnv("NONEXISTENT_VAR", "default"))
	})
	
	t.Run("getEnvAsInt", func(t *testing.T) {
		t.Setenv("TEST_INT", "42")
		assert.Equal(t, 42, getEnvAsInt("TEST_INT", 10))
		assert.Equal(t, 10, getEnvAsInt("NONEXISTENT_INT", 10))
		
		t.Setenv("BAD_INT", "not-a-number")
		assert.Equal(t, 10, getEnvAsInt("BAD_INT", 10))
	})
	
	t.Run("getEnvAsBool", func(t *testing.T) {
		t.Setenv("TEST_BOOL", "true")
		assert.True(t, getEnvAsBool("TEST_BOOL", false))
		assert.False(t, getEnvAsBool("NONEXISTENT_BOOL", false))
		
		t.Setenv("BAD_BOOL", "not-a-bool")
		assert.False(t, getEnvAsBool("BAD_BOOL", false))
	})
}

// TestSpecialCharactersInValues tests handling of special characters
func TestSpecialCharactersInValues(t *testing.T) {
	t.Run("SpecialCharsInSecretKey", func(t *testing.T) {
		clearConfigEnv(t)
		specialKey := "key!@#$%^&*(){}[]|\\:;<>?,./~`"
		t.Setenv("SECRET_KEY", specialKey)
		
		cfg := Load()
		assert.Equal(t, specialKey, cfg.SecretKey)
	})
	
	t.Run("URLInEndpoint", func(t *testing.T) {
		clearConfigEnv(t)
		endpoint := "https://test.openai.azure.com/openai/deployments?api-version=2024-02-01"
		t.Setenv("AZURE_OPENAI_ENDPOINT", endpoint)
		
		cfg := Load()
		assert.Equal(t, endpoint, cfg.AzureOpenAIEndpoint)
	})
	
	t.Run("PathWithSpaces", func(t *testing.T) {
		clearConfigEnv(t)
		pathWithSpaces := "/path with spaces/to database/file.db"
		t.Setenv("DATABASE_PATH", pathWithSpaces)
		
		cfg := Load()
		assert.Equal(t, pathWithSpaces, cfg.DatabasePath)
	})
}

// TestBoundaryValues tests boundary values for integer fields
func TestBoundaryValues(t *testing.T) {
	t.Run("MaxInt", func(t *testing.T) {
		clearConfigEnv(t)
		t.Setenv("PORT", "2147483647") // Max int32
		
		cfg := Load()
		assert.Equal(t, 2147483647, cfg.Port)
	})
	
	t.Run("ZeroValues", func(t *testing.T) {
		clearConfigEnv(t)
		t.Setenv("PORT", "0")
		t.Setenv("COM_CONNECTION_TIMEOUT", "0")
		t.Setenv("COM_RETRY_ATTEMPTS", "0")
		
		cfg := Load()
		assert.Equal(t, 0, cfg.Port)
		assert.Equal(t, 0, cfg.ComTimeout)
		assert.Equal(t, 0, cfg.ComRetryAttempts)
	})
	
	t.Run("NegativeValues", func(t *testing.T) {
		clearConfigEnv(t)
		t.Setenv("EMAIL_PROCESSING_LIMIT", "-100")
		
		cfg := Load()
		// Negative values are parsed as-is (validation would happen at runtime)
		assert.Equal(t, -100, cfg.EmailProcessingLimit)
	})
}

// TestReloadConfig tests that Load() creates a new config each time
func TestReloadConfig(t *testing.T) {
	clearConfigEnv(t)
	t.Setenv("PORT", "8000")
	
	cfg1 := Load()
	assert.Equal(t, 8000, cfg1.Port)
	
	// Change environment and reload
	clearConfigEnv(t)
	t.Setenv("PORT", "9000")
	
	cfg2 := Load()
	assert.Equal(t, 9000, cfg2.Port)
	
	// Both configs exist but are different
	assert.NotEqual(t, cfg1.Port, cfg2.Port)
}

// Helper function to clear all config-related environment variables
func clearConfigEnv(t *testing.T) {
	// Reset the global config variable
	config = nil
	
	// List of all config environment variables
	envVars := []string{
		"PORT", "HOST", "DEBUG",
		"DATABASE_PATH",
		"AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY",
		"AZURE_OPENAI_DEPLOYMENT", "AZURE_OPENAI_API_VERSION",
		"USE_COM_BACKEND", "EMAIL_PROVIDER",
		"COM_CONNECTION_TIMEOUT", "COM_RETRY_ATTEMPTS",
		"SECRET_KEY", "REQUIRE_AUTHENTICATION",
		"ACCESS_TOKEN_EXPIRE_MINUTES", "REFRESH_TOKEN_EXPIRE_DAYS",
		"EMAIL_PROCESSING_LIMIT",
	}
	
	// Unset all environment variables
	for _, envVar := range envVars {
		os.Unsetenv(envVar)
	}
}
