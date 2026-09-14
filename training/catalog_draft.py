"""Prepara un borrador comercial de sillas sin inventar SKU, precio o stock."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from training.corpus import read_jsonl


def draft(corpus: Path, destination: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, record in read_jsonl(corpus):
        products = [
            record["text"][start:end]
            for start, end, label in record["entities"]
            if label == "PRODUCTO"
        ]
        rows.append(
            {
                "source_record_id": record["id"],
                "source_line": record["source_line"],
                "name_proposed_from_annotation": products[0] if products else None,
                "sku": None,
                "category": "SILLA",
                "price_bob": None,
                "initial_stock": None,
                "active": False,
                "commercial_review_required": True,
                "missing": ["sku", "presentación/SKU por color", "precio", "existencia inicial"],
            }
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(f"borrador: {len(draft(args.corpus, args.destination))} fichas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
