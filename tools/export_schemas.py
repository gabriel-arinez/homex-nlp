"""Genera esquemas v1 deterministas; --check no modifica archivos."""

import argparse
import json
from pathlib import Path

from homex_nlp.contracts import (
    ExtractionRequest,
    ExtractionResult,
    ItemProposal,
    ReviewComparison,
    TranscriptionResult,
)

MODELS = {
    "extraction-request-v1": ExtractionRequest,
    "extraction-result-v1": ExtractionResult,
    "item-proposal-v1": ItemProposal,
    "review-comparison-v1": ReviewComparison,
    "transcription-result-v1": TranscriptionResult,
}
ROOT = Path(__file__).resolve().parents[1]


def schema_text(name: str) -> str:
    # Campos de transporte son strings decimales tanto en entrada como en salida.
    schema = MODELS[name].model_json_schema(mode="validation")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = f"urn:homex:nlp:schema:{name}"
    return json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    mismatches = []
    for name in MODELS:
        path = ROOT / "schemas" / f"{name}.schema.json"
        expected = schema_text(name)
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                mismatches.append(path.name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
    if mismatches:
        print("Esquemas desactualizados: " + ", ".join(mismatches))
        return 1
    print("Esquemas v1: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
