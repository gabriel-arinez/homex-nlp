#!/usr/bin/env python3
"""Perfil acotado y sin datos sensibles del runtime NLP para F10."""

from __future__ import annotations

import argparse
import json
import resource
import statistics
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import perf_counter, process_time

from homex_nlp.asr import AsrService
from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


class ProfileTranscriber:
    model_version = "f10-profile-double"

    def transcribe(self, path: Path):
        del path
        yield 0.0, 0.5, "texto controlado"


def kib_maxrss() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value)


def timed(callable_):
    wall_start = perf_counter()
    cpu_start = process_time()
    result = callable_()
    return result, {
        "wall_ms": round((perf_counter() - wall_start) * 1000, 3),
        "cpu_ms": round((process_time() - cpu_start) * 1000, 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--iterations", type=int, default=100)
    args = parser.parse_args()
    if not 1 <= args.iterations <= 10_000:
        raise SystemExit("iterations debe estar entre 1 y 10000")

    rss_before = kib_maxrss()
    engine, initialization = timed(RulesEngine)

    durations: list[float] = []

    def extract(index: int) -> str:
        started = perf_counter()
        result = engine.extract(
            ExtractionRequest(
                request_id=f"f10-{index}",
                text="tres muebles, total 100",
                currency_context="BOB",
            )
        )
        durations.append((perf_counter() - started) * 1000)
        return result.engine.mode

    _, extraction_batch = timed(
        lambda: list(ThreadPoolExecutor(max_workers=2).map(extract, range(args.iterations)))
    )

    with tempfile.TemporaryDirectory(prefix="homex-f10-audio-") as temporary:
        root = Path(temporary)
        paths = [root / f"request-{index}.wav" for index in range(2)]
        for path in paths:
            path.write_bytes(b"audio-controlado")

        def transcribe(path: Path) -> int:
            result = AsrService(ProfileTranscriber()).transcribe(path)
            return result.latency_ms

        _, asr_batch = timed(lambda: list(ThreadPoolExecutor(max_workers=2).map(transcribe, paths)))
        audio_remaining = sum(1 for path in root.iterdir() if path.is_file())

    profile = {
        "schema_version": "1.0",
        "package_version": "0.1.0",
        "mode": "RULES_ONLY",
        "profile_kind": "CONTROLLED_DOUBLE",
        "iterations": args.iterations,
        "workers": 2,
        "initialization": initialization,
        "extraction_batch": extraction_batch,
        "extraction_latency_ms": {
            "median": round(statistics.median(durations), 3),
            "max": round(max(durations), 3),
        },
        "asr_two_requests": asr_batch,
        "rss_before_kib": rss_before,
        "rss_after_kib": kib_maxrss(),
        "audio_files_remaining": audio_remaining,
        "contains_transcript_or_audio_path": False,
        "real_model_profile_required_in_d07": True,
    }
    serialized = json.dumps(profile, sort_keys=True, separators=(",", ":"))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)


if __name__ == "__main__":
    main()
