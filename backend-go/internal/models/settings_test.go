package models

import (
	"encoding/json"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestUserSettingsSerialization(t *testing.T) {
	username := "testuser"
	jobContext := "Software Engineer"
	endpoint := "https://test.openai.azure.com"
	deployment := "gpt-4"

	settings := UserSettings{
		Username:              &username,
		JobContext:            &jobContext,
		AzureOpenAIEndpoint:   &endpoint,
		AzureOpenAIDeployment: &deployment,
		CustomPrompts: map[string]string{
			"classification": "Custom prompt",
			"summary":        "Summary prompt",
		},
	}

	// Test JSON serialization
	jsonData, err := json.Marshal(settings)
	assert.NoError(t, err)
	assert.Contains(t, string(jsonData), "testuser")
	assert.Contains(t, string(jsonData), "custom_prompts")

	// Test JSON deserialization
	var decoded UserSettings
	err = json.Unmarshal(jsonData, &decoded)
	assert.NoError(t, err)
	assert.NotNil(t, decoded.Username)
	assert.Equal(t, *settings.Username, *decoded.Username)
	assert.NotNil(t, decoded.JobContext)
	assert.Equal(t, *settings.JobContext, *decoded.JobContext)
	assert.Equal(t, len(settings.CustomPrompts), len(decoded.CustomPrompts))
}

func TestUserSettingsPartial(t *testing.T) {
	username := "testuser"

	settings := UserSettings{
		Username: &username,
	}

	jsonData, err := json.Marshal(settings)
	assert.NoError(t, err)
	assert.Contains(t, string(jsonData), "testuser")

	var decoded UserSettings
	err = json.Unmarshal(jsonData, &decoded)
	assert.NoError(t, err)
	assert.NotNil(t, decoded.Username)
	assert.Nil(t, decoded.JobContext)
	assert.Nil(t, decoded.AzureOpenAIEndpoint)
}

func TestSettingsResponse(t *testing.T) {
	username := "testuser"
	settings := UserSettings{
		Username: &username,
	}

	response := SettingsResponse{
		Success:  true,
		Message:  "Settings updated successfully",
		Settings: &settings,
	}

	jsonData, err := json.Marshal(response)
	assert.NoError(t, err)
	assert.Contains(t, string(jsonData), "success")
	assert.Contains(t, string(jsonData), "testuser")

	var decoded SettingsResponse
	err = json.Unmarshal(jsonData, &decoded)
	assert.NoError(t, err)
	assert.True(t, decoded.Success)
	assert.Equal(t, response.Message, decoded.Message)
	assert.NotNil(t, decoded.Settings)
}

func TestCustomPrompts(t *testing.T) {
	settings := UserSettings{
		CustomPrompts: map[string]string{
			"classification": "You are an expert email classifier",
			"action_items":   "Extract all actionable tasks",
			"summary":        "Provide a concise summary",
		},
	}

	jsonData, err := json.Marshal(settings)
	assert.NoError(t, err)

	var decoded UserSettings
	err = json.Unmarshal(jsonData, &decoded)
	assert.NoError(t, err)
	assert.Equal(t, 3, len(decoded.CustomPrompts))
	assert.Contains(t, decoded.CustomPrompts, "classification")
	assert.Equal(t, settings.CustomPrompts["classification"], decoded.CustomPrompts["classification"])
}
