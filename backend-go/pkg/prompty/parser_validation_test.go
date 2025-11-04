package prompty

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestYAMLFrontmatterParsing tests various YAML frontmatter scenarios
func TestYAMLFrontmatterParsing(t *testing.T) {
	t.Run("ValidYAML", func(t *testing.T) {
		content := `---
name: Valid Prompt
description: Test prompt
version: 1.0
model:
  api: chat
  parameters:
    temperature: 0.7
    max_tokens: 500
inputs:
  test:
    type: string
---

system:
Test system prompt

user:
Test user prompt
`
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		assert.Equal(t, "Valid Prompt", tmpl.Name)
		assert.Equal(t, "Test prompt", tmpl.Description)
		assert.Equal(t, float32(0.7), tmpl.Model.Parameters.Temperature)
		assert.Equal(t, int32(500), tmpl.Model.Parameters.MaxTokens)
	})

	t.Run("InvalidYAML_BadIndentation", func(t *testing.T) {
		content := `---
name: Bad Indent
model:
api: chat
  parameters:
    temperature: 0.7
---

system:
Test

user:
Test
`
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "failed to parse YAML frontmatter")
	})

	t.Run("InvalidYAML_UnterminatedString", func(t *testing.T) {
		content := `---
name: "Unterminated string
description: Test
---

system:
Test

user:
Test
`
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
	})

	t.Run("MissingDelimiters", func(t *testing.T) {
		content := `name: No Delimiters
description: Missing --- markers

system:
Test
user:
Test
`
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "invalid prompty format")
	})

	t.Run("OnlyOneDelimiter", func(t *testing.T) {
		content := `---
name: One Delimiter
description: Missing closing delimiter
system:
Test
user:
Test
`
		// SplitN with 3 will only find 2 parts if there's only one ---
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
		// Can be either format error or missing sections error
		assert.True(t, strings.Contains(err.Error(), "invalid prompty format") || 
			strings.Contains(err.Error(), "must contain both 'system:' and 'user:' sections"))
	})

	t.Run("EmptyFrontmatter", func(t *testing.T) {
		content := `---
---

system:
Test

user:
Test
`
		tmpl, err := ParsePromptyContent([]byte(content))
		// Should parse but have empty fields
		require.NoError(t, err)
		assert.Empty(t, tmpl.Name)
		assert.Empty(t, tmpl.Description)
	})

	t.Run("MalformedYAML_DuplicateKeys", func(t *testing.T) {
		content := `---
name: First Name
name: Second Name
description: Test
---

system:
Test

user:
Test
`
		_, err := ParsePromptyContent([]byte(content))
		// YAML parser is strict and errors on duplicate keys
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "failed to parse YAML frontmatter")
	})
}

// TestTemplateVariableValidation tests template variable handling
func TestTemplateVariableValidation(t *testing.T) {
	t.Run("ValidVariables", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			SystemPrompt: "You are analyzing email from {{sender}}.",
			UserPrompt:   "Subject: {{subject}}\nBody: {{body}}",
		}
		
		vars := map[string]string{
			"sender":  "test@example.com",
			"subject": "Test Subject",
			"body":    "Test Body",
		}
		
		systemRendered, err := tmpl.RenderPrompt("system", vars)
		require.NoError(t, err)
		assert.Contains(t, systemRendered, "test@example.com")
		
		userRendered, err := tmpl.RenderPrompt("user", vars)
		require.NoError(t, err)
		assert.Contains(t, userRendered, "Test Subject")
		assert.Contains(t, userRendered, "Test Body")
	})

	t.Run("MissingVariable", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			UserPrompt: "Email from {{sender}} about {{subject}}",
		}
		
		vars := map[string]string{
			"sender": "test@example.com",
			// Missing "subject"
		}
		
		rendered, err := tmpl.RenderPrompt("user", vars)
		// Go templates don't error on missing variables, they use <no value>
		require.NoError(t, err)
		assert.Contains(t, rendered, "test@example.com")
		assert.Contains(t, rendered, "<no value>")
	})

	t.Run("InvalidVariableSyntax_MissingCloseBrace", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			UserPrompt: "Subject: {{subject",
		}
		
		vars := map[string]string{"subject": "Test"}
		
		_, err := tmpl.RenderPrompt("user", vars)
		assert.Error(t, err)
	})

	t.Run("InvalidVariableSyntax_MissingOpenBrace", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			UserPrompt: "Subject: subject}}",
		}
		
		vars := map[string]string{"subject": "Test"}
		
		rendered, err := tmpl.RenderPrompt("user", vars)
		require.NoError(t, err)
		// Without proper braces, it's treated as literal text
		assert.Contains(t, rendered, "subject}}")
	})

	t.Run("VariableWithSpaces", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			UserPrompt: "Value: {{ variable_name }}",
		}
		
		vars := map[string]string{"variable_name": "test value"}
		
		rendered, err := tmpl.RenderPrompt("user", vars)
		require.NoError(t, err)
		assert.Contains(t, rendered, "test value")
	})

	t.Run("VariableWithUnderscores", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			UserPrompt: "User: {{user_name}}, Email: {{email_address}}",
		}
		
		vars := map[string]string{
			"user_name":     "John Doe",
			"email_address": "john@example.com",
		}
		
		rendered, err := tmpl.RenderPrompt("user", vars)
		require.NoError(t, err)
		assert.Contains(t, rendered, "John Doe")
		assert.Contains(t, rendered, "john@example.com")
	})

	t.Run("NestedBraces", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			UserPrompt: "Data: {{data}}",
		}
		
		vars := map[string]string{
			"data": "Value with {{nested}} braces",
		}
		
		rendered, err := tmpl.RenderPrompt("user", vars)
		require.NoError(t, err)
		// Nested braces in the value should be treated as literal text
		assert.Contains(t, rendered, "{{nested}}")
	})
}

