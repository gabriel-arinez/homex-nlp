.PHONY: check lint test schemas corpus-check docbin-check build distribution-check backend-consumer-check f10-check

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

backend-consumer-check:
	uv run --locked --extra dev pytest tests/contract/test_backend_consumer.py -q

SOURCE_DATE_EPOCH ?= 0
BACKEND_F10_PATH ?= ../homex-backend

build:
	SOURCE_DATE_EPOCH=$(SOURCE_DATE_EPOCH) uv build

distribution-check: build
	uv run --locked --extra dev python tools/verify_distribution.py


f10-check:
	uv run --locked --extra dev pytest tests/operations/test_f10_runtime.py -q
	uv run --locked --extra dev python tools/verify_backend_f10.py $(BACKEND_F10_PATH) --revision bc375894036d30cefbc8cdf7c512315aaf1ab971
	uv run --locked --extra dev python tools/profile_f10_runtime.py --iterations 100 --output /tmp/homex-nlp-f10-profile.json
