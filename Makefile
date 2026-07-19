# Sovereign Reconstruction Engine — Makefile v0.1
.PHONY: install test lint format run

install:
	@echo "Installing dependencies..."
	pip install -e ".[dev]"

test:
	@echo "Running test suite..."
	pytest -q

lint:
	@echo "Linting codebase..."
	ruff check src/ tests/

format:
	@echo "Formatting codebase..."
	ruff check --fix src/ tests/

run:
	@echo "Running minimal reconstruction demo..."
	@bash scripts/run_local.sh || sh scripts/run_local.sh
