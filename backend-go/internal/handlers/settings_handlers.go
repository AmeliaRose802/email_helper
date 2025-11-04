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
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, settings)
}

// UpdateSettings updates user settings
func UpdateSettings(c *gin.Context) {
	var settings models.UserSettings
	if err := c.ShouldBindJSON(&settings); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if err := settingsService.UpdateSettings(&settings); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
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
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Settings reset to defaults",
	})
}
