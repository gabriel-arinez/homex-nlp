"""Full synthetic regression gate. CI never hydrates LFS or executes actual ASR."""

import argparse
import hashlib
import json
import os
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path

from training.benchmark_campo.pipeline import ROOT, canonical
from training.corpus_v2_rc2.no_training import check_command

from .dataset import validate

BASE = "9b2d57d145c09d6ac354ee3d8ecef4f294db94ee"
ALLOWED = {
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
    "tools/ci_corpus_scope.py",
    ".github/workflows/audio-pilot.yml",
}


def verify():
    paths = subprocess.check_output(["git", "diff", "--name-only", BASE], text=True).splitlines()
    paths += subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"], text=True
    ).splitlines()
    if not set(paths) <= ALLOWED or any((ROOT / name).is_symlink() for name in paths):
        raise ValueError("PROTECTED_PATH_OR_PRIVATE_DATA_IN_PR")
    fixture = runpy.run_path(str(ROOT / "tests/training/test_audio_pilot.py"))["dataset"]
    with tempfile.TemporaryDirectory() as folder:
        root, _ = fixture.__wrapped__(Path(folder))
        first = canonical(validate(root, synthetic=True))
        second = canonical(validate(root, synthetic=True))
    assert first == second
    return hashlib.sha256(first.encode()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", type=Path, required=True)
    args = p.parse_args()
    out = args.evidence.resolve()
    out.mkdir(parents=True, mode=0o700, exist_ok=True)
    guard = out / "guard"
    guard.mkdir(exist_ok=True)
    (guard / "sitecustomize.py").write_text(
        "from training.corpus_v2_rc2.no_training import install\ninstall()\n"
    )
    env = os.environ | {
        "CI": "true",
        "HOMEX_DATA_GATE_NO_TRAINING": "1",
        "HF_HUB_OFFLINE": "1",
        "PYTHONPATH": str(guard) + os.pathsep + str(ROOT),
    }
    checks = []
    for index, command in enumerate(
        [
            [sys.executable, "-m", "pytest", "-q"],
            [sys.executable, "-m", "ruff", "check", "src", "tests", "tools", "training"],
            [
                sys.executable,
                "-m",
                "ruff",
                "format",
                "--check",
                "src",
                "tests",
                "tools",
                "training",
            ],
            ["git", "diff", "--check"],
        ]
    ):
        check_command(command)
        with (out / f"check-{index}.log").open("w") as stream:
            run = subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT)
        checks.append({"index": index, "exit_code": run.returncode})
        if run.returncode:
            break
    passed = len(checks) == 4 and all(x["exit_code"] == 0 for x in checks)
    result = {
        "passed": passed,
        "checks": checks,
        "synthetic_manifest_sha256": verify() if passed else None,
        "training_commands_executed": 0,
        "real_asr_executions": 0,
        "lfs_downloads": 0,
        "HUMAN_GOLD": "NO",
        "WER": "N/A",
        "scope": "SYNTHETIC_TESTS_ONLY",
    }
    (out / "result.json").write_text(canonical(result))
    print(json.dumps(result))
    return int(not passed)


if __name__ == "__main__":
    raise SystemExit(main())
