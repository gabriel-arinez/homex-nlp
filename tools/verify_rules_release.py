"""Read-only integrity verification of a private rules release dossier."""

import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    manifest = json.loads((args.evidence / "manifest_sha256.json").read_text())
    failures = []
    for entry in manifest["files"]:
        path = Path(entry["path"])
        if not path.is_absolute():
            path = args.evidence / path
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            failures.append(str(path))
    if failures:
        raise SystemExit("Integrity failure: " + ", ".join(failures))
    report = json.loads((args.evidence / "contratos_integracion.json").read_text())
    assert report["schema_version"] == "1.0"
    assert report["mode"] == "RULES_ONLY"
    assert report["openapi_identical"]
    assert json.loads((args.evidence / "audio_integrity.json").read_text())["status"] == "PASS"
    ci = json.loads((args.evidence / "pruebas_ci.json").read_text())
    assert ci["all_required_success"], "Recorded CI is not complete/successful"
    for filename in ("baseline_v15.json", "resultados_v16.json"):
        rows = json.loads((args.evidence / filename).read_text())["rows"]
        assert len(rows) == 103
        for row in rows:
            result = row["result"]
            assert result["schema_version"] == "1.0"
            text = result["text_original"]
            candidates = {c["candidate_id"]: c for c in result["candidates"]}
            assert len(candidates) == len(result["candidates"])
            item = result["item_proposal"]
            assert result["proposed_item_count"] == int(item is not None)
            components = {c["component_id"] for c in item["components"]} if item else set()
            for c in candidates.values():
                assert text[c["start"] : c["end"]] == c["text"]
                assert c["component_ref"] is None or c["component_ref"] in components
            if item:
                values = (
                    item["dimensions"]
                    + item["thicknesses"]
                    + item["accessories"]
                    + item["components"]
                    + [item["primary_color"], item["secondary_color"], item["price"]]
                )
                for value in filter(None, values):
                    assert all(i in candidates for i in value["evidence_ids"])
                assert all(candidates[i]["decision"] == "UNRESOLVED" for i in item["unresolved"])
    print(
        f"PASS: {len(manifest['files'])} hashes; 206 results; spans/references; contracts; audio; recorded CI."
    )
    print("This verifies integrity and recorded gates; it does not promote the release.")


if __name__ == "__main__":
    main()
