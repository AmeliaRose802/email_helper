package main

import (
	"fmt"
	"log"

	"email-helper-backend/pkg/prompty"
)

func main() {
	// Try to load prompts from various locations
	locations := []string{
		"./prompts",
		"../prompts",
		"../../prompts",
	}

	var templates map[string]*prompty.PromptyTemplate
	var err error
	var loadedFrom string

	for _, loc := range locations {
		templates, err = prompty.LoadPromptDirectory(loc)
		if err == nil {
			loadedFrom = loc
			break
		}
	}

	if err != nil {
		log.Fatalf("Failed to load prompty files from any location: %v", err)
	}

	fmt.Printf("✓ Successfully loaded %d prompty templates from %s\n\n", len(templates), loadedFrom)

	// List all loaded templates
	for name, tmpl := range templates {
		fmt.Printf("Template: %s\n", name)
		fmt.Printf("  Name: %s\n", tmpl.Name)
		fmt.Printf("  Description: %s\n", tmpl.Description)
		fmt.Printf("  Version: %s\n", tmpl.Version)
		fmt.Printf("  Temperature: %.1f\n", tmpl.Model.Parameters.Temperature)
		fmt.Printf("  Max Tokens: %d\n", tmpl.Model.Parameters.MaxTokens)
		fmt.Printf("  System Prompt Length: %d chars\n", len(tmpl.SystemPrompt))
		fmt.Printf("  User Prompt Length: %d chars\n\n", len(tmpl.UserPrompt))
	}

	// Test rendering the classification template
	if classifyTmpl, ok := templates["email_classifier_with_explanation"]; ok {
		fmt.Println("Testing email_classifier_with_explanation template rendering:")
		
		vars := map[string]string{
			"context":          "Team collaboration",
			"job_role_context": "Software Engineer working on email management tools",
			"username":         "TestUser",
			"subject":          "Code Review Request: PR #1234",
			"sender":           "teammate@example.com",
			"date":             "2025-10-31",
			"body":             "Please review my pull request for the email classification feature.",
		}

		systemPrompt, err := classifyTmpl.RenderPrompt("system", vars)
		if err != nil {
			log.Fatalf("Failed to render system prompt: %v", err)
		}

		userPrompt, err := classifyTmpl.RenderPrompt("user", vars)
		if err != nil {
			log.Fatalf("Failed to render user prompt: %v", err)
		}

		fmt.Printf("  System Prompt (first 200 chars): %s...\n", systemPrompt[:min(200, len(systemPrompt))])
		fmt.Printf("  User Prompt (first 200 chars): %s...\n\n", userPrompt[:min(200, len(userPrompt))])
		fmt.Println("✓ Template rendering successful!")
	} else {
		fmt.Println("⚠ email_classifier_with_explanation template not found")
	}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
