import json
from pathlib import Path

from training.split import create_splits
from training.validate_corpus import validate

ROOT = Path(__file__).parents[2]
LABELS = set(json.loads((ROOT / "data/manifests/source_labels_v1.json").read_text())["labels"])


def test_raw_source_exposes_the_known_technical_errors() -> None:
    report = validate(ROOT / "data/raw/homex_original.jsonl", LABELS, curated=False)
    assert report.records == 200
    assert report.entities == 2378
    assert len(report.errors) == 11
    assert {error["code"] for error in report.errors} == {"TOKEN_ALIGNMENT"}


def test_curated_corpora_are_strictly_valid() -> None:
    commercial = validate(ROOT / "data/curated/homex_original_v1.jsonl", LABELS, curated=True)
    chairs = validate(ROOT / "data/curated/catalogo_sillas_v1.jsonl", LABELS, curated=True)
    assert commercial.valid and commercial.records == 200 and commercial.entities == 2378
    assert chairs.valid and chairs.records == 19 and chairs.entities == 182


def test_changes_preserve_all_records_and_splits_do_not_leak_families(tmp_path: Path) -> None:
    source = [
        json.loads(line)
        for line in (ROOT / "data/raw/homex_original.jsonl").read_text().splitlines()
    ]
    curated = [
        json.loads(line)
        for line in (ROOT / "data/curated/homex_original_v1.jsonl").read_text().splitlines()
    ]
    changes = [
        json.loads(line)
        for line in (ROOT / "data/curated/homex_original_changes.jsonl").read_text().splitlines()
    ]
    assert len(source) == len(curated) == 200
    assert len(changes) == 11
    split = create_splits(
        ROOT / "data/curated/homex_original_v1.jsonl",
        tmp_path / "split.json",
        seed="test",
        force=True,
    )
    assigned = [item for values in split["assignments"].values() for item in values]
    assert len(assigned) == len(set(assigned)) == 200
    assert split["sealed"] is True
