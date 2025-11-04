package database

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	"email-helper-backend/internal/models"
)

// GetSettings retrieves user settings
func GetSettings() (*models.UserSettings, error) {
	db, err := GetDB()
	if err != nil {
		return nil, err
	}

	query := `
		SELECT username, job_context, newsletter_interests, azure_openai_endpoint,
		       azure_openai_deployment, custom_prompts, ado_area_path, ado_pat
		FROM user_settings
		WHERE user_id = 1
	`

	var username, jobContext, newsletterInterests, azureEndpoint, azureDeployment sql.NullString
	var customPromptsJSON, adoAreaPath, adoPat sql.NullString

	err = db.QueryRow(query).Scan(
		&username,
		&jobContext,
		&newsletterInterests,
		&azureEndpoint,
		&azureDeployment,
		&customPromptsJSON,
		&adoAreaPath,
		&adoPat,
	)

	if err == sql.ErrNoRows {
		// Return empty settings if none exist
		return &models.UserSettings{}, nil
	}
	if err != nil {
		return nil, err
	}

	settings := &models.UserSettings{}

	if username.Valid {
		settings.Username = &username.String
	}
	if jobContext.Valid {
		settings.JobContext = &jobContext.String
	}
	if newsletterInterests.Valid {
		settings.NewsletterInterests = &newsletterInterests.String
	}
	if azureEndpoint.Valid {
		settings.AzureOpenAIEndpoint = &azureEndpoint.String
	}
	if azureDeployment.Valid {
		settings.AzureOpenAIDeployment = &azureDeployment.String
	}
	if adoAreaPath.Valid {
		settings.ADOAreaPath = &adoAreaPath.String
	}
	if adoPat.Valid {
		settings.ADOPAT = &adoPat.String
	}

	// Parse custom prompts JSON
	if customPromptsJSON.Valid && customPromptsJSON.String != "" {
		var customPrompts map[string]string
		if err := json.Unmarshal([]byte(customPromptsJSON.String), &customPrompts); err == nil {
			settings.CustomPrompts = customPrompts
		}
	}

	return settings, nil
}

// UpdateSettings updates user settings
func UpdateSettings(settings *models.UserSettings) error {
	db, err := GetDB()
	if err != nil {
		return err
	}

	// Check if settings row exists
	var exists bool
	err = db.QueryRow("SELECT EXISTS(SELECT 1 FROM user_settings WHERE user_id = 1)").Scan(&exists)
	if err != nil {
		return err
	}

	// If no row exists, insert a default row first
	if !exists {
		insertQuery := `
			INSERT INTO user_settings (user_id, updated_at)
			VALUES (1, ?)
		`
		_, err = db.Exec(insertQuery, time.Now())
		if err != nil {
			return fmt.Errorf("failed to create settings row: %w", err)
		}
	}

	// Build dynamic update query
	setClause := "updated_at = ?"
	args := []interface{}{time.Now()}

	if settings.Username != nil {
		setClause += ", username = ?"
		args = append(args, *settings.Username)
	}
	if settings.JobContext != nil {
		setClause += ", job_context = ?"
		args = append(args, *settings.JobContext)
	}
	if settings.NewsletterInterests != nil {
		setClause += ", newsletter_interests = ?"
		args = append(args, *settings.NewsletterInterests)
	}
	if settings.AzureOpenAIEndpoint != nil {
		setClause += ", azure_openai_endpoint = ?"
		args = append(args, *settings.AzureOpenAIEndpoint)
	}
	if settings.AzureOpenAIDeployment != nil {
		setClause += ", azure_openai_deployment = ?"
		args = append(args, *settings.AzureOpenAIDeployment)
	}
	if settings.ADOAreaPath != nil {
		setClause += ", ado_area_path = ?"
		args = append(args, *settings.ADOAreaPath)
	}
	if settings.ADOPAT != nil {
		setClause += ", ado_pat = ?"
		args = append(args, *settings.ADOPAT)
	}
	if settings.CustomPrompts != nil {
		customPromptsJSON, err := json.Marshal(settings.CustomPrompts)
		if err != nil {
			return fmt.Errorf("failed to marshal custom prompts: %w", err)
		}
		setClause += ", custom_prompts = ?"
		args = append(args, string(customPromptsJSON))
	}

	query := fmt.Sprintf("UPDATE user_settings SET %s WHERE user_id = 1", setClause)
	_, err = db.Exec(query, args...)
	return err
}

// ResetSettings resets user settings to defaults
func ResetSettings() error {
	db, err := GetDB()
	if err != nil {
		return err
	}

	query := `
		UPDATE user_settings
		SET username = NULL,
		    job_context = NULL,
		    newsletter_interests = NULL,
		    azure_openai_endpoint = NULL,
		    azure_openai_deployment = NULL,
		    custom_prompts = NULL,
		    ado_area_path = NULL,
		    ado_pat = NULL,
		    updated_at = ?
		WHERE user_id = 1
	`

	_, err = db.Exec(query, time.Now())
	return err
}
