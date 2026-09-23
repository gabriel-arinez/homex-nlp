"""Validador estricto de fuentes y copias curadas antes de entrenar."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import spacy

from training.corpus import read_jsonl


@dataclass(frozen=True)
class ValidationReport:
    path: str
    records: int
    entities: int
    labels: dict[str, int]
    errors: list[dict[str, Any]]
    duplicate_texts: int

    @property
    def valid(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "records": self.records,
            "entities": self.entities,
            "labels": self.labels,
            "errors": self.errors,
            "duplicate_texts": self.duplicate_texts,
            "valid": self.valid,
            "tokenizer": {"package": "spacy", "version": spacy.__version__, "language": "es"},
        }


def validate(path: Path, allowed_labels: set[str], *, curated: bool) -> ValidationReport:
    tokenizer = spacy.blank("es")
    errors: list[dict[str, Any]] = []
    label_counts: Counter[str] = Counter()
    text_counts: Counter[str] = Counter()
    records = 0
    entities_count = 0
    for line_number, row in read_jsonl(path):
        records += 1
        text = row.get("text")
        entities = row.get("entities" if curated else "label")
        prefix = {"line": line_number}
        if not isinstance(text, str) or not text:
            errors.append(prefix | {"code": "TEXT", "detail": "text debe ser string no vacío"})
            continue
        if not isinstance(entities, list):
            errors.append(prefix | {"code": "ENTITIES", "detail": "lista de anotaciones requerida"})
            continue
        if curated and row.get("negative_intentional") is not False:
            errors.append(
                prefix | {"code": "NEGATIVE_FLAG", "detail": "negative_intentional debe ser false"}
            )
        text_counts[text] += 1
        doc = tokenizer.make_doc(text)
        previous_end = -1
        seen: set[tuple[int, int, str]] = set()
        for entity in entities:
            entities_count += 1
            if not isinstance(entity, list) or len(entity) != 3:
                errors.append(prefix | {"code": "ENTITY_SHAPE", "detail": repr(entity)})
                continue
            start, end, label = entity
            if type(start) is not int or type(end) is not int or not isinstance(label, str):
                errors.append(prefix | {"code": "ENTITY_TYPE", "detail": repr(entity)})
                continue
            key = (start, end, label)
            if key in seen:
                errors.append(prefix | {"code": "DUPLICATE", "entity": entity})
            seen.add(key)
            if label not in allowed_labels:
                errors.append(prefix | {"code": "LABEL", "entity": entity})
            if not 0 <= start < end <= len(text):
                errors.append(prefix | {"code": "BOUNDS", "entity": entity})
                continue
            if start < previous_end:
                errors.append(prefix | {"code": "OVERLAP", "entity": entity})
            previous_end = max(previous_end, end)
            if doc.char_span(start, end, alignment_mode="strict") is None:
                errors.append(
                    prefix | {"code": "TOKEN_ALIGNMENT", "entity": entity, "slice": text[start:end]}
                )
            label_counts[label] += 1
    return ValidationReport(
        path=str(path),
        records=records,
        entities=entities_count,
        labels=dict(sorted(label_counts.items())),
        errors=errors,
        duplicate_texts=sum(count - 1 for count in text_counts.values() if count > 1),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--curated", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    labels = set(json.loads(args.labels.read_text(encoding="utf-8"))["labels"])
    report = validate(args.path, labels, curated=args.curated)
    serialized = json.dumps(report.as_dict(), ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
