"""Private offline outputs and aggregate-only comparison; no NLP invocation."""

import hashlib
import math
import os
import platform
import subprocess
import time
from pathlib import Path

from training.benchmark_campo.metrics import stats
from training.benchmark_campo.pipeline import digest, private_path, read_json, write_private

from .asr import Decode, LocalWhisper
from .dataset import IDS, PilotError, validate, validated_audio

ROOT = Path(__file__).resolve().parents[2]


def private_directory(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in [path, *path.parents]):
        raise PilotError("PRIVATE_OUTPUT_SYMLINK")
    private_path(path)
    path.mkdir(parents=True, mode=0o700, exist_ok=False)
    if path.stat().st_mode & 0o077:
        raise PilotError("PRIVATE_OUTPUT_PERMISSIONS")
    return path


def provenance():
    files = sorted(Path(__file__).parent.glob("*.py"))
    return {
        "code_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "code_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)),
        "tool_sources_digest": digest(
            {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        ),
        "uv_lock_sha256": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "system": platform.system(),
        "machine": platform.machine(),
        "cpu": platform.processor(),
        "cpu_count": os.cpu_count(),
        "memory_bytes": os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"),
        "gpu_inventory": "NOT_PROBED_DEVICE_EXPLICIT_IN_CONFIGURATION",
    }


def annotation_template(manifest):
    return {
        "schema_version": "audio-pilot-annotation-1",
        "HUMAN_GOLD": "NO",
        "instruction": "Two human listeners independently transcribe THIS audio; reconcile and attest via benchmark review, never copy planned scripts or ASR",
        "dataset_digest": manifest["dataset_digest"],
        "entries": [
            {"id": e["id"], "audio_sha256": e["audio_sha256"], "reference": None}
            for e in manifest["entries"]
        ],
    }


def quality(run):
    return {k: run[k] for k in ("schema_version", "input", "parameters", "model", "records")}


def summarize_run(run):
    records = run["records"]
    return {
        "schema_version": "audio-pilot-summary-1",
        "source_type": run["input"]["source_type"],
        "status": run["status"],
        "dataset_digest": run["input"]["dataset_digest"],
        "manifest_csv_sha256": run["input"]["manifest_csv_sha256"],
        "quality_digest": digest(quality(run)),
        "configuration_digest": digest(run["parameters"]),
        "model": run["model"],
        "parameters": run["parameters"],
        "audios": len(records),
        "completed": sum(r["status"] == "OK" for r in records),
        "failed": sum(r["status"] == "ERROR" for r in records),
        "asr_seconds": {
            phase: stats(
                [r["seconds"] for r in run["timings"] if phase == "all" or r["phase"] == phase]
            )
            for phase in ("all", "first_inference", "warm")
        },
        "setup_seconds": run["setup_seconds"],
        "model_load_seconds": run["model_load_seconds"],
        "provenance": run["provenance"],
        "HUMAN_GOLD": "NO",
        "WER": "N/A",
        "HOLDOUT_EXTERNO": 0,
        "PROMOCION": "NO",
        "nlp_projection_ux": "NOT_MEASURED",
        "historical_attempts": "20 recordings are NOT a verified 1:1 match to historical 22 attempts",
        "cold_warm_method": "First inference after a new model instance vs later cases; OS cache not controlled; loading separate; not voice E2E",
    }


