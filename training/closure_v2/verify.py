"""Recompute versioned mechanical artifacts; no training, test scoring or private input."""

import json
from pathlib import Path

from training.closure_v2.audit import audit
from training.closure_v2.curate import build
from training.closure_v2.oral import OralRecord, validate


def main():
    folder = Path("docs/closure_v2")
    current, _ = audit()
    if current["formal_errors"]:
        raise ValueError("BASELINE_INTEGRITY_FAILURE")
    if current != json.loads((folder / "audit.json").read_text()):
        raise ValueError("AUDIT_DRIFT")
    if build() != json.loads((folder / "development_overlay.json").read_text()):
        raise ValueError("OVERLAY_DRIFT")
    if OralRecord.model_json_schema() != json.loads(
        (folder / "oral_intake/record.schema.json").read_text()
    ):
        raise ValueError("ORAL_SCHEMA_DRIFT")
    if (folder / "oral_intake/records.jsonl").read_text():
        raise ValueError("PUBLIC_INTAKE_MUST_REMAIN_EMPTY")
    validate([], set(), {})
    print("PASS: baseline, development overlay, oral schema and empty intake reproduced")


if __name__ == "__main__":
    main()
