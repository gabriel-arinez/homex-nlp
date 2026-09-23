from pathlib import Path

from training.convert_to_docbin import convert

ROOT = Path(__file__).parents[2]


def test_docbin_conversion_respects_the_sealed_split(tmp_path: Path) -> None:
    counts = convert(
        ROOT / "data/curated/homex_original_v1.jsonl",
        ROOT / "data/splits/homex_original_v1.json",
        tmp_path,
    )
    assert counts == {"dev": 30, "test": 32, "train": 138}
    assert {path.name for path in tmp_path.glob("*.spacy")} == {
        "train.spacy",
        "dev.spacy",
        "test.spacy",
    }
