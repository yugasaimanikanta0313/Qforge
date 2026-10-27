.PHONY: help dev test lint build-index run-demo clean

PYTHON := venv/Scripts/python.exe
PYTEST := venv/Scripts/pytest.exe

help:
	@echo "QForge Framework — Dev Commands:"
	@echo "  make dev         - Run FastAPI backend with auto-reload"
	@echo "  make test        - Run unit and integration tests"
	@echo "  make lint        - Run code formatting and syntax checks"
	@echo "  make build-index - Rebuild offline FAISS guideline index"
	@echo "  make run-demo    - Run terminal demo pipeline across all phases"

dev:
	$(PYTHON) run.py

test:
	$(PYTEST) tests/unit tests/integration -v

lint:
	$(PYTHON) -m py_compile backend/main.py
	@echo "Python syntax check passed."

build-index:
	$(PYTHON) -m backend.services.vector_store.index_builder

run-demo:
	$(PYTHON) demo_run.py

clean:
	rm -rf .pytest_cache __pycache__ backend/**/__pycache__
