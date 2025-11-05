package prompty

import (
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestParsePromptyContent(t *testing.T) {
	content := `---
name: Test Prompt
description: A test prompt
version: 1.0
model:
  api: chat
  parameters:
    temperature: 0.1
    max_tokens: 300
inputs:
  subject:
    type: string
  content:
    type: string
---

system:
You are a helpful assistant.
Process the email carefully.

user:
Subject: {{.subject}}
Content: {{.content}}
`

	tmpl, err := ParsePromptyContent([]byte(content))
	if err != nil {
		t.Fatalf("Failed to parse prompty content: %v", err)
	}

	if tmpl.Name != "Test Prompt" {
		t.Errorf("Expected name 'Test Prompt', got '%s'", tmpl.Name)
	}

	if tmpl.Model.Parameters.Temperature != 0.1 {
		t.Errorf("Expected temperature 0.1, got %f", tmpl.Model.Parameters.Temperature)
	}

	if tmpl.Model.Parameters.MaxTokens != 300 {
		t.Errorf("Expected max_tokens 300, got %d", tmpl.Model.Parameters.MaxTokens)
	}

	if !contains(tmpl.SystemPrompt, "helpful assistant") {
		t.Errorf("System prompt doesn't contain expected text: %s", tmpl.SystemPrompt)
	}

	if !contains(tmpl.UserPrompt, "{{.subject}}") {
		t.Errorf("User prompt doesn't contain template variable: %s", tmpl.UserPrompt)
	}
}

func TestRenderPrompt(t *testing.T) {
	tmpl := &PromptyTemplate{
		SystemPrompt: "You are a {{.role}}.",
		UserPrompt:   "Process: {{.input}}",
	}

	vars := map[string]string{
		"role":  "helpful assistant",
		"input": "test data",
	}

	systemRendered, err := tmpl.RenderPrompt("system", vars)
	if err != nil {
		t.Fatalf("Failed to render system prompt: %v", err)
	}

	if systemRendered != "You are a helpful assistant." {
		t.Errorf("Unexpected rendered system prompt: %s", systemRendered)
	}

	userRendered, err := tmpl.RenderPrompt("user", vars)
	if err != nil {
		t.Fatalf("Failed to render user prompt: %v", err)
	}

	if userRendered != "Process: test data" {
		t.Errorf("Unexpected rendered user prompt: %s", userRendered)
	}
}

// Test invalid YAML frontmatter
func TestParsePromptyContentInvalidYAML(t *testing.T) {
	t.Run("MalformedYAML", func(t *testing.T) {
		content := `---
name: Test
this is: not valid: yaml: structure
---

system:
Test

user:
Test
`
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "failed to parse YAML")
	})

	t.Run("InvalidYAMLStructure", func(t *testing.T) {
		content := `---
name
description
---

system:
Test

user:
Test
`
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
	})

	t.Run("EmptyYAMLFrontmatter", func(t *testing.T) {
		content := `---
---

system:
Test

user:
Test
`
		// Should parse but have empty fields
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		assert.Empty(t, tmpl.Name)
		assert.Empty(t, tmpl.Description)
	})
}

// Test missing delimiters
func TestParsePromptyContentMissingDelimiters(t *testing.T) {
	t.Run("NoDelimiters", func(t *testing.T) {
		content := `name: Test
system:
Test
user:
Test`
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "expected YAML frontmatter between --- markers")
	})

	t.Run("OnlyOneDelimiter", func(t *testing.T) {
		content := `---
name: Test
system:
Test
user:
Test`
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "expected YAML frontmatter between --- markers")
	})

	t.Run("DelimitersInWrongOrder", func(t *testing.T) {
		content := `system:
Test
---
name: Test
---
user:
Test`
		_, err := ParsePromptyContent([]byte(content))
		// Should fail to parse YAML or have wrong structure
		assert.Error(t, err)
	})
}

