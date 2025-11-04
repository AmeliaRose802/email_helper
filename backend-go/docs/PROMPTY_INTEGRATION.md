# Prompty Integration in Go Backend

The Go backend now reads prompts from `.prompty` files in the `prompts/` directory instead of using hardcoded prompts.

## How It Works

1. **Parser Package** (`pkg/prompty/parser.go`):
   - Parses `.prompty` files with YAML frontmatter and prompt content
   - Extracts system and user prompt sections
   - Supports template variable substitution using Go's `text/template`
   - Reads model parameters (temperature, max_tokens) from frontmatter

2. **Azure OpenAI Client** (`pkg/azureopenai/client.go`):
   - Loads all `.prompty` files on initialization
   - Uses prompty templates for:
     - `email_classifier_with_explanation.prompty` → Email classification
     - `summerize_action_item.prompty` → Action item extraction
     - `email_one_line_summary.prompty` → Email summarization
   - Falls back to hardcoded prompts if `.prompty` files aren't found
   - Uses temperature and token limits from prompty files

## Prompty Files Used

- **email_classifier_with_explanation.prompty**: Classifies emails into categories with detailed reasoning
- **summerize_action_item.prompty**: Extracts action items and deadlines from emails
- **email_one_line_summary.prompty**: Generates concise one-line email summaries

## Template Variables

The following variables are passed to prompty templates:

- `context`: User-provided context for classification
- `job_role_context`: User's job role (currently hardcoded as "Software Engineer")
- `username`: User's name (currently hardcoded as "User")
- `subject`: Email subject line
- `sender`: Email sender address
- `date`: Email date (or current date for new classifications)
- `body`: Email body content

## Testing

Run prompty integration tests:

```bash
cd backend-go
go test ./pkg/prompty/... -v           # Test prompty parser
go test ./pkg/azureopenai -run TestPrompty -v  # Test prompty integration
```

## Running the Backend

The backend automatically loads `.prompty` files from:
1. `./prompts/` (when running from project root)
2. `../prompts/` (when running from `backend-go/` directory)

Start the server:

```bash
cd backend-go
go run ./cmd/api
```

Or build and run:

```bash
cd backend-go
go build -o bin/email-helper-api ./cmd/api
./bin/email-helper-api
```

## Fallback Behavior

If `.prompty` files cannot be loaded:
- The client logs a warning
- Hardcoded fallback prompts are used (legacy behavior)
- The system continues to function normally

This ensures the backend works even if prompt files are missing or invalid.

## Future Improvements

- Make `username` and `job_role_context` configurable via environment variables or config files
- Add support for custom prompt directories via configuration
- Implement prompt caching/reload without restart
- Add more prompty templates for other email analysis tasks
