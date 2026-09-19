.PHONY: help build up down test lint clean reset-db

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build docker images
	docker-compose build

up: ## Start all services in the background
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## Tail logs of all services
	docker-compose logs -f

test: ## Run tests inside the web container
	docker-compose exec web pytest -v tests/

lint: ## Run code formatters and linters (ruff)
	pip install ruff
	ruff check . --fix
	ruff format .

shell: ## Open a bash shell inside the web container
	docker-compose exec web bash

reset-db: ## Drop all tables and re-run migrations
	docker-compose exec web python -c "from app.core.database import engine; from app.models.base import Base; Base.metadata.drop_all(bind=engine)"
	docker-compose exec web alembic upgrade head
