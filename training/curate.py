"""Construye copias curadas y manifiestos a partir de fuentes inmutables."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import spacy

from training.corpus import (
    OFFSET_PATCHES,
    family_id,
    json_dump,
    read_jsonl,
    sha256_bytes,
    sha256_text,
    source_record_id,
)


def curate(
    source_id: str, source: Path, destination: Path, changes: Path, manifest: Path
) -> dict[str, Any]:
    raw = source.read_bytes()
    rows: list[dict[str, Any]] = []
    changes_rows: list[dict[str, Any]] = []
    labels: Counter[str] = Counter()
    for line_number, row in read_jsonl(source):
        text = row["text"]
        original = row["label"]
        entities: list[list[Any]] = []
        for start, end, label in original:
            patch = OFFSET_PATCHES.get((source_id, line_number, start, label))
            new_start, new_end = (start, end) if patch is None else patch[:2]
            entities.append([new_start, new_end, label])
            if patch is not None:
                changes_rows.append(
                    {
                        "id": source_record_id(source_id, line_number, text),
                        "source_id": source_id,
                        "source_line": line_number,
                        "label": label,
                        "before": [start, end, text[start:end]],
                        "after": [new_start, new_end, text[new_start:new_end]],
                        "reason": patch[2],
                        "kind": "OFFSET_TECHNICAL",
                        "review": "F02",
                    }
                )
            labels[label] += 1
        record_id = source_record_id(source_id, line_number, text)
        rows.append(
            {
                "id": record_id,
                "source_id": source_id,
                "source_line": line_number,
                "text": text,
                "text_sha256": sha256_text(text),
                "entities": entities,
                "negative_intentional": False,
                "family_id": family_id(text, entities),
            }
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    changes.parent.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("".join(json_dump(row) + "\n" for row in rows), encoding="utf-8")
    changes.write_text("".join(json_dump(row) + "\n" for row in changes_rows), encoding="utf-8")
    metadata = {
        "format": "homex-corpus-manifest-v1",
        "source_id": source_id,
        "source_file": str(source),
        "source_sha256": sha256_bytes(raw),
        "records": len(rows),
        "entities": sum(labels.values()),
        "labels": dict(sorted(labels.items())),
        "curated_file": str(destination),
        "curated_sha256": sha256_bytes(destination.read_bytes()),
        "changes_file": str(changes),
        "changes": len(changes_rows),
        "tokenizer": {
            "package": "spacy",
            "version": spacy.__version__,
            "language": "es",
            "pipeline": "blank",
        },
        "family_algorithm": "annotated-template-v1",
    }
    manifest.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_id", choices=("homex_original", "catalogo_sillas"))
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("changes", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    print(json.dumps(curate(**vars(args)), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
