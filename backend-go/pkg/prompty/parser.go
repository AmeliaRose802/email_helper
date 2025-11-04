package prompty

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"text/template"

	"gopkg.in/yaml.v3"
)

// PromptyTemplate represents a parsed .prompty file
type PromptyTemplate struct {
	Name        string                 `yaml:"name"`
	Description string                 `yaml:"description"`
	Version     string                 `yaml:"version"`
	Tags        []string               `yaml:"tags"`
	Model       PromptyModel           `yaml:"model"`
	Inputs      map[string]PromptyInput `yaml:"inputs"`
	Outputs     map[string]interface{} `yaml:"outputs"`
	
	// The actual prompt content (system and user sections)
	SystemPrompt string
	UserPrompt   string
}

type PromptyModel struct {
	API           string                 `yaml:"api"`
	Configuration map[string]interface{} `yaml:"configuration"`
	Parameters    PromptyParameters      `yaml:"parameters"`
}

type PromptyParameters struct {
	Temperature float32 `yaml:"temperature"`
	MaxTokens   int32   `yaml:"max_tokens"`
}

type PromptyInput struct {
	Type string `yaml:"type"`
}

// ParsePromptyFile reads and parses a .prompty file
func ParsePromptyFile(filepath string) (*PromptyTemplate, error) {
	content, err := os.ReadFile(filepath)
	if err != nil {
		return nil, fmt.Errorf("failed to read prompty file: %w", err)
	}

	return ParsePromptyContent(content)
}

// ParsePromptyContent parses prompty content from bytes
func ParsePromptyContent(content []byte) (*PromptyTemplate, error) {
	// Split on "---" to separate YAML frontmatter from prompt content
	parts := bytes.SplitN(content, []byte("---"), 3)
	
	if len(parts) < 3 {
		return nil, fmt.Errorf("invalid prompty format: expected YAML frontmatter between --- markers")
	}

	// Parse YAML frontmatter (second part, first part is empty before first ---)
	var tmpl PromptyTemplate
	if err := yaml.Unmarshal(parts[1], &tmpl); err != nil {
		return nil, fmt.Errorf("failed to parse YAML frontmatter: %w", err)
	}

	// Parse prompt content (third part)
	promptContent := string(parts[2])
	
	// Split system and user prompts
	systemIdx := strings.Index(promptContent, "system:")
	userIdx := strings.Index(promptContent, "user:")
	
	if systemIdx == -1 || userIdx == -1 {
		return nil, fmt.Errorf("prompty file must contain both 'system:' and 'user:' sections")
	}

	// Extract system prompt (between "system:" and "user:")
	tmpl.SystemPrompt = strings.TrimSpace(promptContent[systemIdx+7 : userIdx])
	
	// Extract user prompt (after "user:")
	tmpl.UserPrompt = strings.TrimSpace(promptContent[userIdx+5:])

	return &tmpl, nil
}

// RenderPrompt fills in template variables with actual values
func (pt *PromptyTemplate) RenderPrompt(promptType string, variables map[string]string) (string, error) {
	var promptTemplate string
	
	switch promptType {
	case "system":
		promptTemplate = pt.SystemPrompt
	case "user":
		promptTemplate = pt.UserPrompt
	default:
		return "", fmt.Errorf("invalid prompt type: %s (must be 'system' or 'user')", promptType)
	}

	// Convert {{variable}} to {{.variable}} for Go templates
	promptTemplate = convertPromptyToGoTemplate(promptTemplate)

	// Use Go's text/template to render the prompt
	tmpl, err := template.New("prompt").Parse(promptTemplate)
	if err != nil {
		return "", fmt.Errorf("failed to parse prompt template: %w", err)
	}

	var buf bytes.Buffer
	if err := tmpl.Execute(&buf, variables); err != nil {
		return "", fmt.Errorf("failed to render prompt template: %w", err)
	}

	return buf.String(), nil
}

// convertPromptyToGoTemplate converts prompty template syntax {{variable}} to Go template syntax {{.variable}}
func convertPromptyToGoTemplate(tmpl string) string {
	// Use regex to find {{variable}} patterns that don't already have a dot
	// This matches {{ followed by optional whitespace, then word characters, then optional whitespace, then }}
	// But only if there's no dot after the opening braces
	re := regexp.MustCompile(`\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}`)
	
	// Replace {{variable}} with {{.variable}}
	return re.ReplaceAllString(tmpl, "{{.$1}}")
}

// LoadPromptDirectory loads all .prompty files from a directory
func LoadPromptDirectory(dirPath string) (map[string]*PromptyTemplate, error) {
	templates := make(map[string]*PromptyTemplate)
	
	files, err := os.ReadDir(dirPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read prompts directory: %w", err)
	}

	for _, file := range files {
		if file.IsDir() || !strings.HasSuffix(file.Name(), ".prompty") {
			continue
		}

		fullPath := filepath.Join(dirPath, file.Name())
		tmpl, err := ParsePromptyFile(fullPath)
		if err != nil {
			// Log warning but continue loading other files
			fmt.Printf("Warning: failed to parse %s: %v\n", file.Name(), err)
			continue
		}

		// Use filename without extension as key
		key := strings.TrimSuffix(file.Name(), ".prompty")
		templates[key] = tmpl
	}

	if len(templates) == 0 {
		return nil, fmt.Errorf("no valid .prompty files found in %s", dirPath)
	}

	return templates, nil
}
