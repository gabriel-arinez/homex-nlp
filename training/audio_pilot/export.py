"""Explicit private bridge to the existing PR23 benchmark, not a second scorer."""

import hashlib

from training.benchmark_campo.models import Batch
from training.benchmark_campo.pipeline import read_json

from .dataset import IDS, PilotError
from .runner import load_run


def export_batch(directory, declarations, annotations=None, *, synthetic=False):
    run = load_run(directory)
    expected = "SINTETICO_SOLO_PRUEBA" if synthetic else "PILOTO_REAL_DIAGNOSTICO_CONOCIDO"
    if run["input"]["source_type"] != expected:
        raise PilotError("EXPORT_REQUIRES_REAL_RUN_NOT_SYNTHETIC_FIXTURE")
    if any(r["status"] != "OK" for r in run["records"]):
        raise PilotError("EXPORT_REQUIRES_COMPLETE_ASR_RUN")
    declared = read_json(declarations)
    people = declared["sessions"]
    if len(people) != 20 or sorted(p["id"] for p in people) != list(IDS):
        raise PilotError("EXACT_DECLARATION_MEMBERSHIP_REQUIRED")
    people = {p["id"]: p for p in people}
    references = {}
    if annotations:
        annotated = read_json(annotations)
        if annotated["dataset_digest"] != run["input"]["dataset_digest"]:
            raise PilotError("ANNOTATION_DATASET_MISMATCH")
        entries = annotated["entries"]
        if len(entries) != 20 or sorted(a["id"] for a in entries) != list(IDS):
            raise PilotError("EXACT_ANNOTATION_MEMBERSHIP_REQUIRED")
        hashes = {e["id"]: e["audio_sha256"] for e in run["input"]["entries"]}
        for entry in entries:
            if entry["audio_sha256"] != hashes[entry["id"]]:
                raise PilotError("ANNOTATION_AUDIO_MISMATCH")
            references[entry["id"]] = entry["reference"]
    sessions = []
    for record in run["records"]:
        case = record["id"]
        sessions.append(
            {
                "batch_id": declared["batch_id"],
                "session_id": "AUDIO-" + case,
                "case_id": "PILOTO-" + case,
                "source_type": "SINTETICO_PRUEBA" if synthetic else "ASR_REAL",
                "capture_mode": "synthetic_fixture" if synthetic else "offline_audio",
                "consent": people[case]["consent"],
                "provenance": {
                    "source_id": "WAV-" + case,
                    "template_id": "PILOTO-" + case,
                    "speaker_id": people[case]["speaker_id"],
                    "partition": "PREVIOUSLY_OPEN",
                    "independence": "PENDING",
                },
                "audio": {"private_ref": "AUDIO-" + case, "sha256": record["audio_sha256"]},
                "asr": {
                    "text": record["text"],
                    "sha256": hashlib.sha256(record["text"].encode()).hexdigest(),
                },
                "reference": references.get(case),
                "engines": [],
                "timings": [],
                "temperature": "unknown",
                "hardware_class": "CPU" if run["parameters"]["device"] == "cpu" else "GPU",
                "language": run["parameters"]["language"],
                "condition": "unknown",
            }
        )
    # No gold/consent certification is generated. Existing PR23 review_kit/score
    # verifies the external double-review decisions before any real WER is eligible.
    return Batch.model_validate_json(
        __import__("json").dumps(
            {
                "schema_version": "field-benchmark-1",
                "batch_id": declared["batch_id"],
                "frozen_date": declared["frozen_date"],
                "sessions": sessions,
            }
        )
    ).model_dump(mode="json")
