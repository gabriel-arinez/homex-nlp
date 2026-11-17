"""The live release pointer must describe the package built by current CI."""

import json
from pathlib import Path

import homex_nlp

ROOT = Path(__file__).resolve().parents[2]


def test_current_catalog_release_matches_package_identity():
    release = json.loads((ROOT / "docs/catalog-release.json").read_text())
    assert release["version"] == homex_nlp.__version__
    assert release["wheel"] == f"homex_nlp-{homex_nlp.__version__}-py3-none-any.whl"
    assert release["source_date_epoch"] == 0


def test_previous_published_catalog_manifest_is_retained():
    previous = json.loads((ROOT / "docs/catalog-release-0.1.25.json").read_text())
    assert previous["version"] == "0.1.25"
    assert (
        previous["wheel_sha256"]
        == "9390474a791e357a9d1dd547b6e0e16859f59ac465777ed2ec040e83a2927140"
    )
