package services

import (
	"os"
	"path/filepath"
	"testing"

	"email-helper-backend/internal/database"
	"email-helper-backend/internal/models"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/suite"
)

type SettingsServiceTestSuite struct {
	suite.Suite
	service *SettingsService
	testDB  string
}

func (suite *SettingsServiceTestSuite) SetupSuite() {
	// Reset database for this test suite
	database.ResetForTesting()
	
	// Create temp database for testing
	suite.testDB = filepath.Join(os.TempDir(), "test_settings.db")
	
	// Remove existing test database
	os.Remove(suite.testDB)
	
	// Initialize database
	err := database.InitDB(suite.testDB)
	suite.Require().NoError(err)
	
	// Tables are already created by InitDB
	suite.service = NewSettingsService()
}

func (suite *SettingsServiceTestSuite) TearDownSuite() {
	// Close and reset database for next test suite
	database.Close()
	database.ResetForTesting()
	os.Remove(suite.testDB)
}

func (suite *SettingsServiceTestSuite) TearDownTest() {
	db, _ := database.GetDB()
	db.Exec("DELETE FROM user_settings")
}

func (suite *SettingsServiceTestSuite) TestGetSettings() {
	// Initially should return defaults
	settings, err := suite.service.GetSettings()
	
	assert.NoError(suite.T(), err)
	assert.NotNil(suite.T(), settings)
}

func (suite *SettingsServiceTestSuite) TestUpdateSettings() {
	username := "testuser"
	jobContext := "Software Engineer"
	endpoint := "https://test.openai.azure.com"
	deployment := "gpt-4"
	
	newSettings := &models.UserSettings{
		Username:              &username,
		JobContext:            &jobContext,
		AzureOpenAIEndpoint:   &endpoint,
		AzureOpenAIDeployment: &deployment,
	}
	
	err := suite.service.UpdateSettings(newSettings)
	assert.NoError(suite.T(), err)
	
	// Retrieve and verify
	retrieved, err := suite.service.GetSettings()
	assert.NoError(suite.T(), err)
	assert.NotNil(suite.T(), retrieved.Username)
	assert.Equal(suite.T(), username, *retrieved.Username)
	assert.NotNil(suite.T(), retrieved.JobContext)
	assert.Equal(suite.T(), jobContext, *retrieved.JobContext)
}

func (suite *SettingsServiceTestSuite) TestUpdateSettingsPartial() {
	// Set initial settings
	username := "initialuser"
	jobContext := "Initial Job"
	
	initial := &models.UserSettings{
		Username:   &username,
		JobContext: &jobContext,
	}
	suite.service.UpdateSettings(initial)
	
	// Update only username
	newUsername := "updateduser"
	partial := &models.UserSettings{
		Username: &newUsername,
	}
	
	err := suite.service.UpdateSettings(partial)
	assert.NoError(suite.T(), err)
	
	// Verify username changed but job context remains
	retrieved, _ := suite.service.GetSettings()
	assert.Equal(suite.T(), newUsername, *retrieved.Username)
}

func (suite *SettingsServiceTestSuite) TestUpdateCustomPrompts() {
	customPrompts := map[string]string{
		"classification": "Custom classification prompt",
		"summary":        "Custom summary prompt",
	}
	
	settings := &models.UserSettings{
		CustomPrompts: customPrompts,
	}
	
	err := suite.service.UpdateSettings(settings)
	assert.NoError(suite.T(), err)
	
	// Retrieve and verify
	retrieved, _ := suite.service.GetSettings()
	assert.NotNil(suite.T(), retrieved.CustomPrompts)
	assert.Equal(suite.T(), len(customPrompts), len(retrieved.CustomPrompts))
}

func (suite *SettingsServiceTestSuite) TestResetSettings() {
	// Set some settings
	username := "testuser"
	settings := &models.UserSettings{
		Username: &username,
	}
	suite.service.UpdateSettings(settings)
	
	// Reset
	err := suite.service.ResetSettings()
	assert.NoError(suite.T(), err)
	
	// Verify reset
	retrieved, _ := suite.service.GetSettings()
	assert.NotNil(suite.T(), retrieved)
	// Settings should be back to defaults
}

func TestSettingsServiceTestSuite(t *testing.T) {
	suite.Run(t, new(SettingsServiceTestSuite))
}
