package handlers

import (
	"net/http"

	"email-helper-backend/internal/models"

	"github.com/gin-gonic/gin"
)

// GetSettings retrieves user settings
func GetSettings(c *gin.Context) {
	settings, err := settingsService.GetSettings()
	if err != nil {
		DatabaseError(c, "Failed to retrieve settings: "+err.Error())
		return
	}

	c.JSON(http.StatusOK, settings)
}

// UpdateSettings updates user settings
func UpdateSettings(c *gin.Context) {
	var settings models.UserSettings
	if err := c.ShouldBindJSON(&settings); err != nil {
		BadRequest(c, "Invalid request body: "+err.Error())
		return
	}

	if err := settingsService.UpdateSettings(&settings); err != nil {
		DatabaseError(c, "Failed to update settings: "+err.Error())
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Settings updated",
	})
}

// ResetSettings resets settings to defaults
func ResetSettings(c *gin.Context) {
	if err := settingsService.ResetSettings(); err != nil {
		DatabaseError(c, "Failed to reset settings: "+err.Error())
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Settings reset to defaults",
	})
}
