.PHONY: help dev dev-backend dev-frontend dev-worker db-up db-down migrate seed test test-backend test-worker lint clean

# Default target
help: ## Show this help message
	@echo "Distributed Job Scheduler - Available Commands"
	@echo "==============================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Infrastructure ───────────────────────────────────────────
db-up: ## Start PostgreSQL and Redis containers
	docker compose up -d postgres redis

db-down: ## Stop all containers
	docker compose down

db-reset: ## Reset database (destroy volumes and recreate)
	docker compose down -v
	docker compose up -d postgres redis
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 5
	cd backend && alembic upgrade head

# ── Development ──────────────────────────────────────────────
dev: ## Start all services for development
	$(MAKE) db-up
	@echo "Starting backend, worker, and frontend..."
	$(MAKE) -j3 dev-backend dev-worker dev-frontend

dev-backend: ## Start FastAPI backend in dev mode
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start Next.js frontend in dev mode
	cd frontend && npm run dev

dev-worker: ## Start a single worker instance
	cd worker && python -m app.main

# ── Database Migrations ─────────────────────────────────────
migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="description")
	cd backend && alembic revision --autogenerate -m "$(MSG)"

migrate-rollback: ## Rollback last migration
	cd backend && alembic downgrade -1

# ── Seeding ──────────────────────────────────────────────────
seed: ## Seed database with demo data
	cd backend && python -m app.seed

# ── Testing ──────────────────────────────────────────────────
test: ## Run all tests
	$(MAKE) test-backend
	$(MAKE) test-worker

test-backend: ## Run backend tests
	cd backend && pytest -v --cov=app --cov-report=term-missing

test-worker: ## Run worker tests
	cd worker && pytest -v --cov=app --cov-report=term-missing

# ── Code Quality ─────────────────────────────────────────────
lint: ## Run linters
	cd backend && ruff check . && ruff format --check .
	cd worker && ruff check . && ruff format --check .

format: ## Auto-format code
	cd backend && ruff format .
	cd worker && ruff format .

# ── Cleanup ──────────────────────────────────────────────────
clean: ## Remove generated files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf backend/.coverage backend/htmlcov
	rm -rf worker/.coverage worker/htmlcov
