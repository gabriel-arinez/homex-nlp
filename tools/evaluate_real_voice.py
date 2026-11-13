"""Evaluate immutable real-voice inputs; never interpret paired NLP as gold labels.

Run with ``python -m tools.evaluate_real_voice --help``. Each output directory is
exclusive: completed cases are durable, and --resume verifies input identity.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import resource
import shutil
import subprocess
import tempfile
import time
import unicodedata
import wave
from collections import Counter
from pathlib import Path


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_words(text):
    """Case/punctuation normalization only; retain decimal and code boundaries."""
    return re.findall(r"\w+(?:[.,-]\w+)*", unicodedata.normalize("NFC", text).casefold())


def edit_counts(reference, hypothesis):
    """Levenshtein counts with deterministic substitution/deletion/insertion ties."""
    previous = [(i, 0, 0, i) for i in range(len(hypothesis) + 1)]
    for i, expected in enumerate(reference, 1):
        current = [(i, 0, i, 0)]
        for j, actual in enumerate(hypothesis, 1):
            cost, subs, dels, ins = previous[j - 1]
            diagonal = (cost + (expected != actual), subs + (expected != actual), dels, ins)
            cost, subs, dels, ins = previous[j]
            deletion = (cost + 1, subs, dels + 1, ins)
            cost, subs, dels, ins = current[j - 1]
            insertion = (cost + 1, subs, dels, ins + 1)
            current.append(min((diagonal, deletion, insertion), key=lambda x: x[0]))
        previous = current
    errors, subs, dels, ins = previous[-1]
    return dict(
        errors=errors,
        substitutions=subs,
        deletions=dels,
        insertions=ins,
        reference_length=len(reference),
        rate=errors / len(reference) if reference else None,
    )


def extract(identifier, category, text, values):
    from homex_nlp.catalog import CatalogRequest, extract_catalog
    from homex_nlp.contracts import ExtractionRequest
    from homex_nlp.engine import RulesEngine

    start = time.perf_counter()
    if category == "MUEBLE_MEDIDA":
        result = RulesEngine().extract(
            ExtractionRequest(request_id=identifier, text=text, currency_context="BOB")
        )
    elif text.strip():
        result = extract_catalog(CatalogRequest(category=category, text=text, values=values))
    else:
        return {"error": "EMPTY_TRANSCRIPT", "fields": {}}, 0
    return result.model_dump(mode="json"), (time.perf_counter() - start) * 1000


def git_state(root):
    def run(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()

    return {
        "head": run("rev-parse", "HEAD"),
        "branch": run("branch", "--show-current"),
        "status": run("status", "--short"),
        "diff_sha256": hashlib.sha256(run("diff", "HEAD").encode()).hexdigest(),
    }


def summarize(out):
    rows = [json.loads(p.read_text()) for p in sorted((out / "cases").glob("*.json"))]
    groups = {}
    for category in sorted({r["category"] for r in rows}):
        subset = [r for r in rows if r["category"] == category]
        metrics = {}
        for kind in ("wer", "cer"):
            usable = [r["metrics"][kind] for r in subset if "metrics" in r]
            n = sum(m["reference_length"] for m in usable)
            errors = sum(m["errors"] for m in usable)
            metrics[kind] = {
                "reference_length": n,
                "errors": errors,
                "micro_rate": errors / n if n else None,
            }
        groups[category] = {
            "cases": len(subset),
            "execution_states": dict(Counter(r["execution_state"] for r in subset)),
            **metrics,
        }
    summary = {
        "cases": len(rows),
        "categories": groups,
        "warning": "Script-relative ASR discrepancy, not verified spoken-reference accuracy. "
        "Reference-input NLP is a controlled comparison, NOT independently annotated gold. "
        "All 120 recordings are development data if used to design fixes.",
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument(
        "--values",
        type=Path,
        required=True,
        help="Controlled catalog fixture, not production records",
    )
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    corpus, out = args.corpus.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=args.resume)
    (out / "cases").mkdir(exist_ok=args.resume)
    model = args.model.resolve()
    root = Path(__file__).resolve().parents[1]
    refs_path = corpus / "referencias/guiones_referencia_pregrabacion.jsonl"
    refs = [json.loads(line) for line in refs_path.read_text().splitlines()]
    assert len(refs) == len({r["id"] for r in refs}) == 120
    assert not any(
        out.is_relative_to(corpus / d)
        for d in ("01_muebles_pedido", "02_sillas", "03_pisos", "04_otros")
    )
    versions = {
        n: importlib.metadata.version(n)
        for n in ("homex-nlp", "faster-whisper", "ctranslate2", "pydantic", "spacy")
    }
    identity = {
        "references_sha256": sha256(refs_path),
        "values_sha256": sha256(args.values),
        "model_files": {p.name: sha256(p) for p in sorted(model.iterdir()) if p.is_file()},
        "versions": versions,
        "source_hashes": {
            str(p.relative_to(root)): sha256(p) for p in sorted((root / "src").rglob("*.py"))
        },
        "device": os.getenv("HOMEX_ASR_DEVICE", "cpu"),
        "compute_type": os.getenv("HOMEX_ASR_COMPUTE_TYPE", "int8"),
    }
    identity_path = out / "identity.json"
    if identity_path.exists():
        assert json.loads(identity_path.read_text()) == identity, "Resume identity mismatch"
    else:
        identity_path.write_text(json.dumps(identity, indent=2) + "\n")
    (out / "environment.json").write_text(
        json.dumps(
            {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "repositories": {
                    n: git_state(root.parent / n)
                    for n in ("homex-nlp", "homex-backend", "homex-frontend")
                },
                "asr_parameters": {"language": "es", "others": "faster-whisper 1.2.1 defaults"},
                "reference_review": "PENDING_HUMAN_LISTENING",
            },
            indent=2,
        )
        + "\n"
    )
    from homex_nlp.asr.faster_whisper_adapter import FasterWhisperAdapter
    from homex_nlp.asr.service import AsrService

    started = time.perf_counter()
    service = AsrService(
        FasterWhisperAdapter(
            model, device=identity["device"], compute_type=identity["compute_type"]
        )
    )
    print(f"Model loaded in {time.perf_counter() - started:.3f}s", flush=True)
    values = json.loads(args.values.read_text())
    categories = {
        "muebles_pedido": "MUEBLE_MEDIDA",
        "sillas": "SILLA",
        "pisos": "PISO_FLOTANTE",
        "otros": "OTRO",
        "OTRO": "OTRO",
    }
    for index, ref in enumerate(refs, 1):
        target = out / "cases" / f"{ref['id']}.json"
        original = corpus / ref["ruta_audio_esperada"]
        wav = corpus / ref["ruta_audio_compatible_asr"]
        audio_identity = {
            "original_path": str(original),
            "original_sha256": sha256(original),
            "wav_path": str(wav),
            "wav_sha256": sha256(wav),
        }
        if target.exists():
            assert json.loads(target.read_text())["audio"] == audio_identity
            continue
        category = categories[ref["categoria"]]
        row = {
            "id": ref["id"],
            "category": category,
            "corpus_category": ref["categoria"],
            "audio": audio_identity,
            "reference": ref["guion"],
            "source": ref,
            "versions": versions,
            "reference_review": "PENDING_HUMAN_LISTENING",
            "evaluation_state": "PENDING_FIELD_ANNOTATION",
        }
        begin = time.perf_counter()
        try:
            with wave.open(str(wav)) as audio:
                row["duration_seconds"] = audio.getnframes() / audio.getframerate()
            # The production service deletes its input, never hand it a source path.
            with tempfile.TemporaryDirectory(prefix="homex-eval-") as temporary:
                disposable = Path(temporary) / wav.name
                shutil.copyfile(wav, disposable)
                transcription = service.transcribe(disposable)
                row["asr"] = transcription.model_dump(mode="json")
            text = transcription.text_original
            row["nlp_asr"], row["nlp_asr_ms"] = extract(ref["id"], category, text, values)
            row["nlp_reference"], row["nlp_reference_ms"] = extract(
                ref["id"] + "-ref", category, ref["guion"], values
            )
            expected, actual = normalized_words(ref["guion"]), normalized_words(text)
            row["metrics"] = {
                "wer": edit_counts(expected, actual),
                "cer": edit_counts(" ".join(expected), " ".join(actual)),
            }
            row["execution_state"] = "COMPLETE"
        except Exception as error:
            import traceback

            row["execution_state"] = "ERROR"
            row["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc(),
            }
        row["elapsed_seconds"] = time.perf_counter() - begin
        row["process_peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        assert sha256(original) == audio_identity["original_sha256"]
        assert sha256(wav) == audio_identity["wav_sha256"]
        # Each case is exclusive and flushed; never overwrite baseline evidence.
        with target.open("x") as f:
            json.dump(row, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(
            f"{index}/120 {ref['id']} {category} {row['execution_state']} "
            f"{row['elapsed_seconds']:.2f}s",
            flush=True,
        )
    summarize(out)


if __name__ == "__main__":
    main()
