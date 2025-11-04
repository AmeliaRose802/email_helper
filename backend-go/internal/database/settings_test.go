package database

import (
	"encoding/json"
	"sync"
	"testing"

	"email-helper-backend/internal/models"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// setupSettingsTestDB initializes an in-memory SQLite database for settings tests
func setupSettingsTestDB(t *testing.T) {
	// Reset the singleton for testing
	db = nil
	once = sync.Once{}

	// Initialize with in-memory database
	err := InitDB(":memory:")
	require.NoError(t, err, "Failed to initialize test database")
}

// teardownSettingsTestDB closes the test database
func teardownSettingsTestDB(t *testing.T) {
	if db != nil {
		err := db.Close()
		assert.NoError(t, err, "Failed to close test database")
		db = nil
		once = sync.Once{}
	}
}

// createTestSettings creates a sample settings object for testing
func createTestSettings() *models.UserSettings {
	username := "testuser"
	jobContext := "Software Engineer at Tech Corp"
	newsletterInterests := "AI, Cloud, DevOps"
	azureEndpoint := "https://test.openai.azure.com"
	azureDeployment := "gpt-4"
	adoAreaPath := "Project\\Team\\Area"
	adoPat := "test-pat-token"

	return &models.UserSettings{
		Username:              &username,
		JobContext:            &jobContext,
		NewsletterInterests:   &newsletterInterests,
		AzureOpenAIEndpoint:   &azureEndpoint,
		AzureOpenAIDeployment: &azureDeployment,
		CustomPrompts: map[string]string{
			"classification": "Custom classification prompt",
			"summary":        "Custom summary prompt",
		},
		ADOAreaPath: &adoAreaPath,
		ADOPAT:      &adoPat,
	}
}

func TestGetSettings(t *testing.T) {
	setupSettingsTestDB(t)
	defer teardownSettingsTestDB(t)

	t.Run("GetEmptySettings", func(t *testing.T) {
		// Reset settings to ensure they're empty
		err := ResetSettings()
		require.NoError(t, err)

		settings, err := GetSettings()
		require.NoError(t, err)
		assert.NotNil(t, settings)

		// All fields should be nil/empty for default settings
		assert.Nil(t, settings.Username)
		assert.Nil(t, settings.JobContext)
		assert.Nil(t, settings.NewsletterInterests)
		assert.Nil(t, settings.AzureOpenAIEndpoint)
		assert.Nil(t, settings.AzureOpenAIDeployment)
		assert.Nil(t, settings.ADOAreaPath)
		assert.Nil(t, settings.ADOPAT)
		assert.Nil(t, settings.CustomPrompts)
	})

	t.Run("GetPopulatedSettings", func(t *testing.T) {
		// First update settings
		testSettings := createTestSettings()
		err := UpdateSettings(testSettings)
		require.NoError(t, err)

		// Retrieve and verify
		settings, err := GetSettings()
		require.NoError(t, err)
		assert.NotNil(t, settings)

		assert.Equal(t, *testSettings.Username, *settings.Username)
		assert.Equal(t, *testSettings.JobContext, *settings.JobContext)
		assert.Equal(t, *testSettings.NewsletterInterests, *settings.NewsletterInterests)
		assert.Equal(t, *testSettings.AzureOpenAIEndpoint, *settings.AzureOpenAIEndpoint)
		assert.Equal(t, *testSettings.AzureOpenAIDeployment, *settings.AzureOpenAIDeployment)
		assert.Equal(t, *testSettings.ADOAreaPath, *settings.ADOAreaPath)
		assert.Equal(t, *testSettings.ADOPAT, *settings.ADOPAT)
		assert.Equal(t, testSettings.CustomPrompts, settings.CustomPrompts)
	})

	t.Run("GetSettingsWithNullCustomPrompts", func(t *testing.T) {
		// Reset and set only basic fields
		err := ResetSettings()
		require.NoError(t, err)

		username := "testuser"
		settings := &models.UserSettings{
			Username: &username,
		}
		err = UpdateSettings(settings)
		require.NoError(t, err)

		// Retrieve and verify custom_prompts is nil/empty
		retrieved, err := GetSettings()
		require.NoError(t, err)
		assert.Nil(t, retrieved.CustomPrompts)
	})

	t.Run("GetSettingsWithInvalidJSON", func(t *testing.T) {
		// Reset settings
		err := ResetSettings()
		require.NoError(t, err)

		// Manually insert invalid JSON into custom_prompts
		testDB, err := GetDB()
		require.NoError(t, err)

		_, err = testDB.Exec("UPDATE user_settings SET custom_prompts = ? WHERE user_id = 1", "{invalid json")
		require.NoError(t, err)

		// Should handle gracefully by not setting CustomPrompts
		settings, err := GetSettings()
		require.NoError(t, err)
		assert.NotNil(t, settings)
		assert.Nil(t, settings.CustomPrompts) // Invalid JSON should result in nil map
	})

	t.Run("GetSettingsWithEmptyJSONString", func(t *testing.T) {
		// Reset settings
		err := ResetSettings()
		require.NoError(t, err)

		// Manually insert empty string into custom_prompts
		testDB, err := GetDB()
		require.NoError(t, err)

		_, err = testDB.Exec("UPDATE user_settings SET custom_prompts = ? WHERE user_id = 1", "")
		require.NoError(t, err)

		// Should handle empty string gracefully
		settings, err := GetSettings()
		require.NoError(t, err)
		assert.NotNil(t, settings)
		assert.Nil(t, settings.CustomPrompts)
	})

	t.Run("GetSettingsWithValidEmptyJSON", func(t *testing.T) {
		// Reset settings
		err := ResetSettings()
		require.NoError(t, err)

		// Set empty JSON object
		settings := &models.UserSettings{
			CustomPrompts: map[string]string{},
		}
		err = UpdateSettings(settings)
		require.NoError(t, err)

		// Should retrieve empty map
		retrieved, err := GetSettings()
		require.NoError(t, err)
		assert.NotNil(t, retrieved.CustomPrompts)
		assert.Len(t, retrieved.CustomPrompts, 0)
	})
}

func TestUpdateSettings(t *testing.T) {
	setupSettingsTestDB(t)
	defer teardownSettingsTestDB(t)

	t.Run("UpdateAllFields", func(t *testing.T) {
		settings := createTestSettings()
		err := UpdateSettings(settings)
		assert.NoError(t, err)

		// Verify all fields were updated
		retrieved, err := GetSettings()
		require.NoError(t, err)
		assert.Equal(t, *settings.Username, *retrieved.Username)
		assert.Equal(t, *settings.JobContext, *retrieved.JobContext)
		assert.Equal(t, *settings.NewsletterInterests, *retrieved.NewsletterInterests)
		assert.Equal(t, *settings.AzureOpenAIEndpoint, *retrieved.AzureOpenAIEndpoint)
		assert.Equal(t, *settings.AzureOpenAIDeployment, *retrieved.AzureOpenAIDeployment)
		assert.Equal(t, *settings.ADOAreaPath, *retrieved.ADOAreaPath)
		assert.Equal(t, *settings.ADOPAT, *retrieved.ADOPAT)
		assert.Equal(t, settings.CustomPrompts, retrieved.CustomPrompts)
	})

	t.Run("UpdatePartialFields", func(t *testing.T) {
		// First set all fields
		fullSettings := createTestSettings()
		err := UpdateSettings(fullSettings)
		require.NoError(t, err)

		// Update only username and job context
		newUsername := "updateduser"
		newJobContext := "Senior Engineer"
		partialSettings := &models.UserSettings{
			Username:   &newUsername,
			JobContext: &newJobContext,
		}
		err = UpdateSettings(partialSettings)
		assert.NoError(t, err)

		// Verify only specified fields were updated
		retrieved, err := GetSettings()
		require.NoError(t, err)
		assert.Equal(t, newUsername, *retrieved.Username)
		assert.Equal(t, newJobContext, *retrieved.JobContext)
		// Other fields should remain unchanged
		assert.Equal(t, *fullSettings.NewsletterInterests, *retrieved.NewsletterInterests)
		assert.Equal(t, *fullSettings.AzureOpenAIEndpoint, *retrieved.AzureOpenAIEndpoint)
	})

	t.Run("UpdateSingleField", func(t *testing.T) {
		// Reset first
		err := ResetSettings()
		require.NoError(t, err)

		// Update only username
		username := "singleuser"
		settings := &models.UserSettings{
			Username: &username,
		}
		err = UpdateSettings(settings)
		assert.NoError(t, err)

		retrieved, err := GetSettings()
		require.NoError(t, err)
		assert.Equal(t, username, *retrieved.Username)
		assert.Nil(t, retrieved.JobContext)
		assert.Nil(t, retrieved.NewsletterInterests)
	})

	t.Run("UpdateCustomPrompts", func(t *testing.T) {
		// Reset first
		err := ResetSettings()
		require.NoError(t, err)

		// Set custom prompts
		prompts := map[string]string{
			"test1": "prompt 1",
			"test2": "prompt 2",
		}
		settings := &models.UserSettings{
			CustomPrompts: prompts,
		}
		err = UpdateSettings(settings)
		assert.NoError(t, err)

		// Verify JSON marshaling and storage
		retrieved, err := GetSettings()
		require.NoError(t, err)
		assert.Equal(t, prompts, retrieved.CustomPrompts)
		assert.Equal(t, "prompt 1", retrieved.CustomPrompts["test1"])
		assert.Equal(t, "prompt 2", retrieved.CustomPrompts["test2"])
	})

	t.Run("UpdateToEmptyString", func(t *testing.T) {
		// Set initial value
		initial := "initial value"
		settings := &models.UserSettings{
			Username: &initial,
		}
		err := UpdateSettings(settings)
		require.NoError(t, err)

		// Update to empty string
		empty := ""
		settings = &models.UserSettings{
			Username: &empty,
		}
		err = UpdateSettings(settings)
		assert.NoError(t, err)

		// Verify it's actually empty string, not NULL
		retrieved, err := GetSettings()
		require.NoError(t, err)
		assert.NotNil(t, retrieved.Username)
		assert.Equal(t, "", *retrieved.Username)
	})

	t.Run("UpdateWithVeryLongStrings", func(t *testing.T) {
		// Test with very long field values
		longString := string(make([]byte, 10000))
		for i := range longString {
			longString = longString[:i] + "a" + longString[i+1:]
		}

		settings := &models.UserSettings{
			JobContext: &longString,
		}
		err := UpdateSettings(settings)
		assert.NoError(t, err)

		retrieved, err := GetSettings()
		require.NoError(t, err)
		assert.Equal(t, longString, *retrieved.JobContext)
	})

	t.Run("UpdateWithSpecialCharacters", func(t *testing.T) {
		// Test with special characters that might cause SQL issues
		specialChars := "'; DROP TABLE user_settings; --"
		settings := &models.UserSettings{
			Username: &specialChars,
		}
		err := UpdateSettings(settings)
		assert.NoError(t, err)

		// Verify parameterized queries prevent SQL injection
		retrieved, err := GetSettings()
		require.NoError(t, err)
		assert.Equal(t, specialChars, *retrieved.Username)

		// Verify table still exists
		testDB, _ := GetDB()
		var exists bool
		err = testDB.QueryRow("SELECT EXISTS(SELECT 1 FROM user_settings)").Scan(&exists)
		require.NoError(t, err)
		assert.True(t, exists)
	})

	t.Run("UpdateWithComplexJSON", func(t *testing.T) {
		// Test custom prompts with special characters and complex content
		prompts := map[string]string{
			"prompt1":           "Simple prompt",
			"prompt_with_json":  `{"nested": "json", "values": [1, 2, 3]}`,
			"prompt_with_quote": `He said "hello"`,
			"prompt_multiline":  "Line 1\nLine 2\nLine 3",
		}
		settings := &models.UserSettings{
			CustomPrompts: prompts,
		}
		err := UpdateSettings(settings)
		assert.NoError(t, err)

		retrieved, err := GetSettings()
		require.NoError(t, err)
		assert.Equal(t, prompts, retrieved.CustomPrompts)
	})

	t.Run("UpdateEmptySettings", func(t *testing.T) {
		// Update with empty settings object (no fields set)
		settings := &models.UserSettings{}
		err := UpdateSettings(settings)
		assert.NoError(t, err)

		// Should only update timestamp, no other changes
		retrieved, err := GetSettings()
		require.NoError(t, err)
		assert.NotNil(t, retrieved)
	})

	t.Run("UpdateCreatesRowIfNotExists", func(t *testing.T) {
		// Delete the settings row to test auto-creation
		testDB, err := GetDB()
		require.NoError(t, err)

		_, err = testDB.Exec("DELETE FROM user_settings WHERE user_id = 1")
		require.NoError(t, err)

		// Verify row doesn't exist
		var exists bool
		err = testDB.QueryRow("SELECT EXISTS(SELECT 1 FROM user_settings WHERE user_id = 1)").Scan(&exists)
		require.NoError(t, err)
		assert.False(t, exists)

		// Update should create the row
		username := "newuser"
		settings := &models.UserSettings{
			Username: &username,
		}
		err = UpdateSettings(settings)
		assert.NoError(t, err)

		// Verify row was created
		err = testDB.QueryRow("SELECT EXISTS(SELECT 1 FROM user_settings WHERE user_id = 1)").Scan(&exists)
		require.NoError(t, err)
		assert.True(t, exists)

		// Verify value was set
		retrieved, err := GetSettings()
		require.NoError(t, err)
		assert.Equal(t, username, *retrieved.Username)
	})
}

func TestResetSettings(t *testing.T) {
	setupSettingsTestDB(t)
	defer teardownSettingsTestDB(t)

	t.Run("ResetAllFields", func(t *testing.T) {
		// First populate settings
		settings := createTestSettings()
		err := UpdateSettings(settings)
		require.NoError(t, err)

		// Verify settings are populated
		retrieved, err := GetSettings()
		require.NoError(t, err)
		assert.NotNil(t, retrieved.Username)
		assert.NotNil(t, retrieved.JobContext)

		// Reset settings
		err = ResetSettings()
		assert.NoError(t, err)

		// Verify all fields are NULL/nil
		retrieved, err = GetSettings()
		require.NoError(t, err)
		assert.Nil(t, retrieved.Username)
		assert.Nil(t, retrieved.JobContext)
		assert.Nil(t, retrieved.NewsletterInterests)
		assert.Nil(t, retrieved.AzureOpenAIEndpoint)
		assert.Nil(t, retrieved.AzureOpenAIDeployment)
		assert.Nil(t, retrieved.ADOAreaPath)
		assert.Nil(t, retrieved.ADOPAT)
		assert.Nil(t, retrieved.CustomPrompts)
	})

	t.Run("ResetAlreadyEmptySettings", func(t *testing.T) {
		// Ensure settings are already empty
		err := ResetSettings()
		require.NoError(t, err)

		// Reset again
		err = ResetSettings()
		assert.NoError(t, err)

		// Verify still empty (no errors)
		retrieved, err := GetSettings()
		require.NoError(t, err)
		assert.Nil(t, retrieved.Username)
	})

	t.Run("ResetThenUpdate", func(t *testing.T) {
		// Reset
		err := ResetSettings()
		require.NoError(t, err)

		// Update after reset
		username := "afterreset"
		settings := &models.UserSettings{
			Username: &username,
		}
		err = UpdateSettings(settings)
		assert.NoError(t, err)

		// Verify update worked
		retrieved, err := GetSettings()
		require.NoError(t, err)
		assert.Equal(t, username, *retrieved.Username)
		assert.Nil(t, retrieved.JobContext) // Other fields still NULL
	})

	t.Run("ResetPreservesRowExistence", func(t *testing.T) {
		// Reset settings
		err := ResetSettings()
		require.NoError(t, err)

		// Verify row still exists (not deleted)
		testDB, err := GetDB()
		require.NoError(t, err)

		var exists bool
		err = testDB.QueryRow("SELECT EXISTS(SELECT 1 FROM user_settings WHERE user_id = 1)").Scan(&exists)
		require.NoError(t, err)
		assert.True(t, exists)
	})
}

func TestSettingsWithUninitializedDB(t *testing.T) {
	// Reset DB to nil to simulate uninitialized state
	db = nil
	once = sync.Once{}

	t.Run("GetSettingsWithoutInitialization", func(t *testing.T) {
		_, err := GetSettings()
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "database not initialized")
	})

	t.Run("UpdateSettingsWithoutInitialization", func(t *testing.T) {
		settings := createTestSettings()
		err := UpdateSettings(settings)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "database not initialized")
	})

	t.Run("ResetSettingsWithoutInitialization", func(t *testing.T) {
		err := ResetSettings()
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "database not initialized")
	})
}

