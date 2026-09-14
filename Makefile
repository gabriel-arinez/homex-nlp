.PHONY: check lint test schemas build
check: lint schemas test
lint:
	uv run --locked --extra dev ruff check src tests tools
	uv run --locked --extra dev ruff format --check src tests tools
test:
	uv run --locked --extra dev pytest
schemas:
	uv run --locked --extra dev python tools/export_schemas.py --check
build:
	uv build
