import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_f10_evidence_freezes_versions_and_boundaries() -> None:
    evidence = json.loads((ROOT / "docs/deployment-f10-v0.1.0.json").read_text())

    assert evidence["schema_version"] == "1.0"
    assert evidence["package"] == {
        "name": "homex-nlp",
        "version": "0.1.0",
        "python": "3.11.15",
        "contract": "1.0",
        "mode": "RULES_ONLY",
    }
    assert evidence["backend"]["revision"] == "bc375894036d30cefbc8cdf7c512315aaf1ab971"
    assert evidence["backend"]["wheel_sha256"] == (
        "cfacc3a987f6158f43934cb64304fa50ea3e577cfa576f3db1e6d2a9576d19e6"
    )
    assert evidence["deploy"]["d07_status"] == "PENDING"
    assert evidence["boundaries"]["package_persists_audio"] is False
    assert evidence["boundaries"]["package_downloads_models"] is False
    assert evidence["boundaries"]["hitl_remains_required"] is True
    assert evidence["resource_profile"]["capacity_claim_from_ci_profile"] is False
