PYTHON ?= python3
VENV ?= .venv
ACTIVATE = . $(VENV)/bin/activate

.PHONY: venv install test lint typecheck check run headless doctor

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(ACTIVATE) && python -m pip install -U pip
	$(ACTIVATE) && python -m pip install -e ".[dev]"

test:
	$(ACTIVATE) && pytest -q

lint:
	$(ACTIVATE) && ruff check .

typecheck:
	$(ACTIVATE) && mypy asciipal

check: test lint typecheck

run:
	$(ACTIVATE) && asciipal

headless:
	$(ACTIVATE) && asciipal --headless --max-ticks 40

doctor:
	$(ACTIVATE) && asciipal --doctor