def evaluate(
    dataset_dir,
    output_dir,
    *,
    execute=False,
    model_dir=None,
    parameters=None,
    synthetic=False,
    factory=LocalWhisper,
):
    if os.environ.get("CI") and not synthetic:
        raise PilotError("REAL_AUDIO_FORBIDDEN_IN_CI")
    manifest = validate(dataset_dir, synthetic=synthetic)
    parameters = parameters or Decode()
    params = parameters.validate()
    output = private_directory(output_dir)
    write_private(output / "validation.json", manifest)
    write_private(output / "annotation-template.json", annotation_template(manifest))
    info = provenance()
    if not execute:
        result = {
            "status": "ASR_NO_EJECUTADO",
            "validated": 20,
            "dataset_digest": manifest["dataset_digest"],
            "HUMAN_GOLD": "NO",
            "WER": "N/A",
            "HOLDOUT_EXTERNO": 0,
            "PROMOCION": "NO",
            "mode": "VALIDATE_ONLY",
        }
        write_private(output / "summary.json", result)
        write_private(output / "provenance.json", info)
        return result
    run = {
        "schema_version": "audio-pilot-run-1",
        "status": "ASR_NO_EJECUTADO",
        "input": manifest,
        "parameters": params,
        "model": None,
        "records": [],
        "timings": [],
        "setup_seconds": None,
        "model_load_seconds": None,
        "provenance": info,
    }
    start = time.perf_counter()
    try:
        engine = factory(model_dir, parameters)
    except Exception as exc:
        code = str(exc) if isinstance(exc, PilotError) else "ASR_SETUP_FAILED"
        run["setup_error"] = code
        write_private(output / "run.json", run)
        write_private(output / "summary.json", summarize_run(run))
        raise PilotError(code) from exc
    run.update(
        model=engine.manifest | {"versions": engine.versions},
        setup_seconds=time.perf_counter() - start,
        model_load_seconds=engine.load_seconds,
        status="ASR_EXECUTED",
    )
    for index, entry in enumerate(manifest["entries"]):
        record = {
            "id": entry["id"],
            "audio_sha256": entry["audio_sha256"],
            "status": "ERROR",
            "text": None,
            "segments": [],
            "error": None,
        }
        try:
            payload = validated_audio(dataset_dir, entry)
            start = time.perf_counter()
            segments = engine.transcribe(payload)
            elapsed = time.perf_counter() - start  # Includes lazy iteration and decoding.
            if any(
                not isinstance(s["text"], str)
                or not all(math.isfinite(s[k]) for k in ("start", "end"))
                or not 0 <= s["start"] <= s["end"]
                for s in segments
            ):
                raise PilotError("INVALID_ASR_SEGMENTS")
            record.update(status="OK", segments=segments, text="".join(s["text"] for s in segments))
            run["timings"].append(
                {
                    "id": entry["id"],
                    "seconds": elapsed,
                    "phase": "first_inference" if index == 0 else "warm",
                }
            )
        except Exception as exc:
            record["error"] = str(exc) if isinstance(exc, PilotError) else "ASR_INFERENCE_FAILED"
        run["records"].append(record)
    if any(r["status"] != "OK" for r in run["records"]):
        run["status"] = "ASR_PARTIAL_FAILURE"
    run["quality_digest"] = digest(quality(run))
    write_private(output / "run.json", run)
    summary = summarize_run(run)
    write_private(output / "summary.json", summary)
    return summary


def load_run(directory):
    directory = Path(directory)
    private_path(directory)
    source = directory / "run.json"
    if source.is_symlink() or source.stat().st_mode & 0o077 or directory.stat().st_mode & 0o077:
        raise PilotError("PRIVATE_RUN_PERMISSIONS")
    run = read_json(source)
    if run.get("schema_version") != "audio-pilot-run-1" or run.get("quality_digest") != digest(
        quality(run)
    ):
        raise PilotError("INVALID_RUN_OR_DIGEST")
    if [r["id"] for r in run["records"]] != list(IDS):
        raise PilotError("EXACT_RUN_MEMBERSHIP_REQUIRED")
    expected = {e["id"]: e["audio_sha256"] for e in run["input"]["entries"]}
    if digest(run["input"]["entries"]) != run["input"]["dataset_digest"] or any(
        r["audio_sha256"] != expected[r["id"]] for r in run["records"]
    ):
        raise PilotError("AUDIO_RUN_BINDING")
    return run


def compare(directories):
    paths = [Path(p).resolve(strict=True) for p in directories]
    if len(paths) < 2 or len(set(paths)) != len(paths):
        raise PilotError("TWO_DISTINCT_RUN_DIRECTORIES_REQUIRED")
    runs = [load_run(p) for p in paths]
    if len({digest(r["input"]) for r in runs}) != 1:
        raise PilotError("COMPARISON_REQUIRES_IDENTICAL_INPUT_MANIFEST")
    return {
        "schema_version": "audio-pilot-comparison-1",
        "runs": [summarize_run(r) for r in runs],
        "HUMAN_GOLD": "NO",
        "WER": "N/A",
        "HOLDOUT_EXTERNO": 0,
        "quality_improvement": "NOT_EVALUABLE_WITHOUT_VERIFIED_FAITHFUL_REFERENCE",
        "independent_processes": "UNVERIFIED_ARTIFACTS_ONLY",
        "PROMOCION": "NO",
    }
