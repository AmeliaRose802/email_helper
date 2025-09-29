# Makefile for Email Helper deployment and operations

.PHONY: help build up down restart logs test clean deploy health backup

# Default target
help:
	@echo "Email Helper - Available Commands"
	@echo "=================================="
	@echo "Development:"
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start all services (development)"
	@echo "  make down       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - View logs (all services)"
	@echo "  make test       - Run all tests"
	@echo "  make clean      - Clean up containers and volumes"
	@echo ""
	@echo "Production:"
	@echo "  make prod-up    - Start services (production mode)"
	@echo "  make prod-down  - Stop production services"
	@echo "  make deploy     - Deploy to production"
	@echo ""
	@echo "Maintenance:"
	@echo "  make health     - Run health checks"
	@echo "  make backup     - Backup database"
	@echo "  make restore    - Restore database from backup"
	@echo ""
	@echo "Service-specific:"
	@echo "  make logs-backend   - View backend logs"
	@echo "  make logs-frontend  - View frontend logs"
	@echo "  make shell-backend  - Open backend shell"
	@echo "  make shell-frontend - Open frontend shell"

# Development commands
build:
	@echo "Building Docker images..."
	docker-compose build

up:
	@echo "Starting services in development mode..."
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@make health

down:
	@echo "Stopping all services..."
	docker-compose down

restart:
	@echo "Restarting all services..."
	docker-compose restart

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-worker:
	docker-compose logs -f worker

# Production commands
prod-up:
	@echo "Starting services in production mode..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "Waiting for services to be ready..."
	@sleep 15
	@make health

prod-down:
	@echo "Stopping production services..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

deploy:
	@echo "Deploying to production..."
	@./deployment/scripts/deploy.sh production

# Testing
test: test-backend test-frontend

test-backend:
	@echo "Running backend tests..."
	docker-compose exec backend pytest -v --cov=backend --cov-report=term

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm test

# Health checks
health:
	@echo "Running health checks..."
	@./deployment/scripts/health-check.sh dev

# Database operations
backup:
	@echo "Creating database backup..."
	@mkdir -p backups
	@docker-compose exec -T database pg_dump -U emailhelper email_helper > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup created in backups/"

restore:
	@echo "Restoring database from backup..."
	@read -p "Enter backup filename: " backup; \
	docker-compose exec -T database psql -U emailhelper email_helper < backups/$$backup

# Shell access
shell-backend:
	docker-compose exec backend /bin/bash

shell-frontend:
	docker-compose exec frontend /bin/sh

shell-database:
	docker-compose exec database psql -U emailhelper email_helper

shell-redis:
	docker-compose exec redis redis-cli

# Cleanup
clean:
	@echo "Cleaning up containers and volumes..."
	docker-compose down -v
	@echo "Removing unused Docker images..."
	docker image prune -f

clean-all: clean
	@echo "Removing all Docker images..."
	docker-compose down --rmi all -v

# Development setup
setup:
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then \
		cp .env.docker .env; \
		echo "Created .env file. Please edit it with your configuration."; \
	else \
		echo ".env file already exists."; \
	fi
	@make build
	@make up

# Update dependencies
update-backend:
	@echo "Updating backend dependencies..."
	docker-compose exec backend pip install -r requirements.txt --upgrade

update-frontend:
	@echo "Updating frontend dependencies..."
	cd frontend && npm update

# Linting
lint-backend:
	@echo "Linting backend code..."
	docker-compose exec backend black backend/ --check
	docker-compose exec backend pylint backend/

lint-frontend:
	@echo "Linting frontend code..."
	cd frontend && npm run lint

# Format code
format-backend:
	@echo "Formatting backend code..."
	docker-compose exec backend black backend/

format-frontend:
	@echo "Formatting frontend code..."
	cd frontend && npm run format

# CI/CD
ci:
	@echo "Running CI checks..."
	@make build
	@make test
	@make health

# Quick restart for development
dev-restart: down up
	@echo "Development environment restarted"

# Watch logs
watch:
	docker-compose logs -f backend frontend worker
