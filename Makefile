.PHONY: install dev test test-integration lint clean

install:
	pip install -e .

dev:
	pip install -e ".[dev]"
	pip install Pillow

test:
	pytest tests/unit -v

test-integration:
	pytest tests/integration/ -v -s

lint:
	ruff check src tests

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -name "*.pyc" -delete