// Test missing required sections
func TestParsePromptyContentMissingSections(t *testing.T) {
	t.Run("MissingSystemSection", func(t *testing.T) {
		content := `---
name: Test
---

user:
Test prompt
`
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "must contain both 'system:' and 'user:' sections")
	})

	t.Run("MissingUserSection", func(t *testing.T) {
		content := `---
name: Test
---

system:
Test prompt
`
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "must contain both 'system:' and 'user:' sections")
	})

	t.Run("MissingBothSections", func(t *testing.T) {
		content := `---
name: Test
---

This is just plain text
`
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "must contain both 'system:' and 'user:' sections")
	})
}

// Test empty prompty files
func TestParsePromptyContentEmptyFile(t *testing.T) {
	t.Run("CompletelyEmpty", func(t *testing.T) {
		content := ``
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "expected YAML frontmatter")
	})

	t.Run("OnlyWhitespace", func(t *testing.T) {
		content := `   
   
   `
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
	})

	t.Run("OnlyDelimiters", func(t *testing.T) {
		content := `---
---`
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "must contain both 'system:' and 'user:' sections")
	})
}

// Test prompty with only frontmatter (no template)
func TestParsePromptyContentOnlyFrontmatter(t *testing.T) {
	t.Run("NoPromptContent", func(t *testing.T) {
		content := `---
name: Test
description: A test
---`
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "must contain both 'system:' and 'user:' sections")
	})

	t.Run("EmptyPromptContent", func(t *testing.T) {
		content := `---
name: Test
---

`
		_, err := ParsePromptyContent([]byte(content))
		assert.Error(t, err)
	})
}

// Test template variable validation
func TestConvertPromptyToGoTemplate(t *testing.T) {
	t.Run("SimpleVariable", func(t *testing.T) {
		input := "Hello {{name}}"
		expected := "Hello {{.name}}"
		result := convertPromptyToGoTemplate(input)
		assert.Equal(t, expected, result)
	})

	t.Run("MultipleVariables", func(t *testing.T) {
		input := "{{greeting}} {{name}}, your order {{order_id}} is ready"
		expected := "{{.greeting}} {{.name}}, your order {{.order_id}} is ready"
		result := convertPromptyToGoTemplate(input)
		assert.Equal(t, expected, result)
	})

	t.Run("VariableWithWhitespace", func(t *testing.T) {
		input := "{{ name }} and {{  email  }}"
		expected := "{{.name}} and {{.email}}"
		result := convertPromptyToGoTemplate(input)
		assert.Equal(t, expected, result)
	})

	t.Run("AlreadyConvertedVariable", func(t *testing.T) {
		input := "{{.name}}"
		result := convertPromptyToGoTemplate(input)
		// Should not double-convert
		assert.Contains(t, result, ".name")
		assert.NotContains(t, result, "..name")
	})

	t.Run("MixedVariables", func(t *testing.T) {
		input := "{{name}} and {{.already_converted}}"
		result := convertPromptyToGoTemplate(input)
		assert.Contains(t, result, "{{.name}}")
		assert.Contains(t, result, "{{.already_converted}}")
	})

	t.Run("VariableWithUnderscores", func(t *testing.T) {
		input := "{{user_name}} {{email_address}}"
		expected := "{{.user_name}} {{.email_address}}"
		result := convertPromptyToGoTemplate(input)
		assert.Equal(t, expected, result)
	})

	t.Run("VariableWithNumbers", func(t *testing.T) {
		input := "{{user123}} {{item2}}"
		expected := "{{.user123}} {{.item2}}"
		result := convertPromptyToGoTemplate(input)
		assert.Equal(t, expected, result)
	})

	t.Run("NoVariables", func(t *testing.T) {
		input := "This is plain text without variables"
		result := convertPromptyToGoTemplate(input)
		assert.Equal(t, input, result)
	})
}

