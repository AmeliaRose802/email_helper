package services

import (
	"email-helper-backend/internal/database"
	"email-helper-backend/internal/models"
)

// SettingsService handles user settings operations
type SettingsService struct{}

// NewSettingsService creates a new settings service
func NewSettingsService() *SettingsService {
	return &SettingsService{}
}

// GetSettings retrieves user settings
func (s *SettingsService) GetSettings() (*models.UserSettings, error) {
	return database.GetSettings()
}

// UpdateSettings updates user settings
func (s *SettingsService) UpdateSettings(settings *models.UserSettings) error {
	return database.UpdateSettings(settings)
}

// ResetSettings resets settings to defaults
func (s *SettingsService) ResetSettings() error {
	return database.ResetSettings()
}
