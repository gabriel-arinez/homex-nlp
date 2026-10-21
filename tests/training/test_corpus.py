import json
from pathlib import Path

import pytest

from training.audit_prf04 import FAMILIAS
from training.validate_corpus import validate

ROOT = Path(__file__).parents[2]
LABELS = set(json.loads((ROOT / "data/manifests/prf04_labels.json").read_text())["labels"])


@pytest.mark.parametrize("familia,cantidad", zip(FAMILIAS, [380, 101, 97, 97]))
def test_fuentes_activas_validas(familia, cantidad):
    report = validate(ROOT / f"data/corpus/{familia}.jsonl", LABELS, curated=True)
    assert report.valid, report.errors
    assert report.records == cantidad
    assert report.duplicate_texts == 0


def test_particiones_selladas_conservan_familias_y_hashes():
    from training.corpus import sha256_bytes

    familias = {}
    for familia in FAMILIAS:
        path = ROOT / f"data/corpus/{familia}.jsonl"
        manifest = json.loads((ROOT / f"data/splits/{familia}.json").read_text())
        assert manifest["sealed"]
        assert manifest["corpus_sha256"] == sha256_bytes(path.read_bytes())
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        for row in rows:
            assert row["id"] in manifest["assignments"][row["split"]]
            familias.setdefault(row["family_id"], set()).add(row["split"])
    assert all(len(splits) == 1 for splits in familias.values())
