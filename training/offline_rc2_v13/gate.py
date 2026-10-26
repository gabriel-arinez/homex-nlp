"""CI/test gate, never trains or loads a model; explicitly sets offline prohibitions."""

import argparse
import hashlib
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path

from training.benchmark_campo.pipeline import canonical
from training.corpus_v2_rc2.no_training import check_command
from training.offline_rc2_v13.protocol import BASE, ROOT, check_files
from training.offline_rc2_v13.scoring import summarize

ALLOWED = {
    "training/offline_rc2_v13/__init__.py",
    "training/offline_rc2_v13/protocol.py",
    "training/offline_rc2_v13/train.py",
    "training/offline_rc2_v13/worker.py",
    "training/offline_rc2_v13/scoring.py",
    "training/offline_rc2_v13/cli.py",
    "training/offline_rc2_v13/gate.py",
    "training/offline_rc2_v13/config.json",
    "training/offline_rc2_v13/README.md",
    "training/offline_rc2_v13/results.json",
    "tests/training/test_offline_rc2_v13.py",
    "tools/ci_corpus_scope.py",
    ".github/workflows/offline-rc2-v13.yml",
}


def verify():
    check_files()
    paths = subprocess.check_output(["git", "diff", "--name-only", BASE], text=True).splitlines()
    paths += subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"], text=True
    ).splitlines()
    if not set(paths) <= ALLOWED:
        raise ValueError("PRIVATE_WEIGHTS_OR_PROTECTED_PATH_IN_DIFF")
    for name in paths:
        p = ROOT / name
        if p.is_symlink() or p.suffix.lower() in {".whl", ".spacy", ".bin", ".pt", ".wav", ".mp3"}:
            raise ValueError("MODEL_OR_AUDIO_IN_PR")
    fixture = runpy.run_path(str(ROOT / "tests/training/test_offline_rc2_v13.py"))["stub_report"]
    a, b = canonical(summarize(*fixture())), canonical(summarize(*fixture()))
    assert a == b
    assert json.loads(a)["engines"]["B"]["muebles_pedido"]["ner"]["micro"]["tp"] == 1
    aggregate = ROOT / "training/offline_rc2_v13/results.json"
    if aggregate.exists():
        text = aggregate.read_text()
        for forbidden in (
            '"text_original"',
            '"text"',
            '"item_proposal"',
            '"rows"',
            '"training_ids"',
            '"import_path_private"',
        ):
            if forbidden in text:
                raise ValueError("PRIVATE_DETAIL_IN_PUBLIC_REPORT")
        data = json.loads(text)
        assert (
            data["HUMAN_GOLD"] == "NO"
            and data["TEST_VOZ_REAL"] == "NO"
            and data["PROMOCION"] == "NO"
        )
    return hashlib.sha256(a.encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    dest = args.evidence.resolve()
    dest.mkdir(mode=0o700, parents=True, exist_ok=True)
    hook = dest / "guard"
    hook.mkdir(exist_ok=True)
    (hook / "sitecustomize.py").write_text(
        "from training.corpus_v2_rc2.no_training import install\ninstall()\n"
    )
    env = os.environ | {
        "CI": "true",
        "HOMEX_DATA_GATE_NO_TRAINING": "1",
        "PYTHONPATH": str(hook) + os.pathsep + str(ROOT),
    }
    commands = [
        [sys.executable, "-m", "pytest", "-q"],
        [sys.executable, "-m", "ruff", "check", "src", "tests", "tools", "training"],
        [sys.executable, "-m", "ruff", "format", "--check", "src", "tests", "tools", "training"],
        ["git", "diff", "--check"],
    ]
    results = []
    for i, command in enumerate(commands):
        check_command(command)
        with (dest / f"check-{i}.log").open("w") as stream:
            run = subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT)
        results.append({"check": i, "exit_code": run.returncode})
        if run.returncode:
            break
    passed = len(results) == len(commands) and all(r["exit_code"] == 0 for r in results)
    result = {
        "passed": passed,
        "checks": results,
        "fixed_synthetic_report_sha256": verify() if passed else None,
        "training_commands_executed": 0,
        "real_model_loads": 0,
        "HUMAN_GOLD": "NO",
        "TEST_VOZ_REAL": "NO",
    }
    (dest / "result.json").write_text(canonical(result))
    print(json.dumps(result))
    return int(not passed)


if __name__ == "__main__":
    raise SystemExit(main())
