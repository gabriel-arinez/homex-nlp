"""Read-only verification of the final private NLP dossier and published Git freeze."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dossier", type=Path)
    root = parser.parse_args().dossier.resolve()
    manifest = read(root / "manifest_sha256.json")
    for entry in manifest["files"]:
        path = Path(entry["path"])
        if not path.is_absolute():
            path = root / path
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise SystemExit(f"SHA256 mismatch: {path}")
    release = read(root / "versiones_hashes.json")
    assert release["version"] == "0.1.17" and release["rules_version"] == "prf04-rules-final"
    assert release["mode"] == "RULES_ONLY" and release["schema_version"] == "1.0"
    assert read(root / "estado_ci.json")["all_success"]
    freeze = read(root / "git_freeze.json")
    commit = subprocess.check_output(
        ["git", "-C", freeze["source_root"], "rev-parse", freeze["tag"] + "^{commit}"],
        text=True,
    ).strip()
    assert commit == freeze["commit"]
    assert read(root / "integridad_audios.json")["status"] == "PASS"
    for name in ("replay_v15.json", "replay_v16.json", "predicciones_definitivas.json"):
        rows = read(root / name)["rows"]
        assert len(rows) == 103
        for row in rows:
            result = row["result"]
            assert result["schema_version"] == "1.0"
            candidates = {c["candidate_id"]: c for c in result["candidates"]}
            assert len(candidates) == len(result["candidates"])
            item = result["item_proposal"]
            assert result["proposed_item_count"] == int(item is not None)
            components = {c["component_id"] for c in item["components"]} if item else set()
            for c in candidates.values():
                assert result["text_original"][c["start"] : c["end"]] == c["text"]
                assert c["component_ref"] is None or c["component_ref"] in components
            if item:
                values = (
                    item["components"]
                    + item["dimensions"]
                    + item["thicknesses"]
                    + item["accessories"]
                    + [item["price"], item["primary_color"], item["secondary_color"]]
                )
                for value in filter(None, values):
                    assert all(i in candidates for i in value["evidence_ids"])
                assert all(candidates[i]["decision"] == "UNRESOLVED" for i in item["unresolved"])
    print(f"PASS: {len(manifest['files'])} hashes, 309 results, audio, contracts, CI, Git freeze.")
    print("NLP development closed; no deployment or universal language-accuracy claim.")


if __name__ == "__main__":
    main()