// TestRequiredFields tests validation of required prompty fields
func TestRequiredFields(t *testing.T) {
	t.Run("MissingName", func(t *testing.T) {
		content := `---
description: Test
model:
  api: chat
---

system:
Test

user:
Test
`
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		assert.Empty(t, tmpl.Name)
	})

	t.Run("MissingDescription", func(t *testing.T) {
		content := `---
name: Test
model:
  api: chat
---

system:
Test

user:
Test
`
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		assert.Empty(t, tmpl.Description)
	})

	t.Run("MissingModel", func(t *testing.T) {
		content := `---
name: Test
description: Test
---

system:
Test

user:
Test
`
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		assert.Empty(t, tmpl.Model.API)
	})

	t.Run("MissingSystemSection", func(t *testing.T) {
		content := `---
name: Test
description: Test
---

user:
Test user prompt
`
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "must contain both 'system:' and 'user:' sections")
	})

	t.Run("MissingUserSection", func(t *testing.T) {
		content := `---
name: Test
description: Test
---

system:
Test system prompt
`
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "must contain both 'system:' and 'user:' sections")
	})

	t.Run("MissingBothSections", func(t *testing.T) {
		content := `---
name: Test
description: Test
---

Just some random text
`
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "must contain both 'system:' and 'user:' sections")
	})
}

// TestInputParameterValidation tests input parameter definitions
func TestInputParameterValidation(t *testing.T) {
	t.Run("ValidInputs", func(t *testing.T) {
		content := `---
name: Test
description: Test
inputs:
  subject:
    type: string
  sender:
    type: string
  body:
    type: string
---

system:
Test

user:
Subject: {{subject}}
Sender: {{sender}}
Body: {{body}}
`
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		assert.Len(t, tmpl.Inputs, 3)
		assert.Equal(t, "string", tmpl.Inputs["subject"].Type)
		assert.Equal(t, "string", tmpl.Inputs["sender"].Type)
		assert.Equal(t, "string", tmpl.Inputs["body"].Type)
	})

	t.Run("NoInputsDefined", func(t *testing.T) {
		content := `---
name: Test
description: Test
---

system:
Test

user:
Static prompt with no variables
`
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		assert.Empty(t, tmpl.Inputs)
	})

	t.Run("EmptyInputsSection", func(t *testing.T) {
		content := `---
name: Test
description: Test
inputs: {}
---

system:
Test

user:
Test
`
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		assert.Empty(t, tmpl.Inputs)
	})

	t.Run("InvalidInputType", func(t *testing.T) {
		content := `---
name: Test
description: Test
inputs:
  field:
    type: 12345
---

system:
Test

user:
Test
`
		// YAML will parse this, but type will be empty or invalid
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		// Type would be empty string since 12345 can't convert to string properly
		assert.NotEmpty(t, tmpl.Inputs)
	})
}

