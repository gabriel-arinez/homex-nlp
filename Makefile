.PHONY: check lint test schemas corpus-check docbin-check build distribution-check demo
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
docbin-check:
	uv run --locked --extra dev python -m training.convert_to_docbin data/curated/homex_original_v1.jsonl data/splits/homex_original_v1.json /tmp/homex-docbin-check
build:
	uv build
distribution-check: build
	uv run --locked --extra dev python tools/verify_distribution.py
demo:
	uv run --locked --extra demo --extra asr uvicorn tools.demo_api:app --host 127.0.0.1 --port 8001