func TestSettingsJSONMarshaling(t *testing.T) {
	setupSettingsTestDB(t)
	defer teardownSettingsTestDB(t)

	t.Run("MarshalCustomPrompts", func(t *testing.T) {
		prompts := map[string]string{
			"key1": "value1",
			"key2": "value2",
		}
		settings := &models.UserSettings{
			CustomPrompts: prompts,
		}

		err := UpdateSettings(settings)
		require.NoError(t, err)

		// Verify JSON was properly marshaled in database
		testDB, err := GetDB()
		require.NoError(t, err)

		var jsonStr string
		err = testDB.QueryRow("SELECT custom_prompts FROM user_settings WHERE user_id = 1").Scan(&jsonStr)
		require.NoError(t, err)

		// Verify it's valid JSON
		var unmarshaled map[string]string
		err = json.Unmarshal([]byte(jsonStr), &unmarshaled)
		assert.NoError(t, err)
		assert.Equal(t, prompts, unmarshaled)
	})

	t.Run("UnmarshalCustomPrompts", func(t *testing.T) {
		// Manually insert JSON
		testDB, err := GetDB()
		require.NoError(t, err)

		jsonStr := `{"test": "value", "another": "test"}`
		_, err = testDB.Exec("UPDATE user_settings SET custom_prompts = ? WHERE user_id = 1", jsonStr)
		require.NoError(t, err)

		// Retrieve and verify unmarshaling
		settings, err := GetSettings()
		require.NoError(t, err)
		assert.NotNil(t, settings.CustomPrompts)
		assert.Equal(t, "value", settings.CustomPrompts["test"])
		assert.Equal(t, "test", settings.CustomPrompts["another"])
	})

	t.Run("EmptyMapMarshalsCorrectly", func(t *testing.T) {
		settings := &models.UserSettings{
			CustomPrompts: map[string]string{},
		}

		err := UpdateSettings(settings)
		require.NoError(t, err)

		retrieved, err := GetSettings()
		require.NoError(t, err)
		assert.NotNil(t, retrieved.CustomPrompts)
		assert.Len(t, retrieved.CustomPrompts, 0)
	})
}

