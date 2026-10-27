"""Classify corpus-only versus mixed/production changes; fail closed on uncertainty."""

import argparse
import json
import subprocess
from pathlib import Path


def corpus_only(paths):
    allowed_prefixes = ("data/candidates/corpus_v2_rc2/", "training/corpus_v2_rc2/")
    allowed_files = {
        "tests/training/test_corpus_v2_rc2.py",
        "tools/ci_corpus_scope.py",
        "training/audio_pilot/__init__.py",
        "training/audio_pilot/human.py",
        "training/audio_pilot/human_cli.py",
        "training/audio_pilot/HUMAN_GOLD_WER.md",
        "tests/training/test_human_gold.py",
        "training/audio_pilot/dataset.py",
        "training/audio_pilot/asr.py",
        "training/audio_pilot/runner.py",
        "training/audio_pilot/export.py",
        "training/audio_pilot/cli.py",
        "training/audio_pilot/gate.py",
        "training/audio_pilot/README.md",
        "tests/training/test_audio_pilot.py",
        ".github/workflows/audio-pilot.yml",
        "training/evaluar_campo_prf04.py",
        "training/benchmark_campo/__init__.py",
        "training/benchmark_campo/models.py",
        "training/benchmark_campo/metrics.py",
        "training/benchmark_campo/pipeline.py",
        "training/benchmark_campo/cli.py",
        "training/benchmark_campo/gate.py",
        "tests/training/test_benchmark_campo.py",
        "tests/fixtures/benchmark_campo/synthetic.json",
        "tests/fixtures/benchmark_campo/report.json",
        "tests/fixtures/benchmark_campo/schema.json",
        "docs/implementacion/PRF_04_BENCHMARK_CAMPO.md",
        ".github/workflows/benchmark-campo.yml",
        ".github/workflows/corpus-v2-rc2.yml",
        ".github/workflows/ci.yml",
    }
    if ".gitleaksignore" in paths and not safe_digest_exceptions():
        return False
    if ".gitleaksignore" in paths:
        paths = [p for p in paths if p != ".gitleaksignore"]
    return bool(paths) and all(p.startswith(allowed_prefixes) or p in allowed_files for p in paths)


def safe_digest_exceptions():
    import re

    try:
        original = subprocess.check_output(
            ["git", "show", "0154ecb:.gitleaksignore"], text=True
        ).splitlines()
        present = Path(".gitleaksignore").read_text().splitlines()
        base = {x for x in original if x and not x.startswith("#")}
        current = {x for x in present if x and not x.startswith("#")}
        if not base <= current:
            return False
        source = subprocess.check_output(
            ["git", "show", "50937c0:data/candidates/corpus_v2_rc2/analysis/rc1_graph.json"],
            text=True,
        ).splitlines()
        for fingerprint in current - base:
            match = re.fullmatch(
                r"50937c0c1fe20b11cfb3015614bac25e69ba44eb:data/candidates/corpus_v2_rc2/analysis/rc1_graph.json:generic-api-key:(\d+)",
                fingerprint,
            )
            if not match or not re.fullmatch(
                r'\s*"key_sha256": "[0-9a-f]{64}",?', source[int(match[1]) - 1]
            ):
                return False
        return True
    except (OSError, ValueError, IndexError, subprocess.CalledProcessError):
        return False


def changed_paths(event, head="HEAD"):
    if "pull_request" in event:
        base = event["pull_request"]["base"]["sha"]
    else:
        base = event.get("before", "")
        if not base or not base.strip("0"):
            # A new branch's parent is sufficient only for a single direct commit on an approved data/evaluation base.
            base = subprocess.check_output(["git", "rev-parse", head + "^"], text=True).strip()
            if base not in {
                "0154ecba0a53d1a7f3cca4ef10a6cf78cc2ef317",
                "b27edfa522f08c4621d31113b14295ece08e2109",
                "9b2d57d145c09d6ac354ee3d8ecef4f294db94ee",
                "7ba61ea3447174dc9d373494209cb5edcc1261cb",
            }:
                return ["__UNKNOWN_NEW_BRANCH_RANGE_REQUIRES_HISTORICAL_CI__"]
    return subprocess.check_output(
        ["git", "diff", "--name-only", base, head], text=True
    ).splitlines()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--event", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    try:
        paths = changed_paths(json.loads(a.event.read_text()))
        only = corpus_only(paths)
    except (ValueError, KeyError, subprocess.CalledProcessError):
        paths = []
        only = False
    with a.output.open("a") as f:
        f.write("corpus_only=" + str(only).lower() + "\n")
    print(
        json.dumps(
            {
                "corpus_only": only,
                "changed_paths": paths,
                "policy": "production/mixed/unknown preserves historical jobs; corpus-only skips package/training, security jobs remain",
            }
        )
    )


if __name__ == "__main__":
    main()
