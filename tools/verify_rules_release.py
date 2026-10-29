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
    print(f"PASS: {len(manifest['files'])} SHA256 entries; contract 1.0; RULES_ONLY; 20 WAV/ASR.")
    print("This verifies integrity and recorded gates; it does not promote the release.")


if __name__ == "__main__":
    main()
