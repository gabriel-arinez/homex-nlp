.PHONY: check lint test schemas corpus-check build
check: lint schemas corpus-check test
lint:
	uv run --locked --extra dev ruff check src tests tools training
	uv run --locked --extra dev ruff format --check src tests tools training
test:
	uv run --locked --extra dev pytest
schemas:
	uv run --locked --extra dev python tools/export_schemas.py --check
corpus-check:
	uv run --locked --extra dev python -m training.validate_corpus data/curated/homex_original_v1.jsonl --labels data/manifests/source_labels_v1.json --curated
	uv run --locked --extra dev python -m training.validate_corpus data/curated/catalogo_sillas_v1.jsonl --labels data/manifests/source_labels_v1.json --curated
build:
	uv build