// TestPromptySpecificTests tests specific prompt templates
func TestPromptySpecificTests(t *testing.T) {
	t.Run("ClassificationPromptInputs", func(t *testing.T) {
		content := `---
name: Email Classification
description: Classify emails
inputs:
  subject:
    type: string
  sender:
    type: string
  body:
    type: string
  date:
    type: string
  context:
    type: string
  username:
    type: string
---

system:
Classify the email.

user:
Subject: {{subject}}
Sender: {{sender}}
Date: {{date}}
Body: {{body}}
Context: {{context}}
User: {{username}}
`
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		
		// Verify all required classification inputs are defined
		requiredInputs := []string{"subject", "sender", "body", "date", "context", "username"}
		for _, input := range requiredInputs {
			assert.Contains(t, tmpl.Inputs, input, "Missing required input: "+input)
		}
		
		// Verify user prompt contains all variables
		for _, input := range requiredInputs {
			assert.Contains(t, tmpl.UserPrompt, "{{"+input+"}}", "User prompt missing variable: "+input)
		}
	})

	t.Run("ActionExtractionPrompt", func(t *testing.T) {
		content := `---
name: Action Item Extraction
description: Extract action items
inputs:
  subject:
    type: string
  body:
    type: string
  sender:
    type: string
---

system:
Extract action items.

user:
Email Subject: {{subject}}
From: {{sender}}
Content: {{body}}
`
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		
		// Verify action extraction required inputs
		assert.Contains(t, tmpl.Inputs, "subject")
		assert.Contains(t, tmpl.Inputs, "body")
		assert.Contains(t, tmpl.Inputs, "sender")
	})

	t.Run("SummaryPrompt", func(t *testing.T) {
		content := `---
name: Email Summary
description: Summarize email
inputs:
  content:
    type: string
  type:
    type: string
---

system:
Summarize the email.

user:
Content: {{content}}
Summary Type: {{type}}
`
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		
		assert.Contains(t, tmpl.Inputs, "content")
		assert.Contains(t, tmpl.Inputs, "type")
	})

	t.Run("MultiLineTemplateHandling", func(t *testing.T) {
		content := `---
name: Multi-line Test
description: Test
inputs:
  field1:
    type: string
  field2:
    type: string
---

system:
This is a multi-line
system prompt that spans
multiple lines with proper
formatting.

user:
Field 1:
{{field1}}

Field 2:
{{field2}}

Additional context
on multiple lines.
`
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		
		// Verify multi-line content is preserved
		assert.Contains(t, tmpl.SystemPrompt, "multi-line")
		assert.Contains(t, tmpl.SystemPrompt, "formatting")
		assert.Contains(t, tmpl.UserPrompt, "Field 1:")
		assert.Contains(t, tmpl.UserPrompt, "Field 2:")
		assert.Contains(t, tmpl.UserPrompt, "Additional context")
	})
}

// TestEdgeCases tests various edge case scenarios
func TestEdgeCases(t *testing.T) {
	t.Run("EmptyFile", func(t *testing.T) {
		content := ``
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "invalid prompty format")
	})

	t.Run("OnlyFrontmatter_NoPromptContent", func(t *testing.T) {
		content := `---
name: Only Frontmatter
description: No prompt content
---
`
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "must contain both 'system:' and 'user:' sections")
	})

	t.Run("PromptWithNoVariables", func(t *testing.T) {
		content := `---
name: Static Prompt
description: No template variables
---

system:
This is a static system prompt.

user:
This is a static user prompt.
`
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		
		systemRendered, err := tmpl.RenderPrompt("system", map[string]string{})
		require.NoError(t, err)
		assert.Equal(t, "This is a static system prompt.", systemRendered)
		
		userRendered, err := tmpl.RenderPrompt("user", map[string]string{})
		require.NoError(t, err)
		assert.Equal(t, "This is a static user prompt.", userRendered)
	})

	t.Run("DuplicateVariableNames", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			UserPrompt: "Value1: {{var}} Value2: {{var}}",
		}
		
		vars := map[string]string{"var": "test"}
		
		rendered, err := tmpl.RenderPrompt("user", vars)
		require.NoError(t, err)
		// Both occurrences should be replaced
		assert.Equal(t, "Value1: test Value2: test", rendered)
	})

	t.Run("SpecialCharactersInVariableValue", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			UserPrompt: "Content: {{content}}",
		}
		
		vars := map[string]string{
			"content": "Special chars: <>&\"'\n\t{}[]",
		}
		
		rendered, err := tmpl.RenderPrompt("user", vars)
		require.NoError(t, err)
		assert.Contains(t, rendered, "Special chars:")
		assert.Contains(t, rendered, "<>&\"'")
	})

	t.Run("ExtraWhitespaceAroundSections", func(t *testing.T) {
		content := `---
name: Test
description: Test
---


system:


System prompt with extra whitespace


user:


User prompt with extra whitespace


`
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		
		// TrimSpace should handle extra whitespace
		assert.NotEmpty(t, tmpl.SystemPrompt)
		assert.NotEmpty(t, tmpl.UserPrompt)
		assert.Contains(t, tmpl.SystemPrompt, "System prompt")
		assert.Contains(t, tmpl.UserPrompt, "User prompt")
	})
}