// Test invalid variable syntax
func TestInvalidVariableSyntax(t *testing.T) {
	t.Run("MissingClosingBrace", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			SystemPrompt: "Hello {{name",
		}
		
		vars := map[string]string{"name": "John"}
		_, err := tmpl.RenderPrompt("system", vars)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "failed to parse prompt template")
	})

	t.Run("MissingOpeningBrace", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			SystemPrompt: "Hello name}}",
		}
		
		vars := map[string]string{"name": "John"}
		rendered, err := tmpl.RenderPrompt("system", vars)
		// Should parse but won't substitute
		require.NoError(t, err)
		assert.Contains(t, rendered, "name}}")
	})

	t.Run("InvalidVariableName", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			SystemPrompt: "Hello {{123invalid}}",
		}
		
		vars := map[string]string{"123invalid": "John"}
		// Should not convert invalid variable names
		rendered, err := tmpl.RenderPrompt("system", vars)
		// May error or leave unconverted
		if err == nil {
			assert.Contains(t, rendered, "{{123invalid}}")
		}
	})
}

// Test RenderPrompt with missing variables
func TestRenderPromptMissingVariables(t *testing.T) {
	t.Run("MissingVariable", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			SystemPrompt: "Hello {{.name}}, your email is {{.email}}",
		}
		
		vars := map[string]string{
			"name": "John",
			// email is missing
		}
		
		rendered, err := tmpl.RenderPrompt("system", vars)
		// Go templates don't error on missing variables, they use <no value>
		assert.NoError(t, err)
		assert.Contains(t, rendered, "John")
		assert.Contains(t, rendered, "<no value>")
	})

	t.Run("EmptyVariableMap", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			SystemPrompt: "Hello {{.name}}",
		}
		
		vars := map[string]string{}
		
		rendered, err := tmpl.RenderPrompt("system", vars)
		// Go templates use <no value> for missing variables
		assert.NoError(t, err)
		assert.Contains(t, rendered, "<no value>")
	})

	t.Run("NilVariableMap", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			SystemPrompt: "Hello {{.name}}",
		}
		
		rendered, err := tmpl.RenderPrompt("system", nil)
		// Nil map is handled by Go templates similar to empty map
		assert.NoError(t, err)
		assert.Contains(t, rendered, "<no value>")
	})
}

// Test RenderPrompt with invalid prompt type
func TestRenderPromptInvalidType(t *testing.T) {
	t.Run("InvalidPromptType", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			SystemPrompt: "System",
			UserPrompt:   "User",
		}
		
		vars := map[string]string{}
		
		_, err := tmpl.RenderPrompt("invalid", vars)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "invalid prompt type")
	})

	t.Run("EmptyPromptType", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			SystemPrompt: "System",
		}
		
		_, err := tmpl.RenderPrompt("", map[string]string{})
		assert.Error(t, err)
	})

	t.Run("WrongCasePromptType", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			SystemPrompt: "System",
		}
		
		// "System" instead of "system"
		_, err := tmpl.RenderPrompt("System", map[string]string{})
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "invalid prompt type")
	})
}

// Test multi-line template handling
func TestMultiLineTemplates(t *testing.T) {
	t.Run("MultiLineSystemPrompt", func(t *testing.T) {
		content := `---
name: Test
---

system:
You are a helpful assistant.
You should be polite.
You must follow these rules:
1. Be clear
2. Be concise

user:
{{.input}}
`
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		
		assert.Contains(t, tmpl.SystemPrompt, "helpful assistant")
		assert.Contains(t, tmpl.SystemPrompt, "Be clear")
		assert.Contains(t, tmpl.SystemPrompt, "Be concise")
	})

	t.Run("MultiLineUserPrompt", func(t *testing.T) {
		content := `---
name: Test
---

system:
Test

user:
Subject: {{.subject}}
From: {{.sender}}
Date: {{.received_time}}

Content:
{{.content}}

Please analyze this email.
`
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		
		assert.Contains(t, tmpl.UserPrompt, "Subject:")
		assert.Contains(t, tmpl.UserPrompt, "{{.subject}}")
		assert.Contains(t, tmpl.UserPrompt, "Please analyze")
	})

	t.Run("TemplateWithBlankLines", func(t *testing.T) {
		content := `---
name: Test
---

system:
Line 1

Line 3 (line 2 is blank)

user:
User prompt

With blank line
`
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		
		assert.Contains(t, tmpl.SystemPrompt, "Line 1")
		assert.Contains(t, tmpl.SystemPrompt, "Line 3")
	})
}

