.PHONY: test test-verbose test-coverage test-unit test-integration clean build run

# Run all tests
test:
	go test ./... -v

# Run tests with verbose output
test-verbose:
	go test ./... -v -race

# Run tests with coverage
test-coverage:
	go test ./... -coverprofile=coverage.out
	go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report generated: coverage.html"

# Run only unit tests
test-unit:
	go test -v -short ./internal/models/... ./internal/services/... ./internal/handlers/...

# Run integration tests (tests that require database)
test-integration:
	go test -v -run Integration ./...

# Run specific package tests
test-models:
	go test -v ./internal/models/...

test-services:
	go test -v ./internal/services/...

test-handlers:
	go test -v ./internal/handlers/...

# Clean test artifacts
clean:
	rm -f coverage.out coverage.html
	rm -f /tmp/test_*.db

# Build the application
build:
	go build -o bin/api cmd/api/main.go

# Run the application
run:
	go run cmd/api/main.go

# Install dependencies
deps:
	go mod download
	go mod tidy

# Format code
fmt:
	go fmt ./...

# Run linter
lint:
	go vet ./...

# Generate mocks (if using mockgen)
mocks:
	@echo "Mocks are manually created in internal/mocks/"

# Run all quality checks
check: fmt lint test

# Help
help:
	@echo "Available targets:"
	@echo "  test              - Run all tests"
	@echo "  test-verbose      - Run tests with verbose output and race detector"
	@echo "  test-coverage     - Run tests and generate coverage report"
	@echo "  test-unit         - Run only unit tests"
	@echo "  test-integration  - Run integration tests"
	@echo "  test-models       - Run model tests only"
	@echo "  test-services     - Run service tests only"
	@echo "  test-handlers     - Run handler tests only"
	@echo "  clean             - Remove test artifacts"
	@echo "  build             - Build the application"
	@echo "  run               - Run the application"
	@echo "  deps              - Install dependencies"
	@echo "  fmt               - Format code"
	@echo "  lint              - Run linter"
	@echo "  check             - Run all quality checks (fmt, lint, test)"
