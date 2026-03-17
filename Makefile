.PHONY: help up down restart logs ps build seed stream ingest-bronze dbt-build dbt-test dbt-docs docs lint typecheck test test-unit test-integration test-data-quality format clean tf-fmt tf-validate tf-plan tf-apply pre-commit-install bundle-validate bundle-deploy bundle-run powerbi-publish

SHELL := /bin/bash
COMPOSE := docker compose
DBT := docker compose run --rm dbt
PY := docker compose run --rm app

help:  ## show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ---------- local dev stack ----------

up:  ## bring up the full local dev stack
	$(COMPOSE) up -d --build
	@echo ""
	@echo "  dbt docs:     http://localhost:8080"
	@echo "  Grafana:      http://localhost:3000  (admin/admin)"
	@echo "  MinIO:        http://localhost:9001  (minioadmin/minioadmin)"
	@echo "  MLflow:       http://localhost:5000"
	@echo "  Prometheus:   http://localhost:9090"
	@echo ""

down:  ## tear down the local stack
	$(COMPOSE) down -v

restart: down up  ## restart the stack

logs:  ## tail logs from all services
	$(COMPOSE) logs -f --tail=100

ps:  ## show running services
	$(COMPOSE) ps

build:  ## rebuild docker images
	$(COMPOSE) build

# ---------- data flow ----------

seed:  ## seed reference data (stations, lines, calendar) into bronze
	$(PY) python -m src.ingestion.seed_reference_data

stream:  ## start the synthetic AFC tap stream generator
	$(PY) python -m src.ingestion.afc_tap_generator

ingest-bronze:  ## run the bronze ingestion job (Auto Loader equivalent locally)
	$(PY) python -m src.ingestion.bronze_ingest

dbt-build:  ## run dbt build (compile + run + test) across silver + gold
	$(DBT) build --profiles-dir /workspace/dbt/profiles --project-dir /workspace/dbt

dbt-test:  ## run only dbt tests
	$(DBT) test --profiles-dir /workspace/dbt/profiles --project-dir /workspace/dbt

dbt-docs:  ## generate and serve dbt docs
	$(DBT) docs generate --profiles-dir /workspace/dbt/profiles --project-dir /workspace/dbt
	$(DBT) docs serve --profiles-dir /workspace/dbt/profiles --project-dir /workspace/dbt --port 8080

# ---------- code quality ----------

lint:  ## run all linters
	ruff check src tests
	mypy --strict src
	sqlfluff lint dbt/models

typecheck:  ## run mypy in strict mode
	mypy --strict src

format:  ## auto-format source
	ruff format src tests
	ruff check --fix src tests
	sqlfluff fix dbt/models || true

test: test-unit test-integration test-data-quality  ## run all tests

test-unit:  ## fast unit tests
	pytest tests/unit -q

test-integration:  ## integration tests against the local docker-compose stack
	pytest tests/integration -q

test-data-quality:  ## great-expectations data-quality suite
	pytest tests/data_quality -q

pre-commit-install:  ## install pre-commit hooks
	pre-commit install --install-hooks
	pre-commit install --hook-type commit-msg

# ---------- terraform ----------

tf-fmt:  ## format terraform
	terraform -chdir=terraform fmt -recursive

tf-validate:  ## validate terraform
	cd terraform/environments/dev && terraform init -backend=false && terraform validate

tf-plan:  ## terraform plan for the dev environment
	cd terraform/environments/dev && terraform plan -out=plan.tfplan

tf-apply:  ## terraform apply for the dev environment
	cd terraform/environments/dev && terraform apply plan.tfplan

# ---------- databricks asset bundles ----------

bundle-validate:  ## validate the databricks asset bundle
	cd databricks && databricks bundle validate

bundle-deploy:  ## deploy the databricks asset bundle to dev
	cd databricks && databricks bundle deploy --target dev

bundle-run:  ## run the bronze_ingest job
	cd databricks && databricks bundle run bronze_ingest --target dev

# ---------- power bi ----------

powerbi-publish:  ## publish the power bi report to the configured service workspace
	python powerbi/deploy/pbi_deploy.py --env $${ENV:-dev}

# ---------- housekeeping ----------

clean:  ## remove caches and build artefacts
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	rm -rf dbt/target dbt/logs dbt/dbt_packages
	rm -rf .coverage htmlcov

docs: dbt-docs  ## generate all docs