// TestErrorMessageQuality tests that error messages are helpful
func TestErrorMessageQuality(t *testing.T) {
	t.Run("InvalidFormat_ClearError", func(t *testing.T) {
		content := `Invalid prompty file`
		_, err := ParsePromptyContent([]byte(content))
		require.Error(t, err)
		// Error should mention format issue
		assert.Contains(t, strings.ToLower(err.Error()), "format")
	})

	t.Run("MissingSections_ClearError", func(t *testing.T) {
		content := `---
name: Test
---

No sections here
`
		_, err := ParsePromptyContent([]byte(content))
		require.Error(t, err)
		// Error should mention missing sections
		assert.Contains(t, err.Error(), "system")
		assert.Contains(t, err.Error(), "user")
	})

	t.Run("InvalidPromptType_ClearError", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			SystemPrompt: "Test",
			UserPrompt:   "Test",
		}
		
		_, err := tmpl.RenderPrompt("invalid", map[string]string{})
		require.Error(t, err)
		// Error should mention valid types
		assert.Contains(t, err.Error(), "invalid prompt type")
		assert.Contains(t, err.Error(), "system")
		assert.Contains(t, err.Error(), "user")
	})

	t.Run("YAMLParseError_IncludesDetails", func(t *testing.T) {
		content := `---
name: [invalid yaml
description: "unterminated
---

system:
Test

user:
Test
`
		_, err := ParsePromptyContent([]byte(content))
		require.Error(t, err)
		// Error should mention YAML issue
		assert.Contains(t, strings.ToLower(err.Error()), "yaml")
	})
}

// TestConvertPromptyToGoTemplateValidation tests the template conversion function with validation focus
func TestConvertPromptyToGoTemplateValidation(t *testing.T) {
	t.Run("SimpleVariable", func(t *testing.T) {
		input := "Hello {{name}}"
		expected := "Hello {{.name}}"
		result := convertPromptyToGoTemplate(input)
		assert.Equal(t, expected, result)
	})

	t.Run("MultipleVariables", func(t *testing.T) {
		input := "{{greeting}} {{name}}, today is {{day}}"
		expected := "{{.greeting}} {{.name}}, today is {{.day}}"
		result := convertPromptyToGoTemplate(input)
		assert.Equal(t, expected, result)
	})

	t.Run("VariablesWithSpaces", func(t *testing.T) {
		input := "{{ name }} and {{ email }}"
		expected := "{{.name}} and {{.email}}"
		result := convertPromptyToGoTemplate(input)
		assert.Equal(t, expected, result)
	})

	t.Run("VariablesWithUnderscores", func(t *testing.T) {
		input := "{{user_name}} and {{email_address}}"
		expected := "{{.user_name}} and {{.email_address}}"
		result := convertPromptyToGoTemplate(input)
		assert.Equal(t, expected, result)
	})

	t.Run("NoVariables", func(t *testing.T) {
		input := "Static text with no variables"
		expected := "Static text with no variables"
		result := convertPromptyToGoTemplate(input)
		assert.Equal(t, expected, result)
	})

	t.Run("MalformedBraces", func(t *testing.T) {
		input := "{{incomplete and {single} and incomplete}}"
		// Should not modify malformed patterns
		result := convertPromptyToGoTemplate(input)
		// Only valid patterns get converted
		assert.NotContains(t, result, "{{.incomplete")
	})
}