// Test valid prompty structure
func TestValidPromptyStructure(t *testing.T) {
	t.Run("MinimalValidPrompty", func(t *testing.T) {
		content := `---
name: Minimal
---

system:
System prompt

user:
User prompt
`
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		assert.Equal(t, "Minimal", tmpl.Name)
		assert.NotEmpty(t, tmpl.SystemPrompt)
		assert.NotEmpty(t, tmpl.UserPrompt)
	})

	t.Run("CompleteValidPrompty", func(t *testing.T) {
		content := `---
name: Complete Test
description: A complete test prompt
version: 1.0
tags:
  - classification
  - email
model:
  api: chat
  parameters:
    temperature: 0.3
    max_tokens: 500
inputs:
  subject:
    type: string
  sender:
    type: string
  body:
    type: string
  context:
    type: string
outputs:
  category:
    type: string
  confidence:
    type: number
---

system:
You are an email classifier.
Use the context: {{.context}}

user:
Subject: {{.subject}}
From: {{.sender}}
Content: {{.content}}
`
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		
		assert.Equal(t, "Complete Test", tmpl.Name)
		assert.Equal(t, "A complete test prompt", tmpl.Description)
		assert.Equal(t, "1.0", tmpl.Version)
		assert.Len(t, tmpl.Tags, 2)
		assert.Contains(t, tmpl.Tags, "classification")
		assert.Equal(t, "chat", tmpl.Model.API)
		assert.Equal(t, float32(0.3), tmpl.Model.Parameters.Temperature)
		assert.Equal(t, int32(500), tmpl.Model.Parameters.MaxTokens)
		assert.Len(t, tmpl.Inputs, 4)
		assert.NotEmpty(t, tmpl.SystemPrompt)
		assert.NotEmpty(t, tmpl.UserPrompt)
	})
}

// Test edge cases with special characters
func TestSpecialCharactersInTemplate(t *testing.T) {
	t.Run("TemplateWithQuotes", func(t *testing.T) {
		content := `---
name: Test
---

system:
You are "helpful" and 'friendly'

user:
Process "{{.input}}"
`
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		assert.Contains(t, tmpl.SystemPrompt, `"helpful"`)
		assert.Contains(t, tmpl.SystemPrompt, `'friendly'`)
	})

	t.Run("TemplateWithNewlines", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			SystemPrompt: "Line 1\nLine 2\nLine 3",
		}
		
		rendered, err := tmpl.RenderPrompt("system", map[string]string{})
		require.NoError(t, err)
		assert.Contains(t, rendered, "Line 1")
		assert.Contains(t, rendered, "Line 2")
	})

	t.Run("TemplateWithSpecialSymbols", func(t *testing.T) {
		content := `---
name: Test
---

system:
Use symbols: @#$%^&*()

user:
Email: {{.email}}
`
		tmpl, err := ParsePromptyContent([]byte(content))
		require.NoError(t, err)
		assert.Contains(t, tmpl.SystemPrompt, "@#$%^&*()")
	})
}

// Test duplicate variable names
func TestDuplicateVariableNames(t *testing.T) {
	t.Run("SameVariableMultipleTimes", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			UserPrompt: "Hello {{.name}}, welcome {{.name}}!",
		}
		
		vars := map[string]string{"name": "John"}
		rendered, err := tmpl.RenderPrompt("user", vars)
		require.NoError(t, err)
		assert.Equal(t, "Hello John, welcome John!", rendered)
	})

	t.Run("VariableInBothPrompts", func(t *testing.T) {
		tmpl := &PromptyTemplate{
			SystemPrompt: "Context: {{.context}}",
			UserPrompt:   "Use context: {{.context}}",
		}
		
		vars := map[string]string{"context": "test context"}
		
		system, err := tmpl.RenderPrompt("system", vars)
		require.NoError(t, err)
		assert.Contains(t, system, "test context")
		
		user, err := tmpl.RenderPrompt("user", vars)
		require.NoError(t, err)
		assert.Contains(t, user, "test context")
	})
}

func contains(s, substr string) bool {
	return strings.Contains(s, substr)
}

