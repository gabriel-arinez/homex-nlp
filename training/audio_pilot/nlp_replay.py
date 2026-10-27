"""Offline ASR→NLP pilot replay. No audio inference, backend writes or promotion.

The ASR run comes from PR #26; the NLP engine source must be an isolated
checkout of PR #25 with its exact commit pinned by the operator.
Private text and field-level results never leave the protected output folder.
"""

import argparse
import hashlib
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

from training.benchmark_campo.pipeline import write_private
from training.audio_pilot.dataset import IDS, PilotError
from training.audio_pilot.runner import load_run, private_directory

EXPECTED_NLP_COMMIT = "0e3d8a77ce8ba990114317835055ade038af3e9b"


def _git(directory, *arguments):
    try:
        return subprocess.check_output(
            ["git", "-C", str(directory), *arguments], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise PilotError("NLP_SOURCE_NOT_A_GIT_CHECKOUT") from exc


def _load_engine(source, *, expected_commit):
    source = Path(source).absolute()
    if source.name != "src" or not (source / "homex_nlp" / "engine.py").is_file():
        raise PilotError("NLP_SOURCE_MUST_BE_CHECKOUT_SRC")
    if any(p.is_symlink() for p in (source, *source.parents)):
        raise PilotError("NLP_SOURCE_SYMLINK_REJECTED")
    repository = source.parent
    if _git(repository, "rev-parse", "HEAD") != expected_commit:
        raise PilotError("NLP_SOURCE_COMMIT_MISMATCH")
    if _git(repository, "status", "--porcelain"):
        raise PilotError("NLP_SOURCE_DIRTY")
    if _git(repository, "rev-parse", "--show-toplevel") != str(repository):
        raise PilotError("NLP_SOURCE_NOT_REPOSITORY_ROOT")
    if any(name in sys.modules for name in ("homex_nlp", "homex_nlp.engine")):
        raise PilotError("NLP_ALREADY_IMPORTED")
    sys.path.insert(0, str(source))
    module = importlib.import_module("homex_nlp.engine")
    contracts = importlib.import_module("homex_nlp.contracts")
    if Path(module.__file__).resolve() != source / "homex_nlp" / "engine.py":
        raise PilotError("NLP_IMPORT_SOURCE_MISMATCH")
    return module.RulesEngine(), contracts.ExtractionRequest


def _safe_record(result, case):
    data = result.model_dump(mode="json")
    if data["text_original"] != case["text"]:
        raise PilotError("NLP_TRANSCRIPT_EVIDENCE_MISMATCH")
    if data["status"] not in {"REQUIRES_REVIEW", "NO_PROPOSAL", "ERROR"}:
        raise PilotError("NLP_INVALID_STATUS")
    return {
        "id": case["id"],
        "audio_sha256": case["audio_sha256"],
        "asr_text_sha256": hashlib.sha256(case["text"].encode("utf-8")).hexdigest(),
        "status": data["status"],
        "result": data,
    }


def evaluate_run(run, engine, request_type, *, currency):
    if run.get("status") != "ASR_EXECUTED":
        raise PilotError("ASR_RUN_INCOMPLETE")
    records = run["records"]
    if [r["id"] for r in records] != list(IDS):
        raise PilotError("ASR_RUN_MEMBERSHIP_MISMATCH")
    if any(r["status"] != "OK" or not isinstance(r.get("text"), str) for r in records):
        raise PilotError("ASR_RUN_HAS_ERRORS")
    details = []
    for case in records:
        request = request_type(
            request_id="audio-pilot-" + case["id"],
            text=case["text"],
            currency_context=currency,
        )
        details.append(_safe_record(engine.extract(request), case))
    counts = {
        key: sum(r["status"] == key for r in details)
        for key in ("REQUIRES_REVIEW", "NO_PROPOSAL", "ERROR")
    }
    summary = {
        "schema_version": "audio-pilot-nlp-summary-1",
        "audio_dataset_digest": run["input"]["dataset_digest"],
        "asr_quality_digest": run["quality_digest"],
        "asr_code_commit": run["provenance"]["code_commit"],
        "nlp_commit": EXPECTED_NLP_COMMIT,
        "currency": currency,
        "cases": len(details),
        "statuses": counts,
        "asr_status": "ASR_EXECUTED",
        "nlp_stage": "OFFLINE_REPLAY_NOT_BACKEND_OR_FRONTEND",
        "HUMAN_GOLD": "NO",
        "WER": "N/A",
        "HOLDOUT_EXTERNO": 0,
        "PROMOCION": "NO",
        "historical_attempt_binding": "NOT_VERIFIED",
        "commercial_field_accuracy": "NOT_VALIDATED_WITH_HUMAN_REFERENCE",
    }
    return summary, details


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asr-run-dir", type=Path, required=True)
    parser.add_argument("--nlp-source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--currency", choices=("BOB", "USD"), required=True)
    parser.add_argument("--expected-nlp-commit", default=EXPECTED_NLP_COMMIT)
    options = parser.parse_args(argv)
    try:
        if os.environ.get("CI"):
            raise PilotError("REAL_REPLAY_FORBIDDEN_IN_CI")
        if options.expected_nlp_commit != EXPECTED_NLP_COMMIT:
            raise PilotError("UNREVIEWED_NLP_COMMIT")
        run = load_run(options.asr_run_dir)
        if run["input"]["source_type"] != "PILOTO_REAL_DIAGNOSTICO_CONOCIDO":
            raise PilotError("REAL_PILOT_ASR_RUN_REQUIRED")
        engine, request_type = _load_engine(
            options.nlp_source_dir, expected_commit=options.expected_nlp_commit
        )
        summary, records = evaluate_run(run, engine, request_type, currency=options.currency)
        output = private_directory(options.output_dir)
        write_private(
            output / "details-private.json",
            {"schema_version": "audio-pilot-nlp-details-1", "records": records},
        )
        write_private(output / "summary-private.json", summary)
        print(json.dumps({"ok": True, "cases": len(records), "statuses": summary["statuses"]}))
        return 0
    except Exception as exc:
        code = str(exc) if isinstance(exc, PilotError) else "REPLAY_FAILED"
        print(json.dumps({"ok": False, "error": code}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
