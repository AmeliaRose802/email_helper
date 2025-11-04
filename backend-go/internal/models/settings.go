package models

// UserSettings represents user configuration
type UserSettings struct {
	Username              *string                `json:"username,omitempty"`
	JobContext            *string                `json:"job_context,omitempty"`
	NewsletterInterests   *string                `json:"newsletter_interests,omitempty"`
	AzureOpenAIEndpoint   *string                `json:"azure_openai_endpoint,omitempty"`
	AzureOpenAIDeployment *string                `json:"azure_openai_deployment,omitempty"`
	CustomPrompts         map[string]string      `json:"custom_prompts,omitempty"`
	ADOAreaPath           *string                `json:"ado_area_path,omitempty"`
	ADOPAT                *string                `json:"ado_pat,omitempty"`
}

// SettingsResponse response for settings operations
type SettingsResponse struct {
	Success  bool          `json:"success"`
	Message  string        `json:"message"`
	Settings *UserSettings `json:"settings,omitempty"`
}
