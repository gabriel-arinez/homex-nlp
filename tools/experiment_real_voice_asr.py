"""Controlled offline ASR experiments; no production setting or source audio edits."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import inspect
import json
import math
import resource
import shutil
import tempfile
import time
import wave
from array import array
from dataclasses import asdict
from pathlib import Path

from tools.evaluate_real_voice import edit_counts, normalized_words


def configurations():
    common = dict(
        language="es",
        beam_size=5,
        temperature=0.0,
        vad_filter=False,
        condition_on_previous_text=False,
        initial_prompt=None,
        hotwords=None,
    )
    return {
        "temperature_zero": {**common, "condition_on_previous_text": True},
        "no_previous": dict(common),
        "vad_no_previous": {
            **common,
            "vad_filter": True,
            "vad_parameters": {"min_silence_duration_ms": 500},
        },
        "wider_beam": {**common, "beam_size": 8},
        "context_no_previous": {
            **common,
            "hotwords": "melamina, MDF, MDP, HDF, PVC, USB, HDMI, tapacantos, bolivianos",
        },
    }


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signal_profile(samples, rate):
    import numpy as np

    x = np.asarray(samples, dtype=np.float64) / 32768.0
    width = max(1, int(rate * 0.02))
    rms = []
    intervals = []
    start = None
    for index in range(0, len(x), width):
        block = x[index : index + width]
        level = float(np.sqrt(np.mean(block * block)))
        rms.append(level)
        if level < 0.01 and start is None:
            start = index / rate
        if level >= 0.01 and start is not None:
            intervals.append([start, index / rate])
            start = None
    if start is not None:
        intervals.append([start, len(x) / rate])
    power = float(np.sqrt(np.mean(x * x))) if len(x) else 0
    peak = float(np.max(np.abs(x))) if len(x) else 0
    return dict(
        duration_seconds=len(x) / rate,
        rms_dbfs=20 * math.log10(max(power, 1e-6)),
        peak_dbfs=20 * math.log10(max(peak, 1e-6)),
        silence_seconds=sum(b - a for a, b in intervals),
        silence_intervals=intervals,
        silence_definition="20ms RMS below -40dBFS; NOT human/VAD adjudication",
        clipped_samples=int(np.sum(np.abs(x) >= 32767 / 32768)),
        clipping_definition="full-scale samples, not proof of audible distortion",
    )


def summary(output):
    groups = {}
    for folder in sorted(output.iterdir()):
        if not folder.is_dir() or not (folder / "cases").is_dir():
            continue
        cases = [json.loads(p.read_text()) for p in (folder / "cases").glob("*.json")]
        per_category = {}
        for category in sorted({r["category"] for r in cases}):
            subset = [r for r in cases if r["category"] == category]
            metrics = {}
            for kind in ["wer", "cer"]:
                valid = [r["metrics"][kind] for r in subset if "metrics" in r]
                n = sum(r["reference_length"] for r in valid)
                errors = sum(r["errors"] for r in valid)
                metrics[kind] = dict(
                    errors=errors, denominator=n, micro_rate=errors / n if n else None
                )
            per_category[category] = dict(
                cases=len(subset), errors=sum("error" in r for r in subset), **metrics
            )
        groups[folder.name] = dict(
            cases=len(cases),
            errors=sum("error" in r for r in cases),
            wall_seconds=sum(r.get("wall_seconds", 0) for r in cases),
            categories=per_category,
        )
    (output / "summary.json").write_text(json.dumps(groups, indent=2) + "\n")
    print(json.dumps(groups), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--configs", nargs="+", choices=list(configurations()), default=list(configurations())
    )
    args = parser.parse_args()
    corpus = args.corpus.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=args.resume)
    refs_file = corpus / "referencias/guiones_referencia_pregrabacion.jsonl"
    refs = [json.loads(line) for line in refs_file.read_text().splitlines()]
    if len(refs) != 120 or len({r["id"] for r in refs}) != 120:
        raise ValueError("Expected120unique IDs")
    frozen = corpus / "evaluaciones/audit-120/baseline-routing-v2/cases"
    from faster_whisper import WhisperModel

    settings = configurations()
    identity = dict(
        model_files={p.name: digest(p) for p in args.model.iterdir() if p.is_file()},
        references_sha256=digest(refs_file),
        configurations={k: settings[k] for k in args.configs},
        versions={
            name: importlib.metadata.version(name)
            for name in ["faster-whisper", "ctranslate2", "numpy"]
        },
        device="cpu",
        compute_type="int8",
        cpu_threads=4,
        num_workers=1,
        runner_sha256=digest(Path(__file__)),
        transcribe_signature=str(inspect.signature(WhisperModel.transcribe)),
        acoustic_verification="PENDING_HUMAN_LISTENING",
        baseline="Frozen original SmallCPU/int8; no replacement or re-decoding",
    )
    path = output / "identity.json"
    if path.exists():
        if json.loads(path.read_text()) != identity:
            raise ValueError("Resume identity mismatch")
    else:
        path.write_text(json.dumps(identity, indent=2) + "\n")
    signal_dir = output / "signals"
    signal_dir.mkdir(exist_ok=args.resume)
    original_audio = {}
    for ref in refs:
        row = json.loads((frozen / (ref["id"] + ".json")).read_text())
        original_audio[ref["id"]] = row["audio"]
        wav = corpus / ref["ruta_audio_compatible_asr"]
        original = corpus / ref["ruta_audio_esperada"]
        if (
            digest(wav) != row["audio"]["wav_sha256"]
            or digest(original) != row["audio"]["original_sha256"]
        ):
            raise ValueError("Audio identity changed")
        target = signal_dir / (ref["id"] + ".json")
        if not target.exists():
            with wave.open(str(wav)) as audio:
                if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) != (
                    1,
                    2,
                    16000,
                ):
                    raise ValueError("WAV contract mismatch")
                samples = array("h", audio.readframes(audio.getnframes()))
            profile = signal_profile(samples, 16000)
            profile.update(
                id=ref["id"],
                original_segments=row["asr"]["segments"],
                wav_sha256=row["audio"]["wav_sha256"],
            )
            target.write_text(json.dumps(profile, indent=2) + "\n")
    begin = time.perf_counter()
    model = WhisperModel(
        str(args.model.resolve()),
        device="cpu",
        compute_type="int8",
        cpu_threads=4,
        num_workers=1,
        local_files_only=True,
    )
    print(f"Model loaded {time.perf_counter() - begin:.3f}s", flush=True)
    categories = {
        "muebles_pedido": "MUEBLE_MEDIDA",
        "sillas": "SILLA",
        "pisos": "PISO_FLOTANTE",
        "OTRO": "OTRO",
    }
    for name in args.configs:
        folder = output / name
        folder.mkdir(exist_ok=args.resume)
        (folder / "cases").mkdir(exist_ok=args.resume)
        for index, ref in enumerate(refs, 1):
            path = folder / "cases" / (ref["id"] + ".json")
            if path.exists():
                old = json.loads(path.read_text())
                if old["audio"] != original_audio[ref["id"]] or old["settings"] != settings[name]:
                    raise ValueError("Case identity mismatch")
                continue
            row = dict(
                id=ref["id"],
                category=categories[ref["categoria"]],
                settings=settings[name],
                audio=original_audio[ref["id"]],
                reference=ref["guion"],
                acoustic_verification="PENDING_HUMAN_LISTENING",
            )
            started = time.perf_counter()
            usage = resource.getrusage(resource.RUSAGE_SELF)
            cpu = usage.ru_utime + usage.ru_stime
            try:
                with tempfile.TemporaryDirectory(prefix="homex-asr-experiment-") as temporary:
                    disposable = Path(temporary) / Path(ref["ruta_audio_compatible_asr"]).name
                    shutil.copyfile(corpus / ref["ruta_audio_compatible_asr"], disposable)
                    segments, info = model.transcribe(str(disposable), **settings[name])
                    row["segments"] = [asdict(segment) for segment in segments]
                    row["text"] = " ".join(
                        s["text"].strip() for s in row["segments"] if s["text"].strip()
                    )
                    row["effective_options"] = asdict(info.transcription_options)
                    row["detected_language"] = info.language
                    row["duration_after_vad"] = info.duration_after_vad
                expected = normalized_words(ref["guion"])
                actual = normalized_words(row["text"])
                row["metrics"] = dict(
                    wer=edit_counts(expected, actual),
                    cer=edit_counts(" ".join(expected), " ".join(actual)),
                )
            except Exception as error:
                import traceback

                row["error"] = dict(
                    type=type(error).__name__, message=str(error), traceback=traceback.format_exc()
                )
            row["wall_seconds"] = time.perf_counter() - started
            usage = resource.getrusage(resource.RUSAGE_SELF)
            row["cpu_seconds"] = usage.ru_utime + usage.ru_stime - cpu
            row["process_peak_rss_kib"] = usage.ru_maxrss
            with path.open("x") as f:
                json.dump(row, f, ensure_ascii=False, indent=2, default=str)
                f.write("\n")
            print(
                f"{name} {index}/120 {ref['id']} {'ERROR' if 'error' in row else 'OK'} {row['wall_seconds']:.2f}s",
                flush=True,
            )
        summary(output)
    for ref in refs:
        if (
            digest(corpus / ref["ruta_audio_esperada"])
            != original_audio[ref["id"]]["original_sha256"]
            or digest(corpus / ref["ruta_audio_compatible_asr"])
            != original_audio[ref["id"]]["wav_sha256"]
        ):
            raise ValueError("Original audio changed")
    print("All240original audio hashes unchanged.", flush=True)


if __name__ == "__main__":
    main()
