# Test Runner Script for Email Helper Backend (Go)

## Quick Start

```powershell
# All platforms: Run all tests (no CGO/GCC required!)
go test ./... -v

# Or use the test script (pure Go SQLite, no dependencies)
.\run-tests-with-cgo.ps1 ./...

# Run tests with coverage
go test ./... -coverprofile=coverage.out

# Run specific package tests
go test ./internal/services/... -v
```

**Note**: The project now uses pure Go SQLite (modernc.org/sqlite), so CGO and GCC are no longer required!

## Using Make Commands

```bash
# Run all tests
make test

# Run tests with coverage report
make test-coverage

# Run only unit tests
make test-unit

# Run specific package tests
make test-models
make test-services
make test-handlers

# Clean test artifacts
make clean

# Run all quality checks
make check
```

## Test Organization

### Unit Tests
- **Models** (`internal/models/*_test.go`): Test JSON serialization, validation
- **Services** (`internal/services/*_test.go`): Test business logic with mocked dependencies
- **Handlers** (`internal/handlers/*_test.go`): Test HTTP handlers with mocked services

### Test Utilities
- **Fixtures** (`internal/testutil/fixtures.go`): Helper functions for creating test data
- **Mocks** (`internal/mocks/*_mock.go`): Mock implementations of external dependencies

## Running Individual Tests

```powershell
# Run a specific test function
go test -v ./internal/models -run TestEmailSerialization

# Run tests matching a pattern
go test -v ./internal/services -run TestCreate

# Run tests with race detector
go test -v -race ./...
```

## Coverage Analysis

```powershell
# Generate coverage report
go test ./... -coverprofile=coverage.out

# View coverage in terminal
go tool cover -func=coverage.out

# Generate HTML coverage report
go tool cover -html=coverage.out -o coverage.html

# View coverage by package
go test ./... -coverprofile=coverage.out -covermode=count
go tool cover -func=coverage.out | grep -v "total:" | sort -k 3 -n
```

## Test Environment

**Prerequisites:**
- ✅ **Go 1.21+** - That's it! No C compiler needed!
- ✅ **Pure Go SQLite** - Uses modernc.org/sqlite (no CGO/GCC required)

Tests use temporary SQLite databases that are automatically cleaned up. No external services are required for unit tests.

For integration tests:
- SQLite database created in system temp directory
- Database cleaned up after each test suite
- No Outlook or Azure OpenAI required (tests use mocks)
- Works identically on Windows, Linux, and Mac

### Why No CGO?

The project switched from `github.com/mattn/go-sqlite3` (CGO-based) to `modernc.org/sqlite` (pure Go) for:
- **Simpler setup** - No C compiler installation needed
- **Faster builds** - No CGO compilation overhead
- **Better portability** - Works everywhere Go works
- **Easier CI/CD** - No build tools required in pipelines

## Continuous Integration

Tests can be run in CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run tests
  run: go test -v -race -coverprofile=coverage.out ./...

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.out
```

## Troubleshooting

### Tests Failing with Database Errors
- Ensure no other processes are using test databases
- Clean test artifacts: `make clean` or manually delete `/tmp/test_*.db`

### Import Errors
- Run `go mod tidy` to ensure dependencies are installed
- Verify module path matches: `email-helper-backend`

### Race Detector Warnings
- Run with `-race` flag to detect concurrency issues: `go test -race ./...`
