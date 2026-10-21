.PHONY: check lint test schemas corpus-check docbin-check build distribution-check backend-consumer-check f10-check

check: lint schemas corpus-check test

lint:
	uv run --locked --extra dev ruff check src tests tools training
	uv run --locked --extra dev ruff format --check src tests tools training

test:
	uv run --locked --extra dev pytest

schemas:
	uv run --locked --extra dev python tools/export_schemas.py --check

PRF04_FAMILIES = muebles_pedido sillas pisos_flotantes otros_productos

corpus-check:
	@for family in $(PRF04_FAMILIES); do \
	  uv run --locked --extra dev python -m training.validate_corpus data/corpus/$$family.jsonl --labels data/manifests/prf04_labels.json --curated || exit $$?; \
	done
	uv run --locked --extra dev python -m training.audit_prf04 --output /tmp/homex-prf04-inventario.json

docbin-check:
	@for family in $(PRF04_FAMILIES); do \
	  uv run --locked --extra dev python -m training.convert_to_docbin data/corpus/$$family.jsonl data/splits/$$family.json /tmp/homex-docbin-prf04/$$family || exit $$?; \
	done

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
