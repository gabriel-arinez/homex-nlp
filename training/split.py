"""Particiones deterministas por familia, con test sellado por defecto."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from training.corpus import json_dump, read_jsonl, sha256_bytes

SPLITS = ("train", "dev", "test")


def family_order(family: str, seed: str) -> str:
    return hashlib.sha256(f"{seed}:{family}".encode()).hexdigest()


def create_splits(
    corpus: Path, destination: Path, *, seed: str, force: bool = False
) -> dict[str, Any]:
    """Escribe el manifiesto una vez; volver a dividir requiere ``force``.

    El bloqueo evita reubicar el conjunto test al observar sus resultados.
    """
    if destination.exists() and not force:
        raise FileExistsError(
            f"{destination} ya existe: el test está sellado; use --force solo para F02"
        )
    rows = [row for _, row in read_jsonl(corpus)]
    by_family: dict[str, list[str]] = {}
    record_labels: dict[str, Counter[str]] = {}
    for row in rows:
        family = row["family_id"]
        by_family.setdefault(family, []).append(row["id"])
        record_labels.setdefault(family, Counter()).update(entity[2] for entity in row["entities"])
    assignments = {name: [] for name in SPLITS}
    # Se reserva test y dev primero. El orden hash es reproducible y las cuotas
    # por registros (no por familias) evitan que 200 cotizaciones queden 86/5/9
    # cuando unas pocas plantillas tienen muchos ejemplos.
    targets = {"test": round(len(rows) * 0.15), "dev": round(len(rows) * 0.15)}
    for family in sorted(by_family, key=lambda value: family_order(value, seed)):
        ids = sorted(by_family[family])
        if len(assignments["test"]) < targets["test"]:
            assigned = "test"
        elif len(assignments["dev"]) < targets["dev"]:
            assigned = "dev"
        else:
            assigned = "train"
        assignments[assigned].extend(ids)
    for ids in assignments.values():
        ids.sort()
    labels: dict[str, Counter[str]] = {name: Counter() for name in SPLITS}
    id_to_family = {record_id: family for family, ids in by_family.items() for record_id in ids}
    for split_name, ids in assignments.items():
        for record_id in ids:
            labels[split_name].update(record_labels[id_to_family[record_id]])
    metadata = {
        "format": "homex-split-v1",
        "corpus": str(corpus),
        "corpus_sha256": sha256_bytes(corpus.read_bytes()),
        "seed": seed,
        "algorithm": "sha256-family-greedy-v1",
        "sealed": True,
        "counts": {name: len(ids) for name, ids in assignments.items()},
        "families": {
            name: len({id_to_family[record_id] for record_id in ids})
            for name, ids in assignments.items()
        },
        "label_counts": {name: dict(sorted(count.items())) for name, count in labels.items()},
        "assignments": assignments,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--seed", default="homex-f02-2026-09-13")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    print(json_dump(create_splits(args.corpus, args.destination, seed=args.seed, force=args.force)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