// TestLoadPromptDirectory tests directory loading functionality
func TestLoadPromptDirectory(t *testing.T) {
	// Create a temporary directory for test files
	tmpDir := t.TempDir()

	t.Run("LoadValidPromptFiles", func(t *testing.T) {
		// Create valid test files
		validPrompt1 := `---
name: Prompt 1
description: First test prompt
---

system:
System 1

user:
User 1
`
		validPrompt2 := `---
name: Prompt 2
description: Second test prompt
---

system:
System 2

user:
User 2
`
		
		err := os.WriteFile(filepath.Join(tmpDir, "prompt1.prompty"), []byte(validPrompt1), 0644)
		require.NoError(t, err)
		err = os.WriteFile(filepath.Join(tmpDir, "prompt2.prompty"), []byte(validPrompt2), 0644)
		require.NoError(t, err)
		
		templates, err := LoadPromptDirectory(tmpDir)
		require.NoError(t, err)
		assert.Len(t, templates, 2)
		assert.Contains(t, templates, "prompt1")
		assert.Contains(t, templates, "prompt2")
		assert.Equal(t, "Prompt 1", templates["prompt1"].Name)
		assert.Equal(t, "Prompt 2", templates["prompt2"].Name)
	})

	t.Run("SkipInvalidFiles", func(t *testing.T) {
		tmpDir2 := t.TempDir()
		
		// Create one valid and one invalid file
		validPrompt := `---
name: Valid
description: Valid prompt
---

system:
Test

user:
Test
`
		invalidPrompt := `Invalid content without proper format`
		
		err := os.WriteFile(filepath.Join(tmpDir2, "valid.prompty"), []byte(validPrompt), 0644)
		require.NoError(t, err)
		err = os.WriteFile(filepath.Join(tmpDir2, "invalid.prompty"), []byte(invalidPrompt), 0644)
		require.NoError(t, err)
		
		templates, err := LoadPromptDirectory(tmpDir2)
		require.NoError(t, err)
		// Should load only the valid file
		assert.Len(t, templates, 1)
		assert.Contains(t, templates, "valid")
	})

	t.Run("SkipNonPromptyFiles", func(t *testing.T) {
		tmpDir3 := t.TempDir()
		
		validPrompt := `---
name: Valid
description: Valid prompt
---

system:
Test

user:
Test
`
		
		err := os.WriteFile(filepath.Join(tmpDir3, "prompt.prompty"), []byte(validPrompt), 0644)
		require.NoError(t, err)
		err = os.WriteFile(filepath.Join(tmpDir3, "readme.txt"), []byte("Not a prompty file"), 0644)
		require.NoError(t, err)
		err = os.WriteFile(filepath.Join(tmpDir3, "config.yaml"), []byte("Also not a prompty file"), 0644)
		require.NoError(t, err)
		
		templates, err := LoadPromptDirectory(tmpDir3)
		require.NoError(t, err)
		// Should only load .prompty files
		assert.Len(t, templates, 1)
		assert.Contains(t, templates, "prompt")
	})

	t.Run("EmptyDirectory", func(t *testing.T) {
		tmpDir4 := t.TempDir()
		
		_, err := LoadPromptDirectory(tmpDir4)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "no valid .prompty files found")
	})

	t.Run("NonExistentDirectory", func(t *testing.T) {
		_, err := LoadPromptDirectory("/nonexistent/path/to/prompts")
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "failed to read prompts directory")
	})
}

// TestParsePromptyFile tests file reading and parsing
func TestParsePromptyFile(t *testing.T) {
	tmpDir := t.TempDir()

	t.Run("ValidFile", func(t *testing.T) {
		content := `---
name: File Test
description: Test file parsing
---

system:
System prompt

user:
User prompt
`
		filePath := filepath.Join(tmpDir, "test.prompty")
		err := os.WriteFile(filePath, []byte(content), 0644)
		require.NoError(t, err)
		
		tmpl, err := ParsePromptyFile(filePath)
		require.NoError(t, err)
		assert.Equal(t, "File Test", tmpl.Name)
	})

	t.Run("NonExistentFile", func(t *testing.T) {
		_, err := ParsePromptyFile("/nonexistent/file.prompty")
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "failed to read prompty file")
	})

	t.Run("InvalidFileContent", func(t *testing.T) {
		filePath := filepath.Join(tmpDir, "invalid.prompty")
		err := os.WriteFile(filePath, []byte("Invalid content"), 0644)
		require.NoError(t, err)
		
		_, err = ParsePromptyFile(filePath)
		assert.Error(t, err)
	})
}
