"""Convierte corpus curado y partición sellada a DocBin de spaCy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import spacy
from spacy.tokens import DocBin

from training.corpus import read_jsonl, sha256_bytes


def convert(corpus: Path, split_manifest: Path, destination: Path) -> dict[str, int]:
    records = {row["id"]: row for _, row in read_jsonl(corpus)}
    split = json.loads(split_manifest.read_text(encoding="utf-8"))
    if split["corpus_sha256"] != sha256_bytes(corpus.read_bytes()):
        raise ValueError("El corpus no coincide con el manifiesto de partición sellado")
    nlp = spacy.blank("es")
    counts: dict[str, int] = {}
    for name, ids in split["assignments"].items():
        bin = DocBin(store_user_data=False)
        for record_id in ids:
            row = records[record_id]
            doc = nlp.make_doc(row["text"])
            spans = []
            for start, end, label in row["entities"]:
                span = doc.char_span(start, end, label=label, alignment_mode="strict")
                if span is None:
                    raise ValueError(f"Span no alineado en {record_id}: {(start, end, label)}")
                spans.append(span)
            doc.ents = spans
            bin.add(doc)
        output = destination / f"{name}.spacy"
        output.parent.mkdir(parents=True, exist_ok=True)
        bin.to_disk(output)
        counts[name] = len(ids)
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=Path)
    parser.add_argument("split_manifest", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(json.dumps(convert(**vars(args)), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
