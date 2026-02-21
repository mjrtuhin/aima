.PHONY: help install dev prod down logs test lint format migrate train-all train-1 train-2 train-6 data-download data-prepare clean

PYTHON := python
PIP := pip
DOCKER := docker
COMPOSE := docker compose

help:
	@echo "AIMA Platform - Available Commands"
	@echo ""
	@echo "  Development"
	@echo "    make install        Install Python dependencies"
	@echo "    make dev            Start all services locally with Docker Compose"
	@echo "    make down           Stop all services"
	@echo "    make logs           Tail logs from all services"
	@echo ""
	@echo "  Database"
	@echo "    make migrate        Run Alembic migrations (upgrade to head)"
	@echo "    make migrate-down   Roll back last migration"
	@echo ""
	@echo "  Testing"
	@echo "    make test           Run full test suite with coverage"
	@echo "    make lint           Run ruff linter and mypy type checker"
	@echo "    make format         Auto-format code with ruff"
	@echo ""
	@echo "  Data and Training"
	@echo "    make data-download  Download public benchmark datasets"
	@echo "    make data-prepare   Prepare training sequences from raw data"
	@echo "    make train-1        Train Module 1: Customer Intelligence (TBT)"
	@echo "    make train-2        Train Module 2: Campaign Predictor"
	@echo "    make train-6        Train Module 6: CLV/Churn Predictor"
	@echo "    make train-all      Train all trainable modules sequentially"
	@echo ""
	@echo "  Utilities"
	@echo "    make clean          Remove compiled files and caches"
	@echo "    make dbt-run        Run dbt transformation pipeline"
	@echo "    make dbt-test       Run dbt data quality tests"

install:
	$(PIP) install -e ".[dev]" --break-system-packages

dev:
	$(COMPOSE) up -d
	@echo "Services starting..."
	@echo "  API:      http://localhost:8000"
	@echo "  Frontend: http://localhost:3000"
	@echo "  MLflow:   http://localhost:5000"
	@echo "  MinIO:    http://localhost:9001"
	@echo "  Grafana:  http://localhost:3001"

prod:
	$(COMPOSE) -f docker-compose.yml up -d --scale api=3 --scale worker=4

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=100

migrate:
	alembic upgrade head

migrate-down:
	alembic downgrade -1

migrate-history:
	alembic history --verbose

test:
	pytest tests/ -v --cov=modules --cov=platform --cov-report=term-missing --cov-report=html:coverage_html -x

lint:
	ruff check . --fix
	mypy modules/ platform/ --ignore-missing-imports

format:
	ruff format .

data-download:
	$(PYTHON) scripts/download_datasets.py

data-prepare:
	$(PYTHON) scripts/prepare_training_data.py

train-1:
	$(PYTHON) scripts/train_module1.py --experiment module1-tbt --epochs 50

train-2:
	$(PYTHON) scripts/train_module2.py --experiment module2-campaign --epochs 40

train-6:
	$(PYTHON) scripts/train_module6.py --experiment module6-churn --epochs 60

train-all: data-download data-prepare train-1 train-2 train-6
	@echo "All modules trained successfully."

dbt-run:
	cd data/pipelines && dbt run --profiles-dir .

dbt-test:
	cd data/pipelines && dbt test --profiles-dir .

dbt-docs:
	cd data/pipelines && dbt docs generate --profiles-dir . && dbt docs serve --profiles-dir .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
	find . -type f -name "*.pyc" -delete 2>/dev/null; true
	find . -type f -name "*.pyo" -delete 2>/dev/null; true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null; true
	rm -rf coverage_html .coverage 2>/dev/null; true
	@echo "Cleaned."
