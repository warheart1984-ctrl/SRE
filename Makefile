# Sovereign Reconstruction Engine — Makefile

.PHONY: install install-api test lint format typecheck run api smoke

install:
	pip install -e ".[dev]"

install-api:
	pip install -e ".[dev,api]"

install-all:
	pip install -e ".[dev,api,postgres]"

test:
	pytest -q

lint:
	ruff check src/ packages/ tests/

format:
	ruff check --fix src/ packages/ tests/ && ruff format src/ packages/ tests/

typecheck:
	mypy src/sre packages/fae

check: lint typecheck test

run:
	python scripts/run_local.py --corpus mythar

api:
	sre-api

smoke:
	python -c "import sre, fae; from sre.substrate import FRAComposedReconstruction; print('ok', sre.__version__)"