func TestSettingsConcurrency(t *testing.T) {
	setupSettingsTestDB(t)
	defer teardownSettingsTestDB(t)

	t.Run("ConcurrentUpdates", func(t *testing.T) {
		// Test concurrent updates don't corrupt data
		done := make(chan bool)

		for i := 0; i < 5; i++ {
			go func(id int) {
				username := "user" + string(rune('0'+id))
				settings := &models.UserSettings{
					Username: &username,
				}
				err := UpdateSettings(settings)
				assert.NoError(t, err)
				done <- true
			}(i)
		}

		// Wait for all goroutines
		for i := 0; i < 5; i++ {
			<-done
		}

		// Verify database is still consistent
		retrieved, err := GetSettings()
		require.NoError(t, err)
		assert.NotNil(t, retrieved.Username)
	})

	t.Run("ConcurrentReadsDuringUpdate", func(t *testing.T) {
		// Test reads don't block on writes
		done := make(chan bool)

		// Start continuous updates
		go func() {
			for i := 0; i < 10; i++ {
				username := "concurrent"
				settings := &models.UserSettings{
					Username: &username,
				}
				UpdateSettings(settings)
			}
			done <- true
		}()

		// Perform concurrent reads
		for i := 0; i < 10; i++ {
			go func() {
				_, err := GetSettings()
				assert.NoError(t, err)
				done <- true
			}()
		}

		// Wait for all operations
		for i := 0; i < 11; i++ {
			<-done
		}
	})
}
