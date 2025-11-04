package azureopenai

import (
	"os"
	"path/filepath"
	"testing"

	"email-helper-backend/pkg/prompty"
)

func TestPromptyFileLoading(t *testing.T) {
	// Try to load prompts from the prompts directory
	promptsDir := filepath.Join("..", "..", "prompts")
	
	// Check if prompts directory exists
	if _, err := os.Stat(promptsDir); os.IsNotExist(err) {
		t.Skip("Prompts directory not found, skipping test")
	}

	prompts, err := prompty.LoadPromptDirectory(promptsDir)
	if err != nil {
		t.Fatalf("Failed to load prompty files: %v", err)
	}

	// Check that expected prompts are loaded
	expectedPrompts := []string{
		"email_classifier_with_explanation",
		"summerize_action_item",
		"email_one_line_summary",
	}

	for _, expected := range expectedPrompts {
		if _, ok := prompts[expected]; !ok {
			t.Errorf("Expected prompt '%s' not found", expected)
		} else {
			t.Logf("Found prompt: %s (%s)", expected, prompts[expected].Name)
		}
	}
}

func TestClassificationPromptRendering(t *testing.T) {
	promptsDir := filepath.Join("..", "..", "prompts")
	
	if _, err := os.Stat(promptsDir); os.IsNotExist(err) {
		t.Skip("Prompts directory not found, skipping test")
	}

	prompts, err := prompty.LoadPromptDirectory(promptsDir)
	if err != nil {
		t.Fatalf("Failed to load prompty files: %v", err)
	}

	tmpl, ok := prompts["email_classifier_with_explanation"]
	if !ok {
		t.Fatal("Classification template not found")
	}

	vars := map[string]string{
		"context":          "Test context",
		"job_role_context": "Software Engineer",
		"username":         "TestUser",
		"subject":          "Test Email",
		"sender":           "test@example.com",
		"date":             "2025-10-31",
		"body":             "This is a test email body",
	}

	systemPrompt, err := tmpl.RenderPrompt("system", vars)
	if err != nil {
		t.Fatalf("Failed to render system prompt: %v", err)
	}

	if len(systemPrompt) == 0 {
		t.Error("Rendered system prompt is empty")
	}

	if !contains(systemPrompt, "Software Engineer") {
		t.Error("System prompt doesn't contain job role context")
	}

	userPrompt, err := tmpl.RenderPrompt("user", vars)
	if err != nil {
		t.Fatalf("Failed to render user prompt: %v", err)
	}

	if len(userPrompt) == 0 {
		t.Error("Rendered user prompt is empty")
	}

	if !contains(userPrompt, "Test Email") {
		t.Error("User prompt doesn't contain subject")
	}

	t.Logf("System prompt length: %d", len(systemPrompt))
	t.Logf("User prompt length: %d", len(userPrompt))
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || findSubstring(s, substr))
}

func findSubstring(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
