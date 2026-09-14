.PHONY: check lint test build
check: lint test
lint:
	uv run --locked --extra dev ruff check src tests tools
	uv run --locked --extra dev ruff format --check src tests tools
test:
	uv run --locked --extra dev pytest
build:
	uv build
