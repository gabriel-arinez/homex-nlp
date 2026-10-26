"""No-training gate: full regression, protected trees, privacy and reproducibility."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from training.benchmark_campo.models import Batch
from training.benchmark_campo.pipeline import ROOT, canonical, load, score
from training.corpus_v2_rc2.no_training import check_command


def verify():
    fixture = ROOT / "tests/fixtures/benchmark_campo/synthetic.json"
    batch = load(fixture)
    assert all(s.source_type == "SINTETICO_PRUEBA" for s in batch.sessions)
    first, second = canonical(score(batch)), canonical(score(load(fixture)))
    assert first == second == (fixture.parent / "report.json").read_text()
    assert (
        canonical({"batch": Batch.model_json_schema()})
        == (fixture.parent / "schema.json").read_text()
    )
    # Only the explicit benchmark surface may differ from the approved RC2 commit.
    from tools.ci_corpus_scope import corpus_only

    paths = subprocess.check_output(
        ["git", "diff", "--name-only", "b27edfa522f08c4621d31113b14295ece08e2109"], text=True
    ).splitlines()
    paths += subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"], text=True
    ).splitlines()
    assert corpus_only(paths), "Mixed/protected modifications are not a field-only delivery"
    blocked = (
        "src/",
        "data/",
        "training/corpus_v2",
        "tests/training/test_prf04_evaluar_campo.py",
        "pyproject.toml",
        "uv.lock",
    )
    assert not any(p.startswith(blocked) for p in paths)
    for path in (ROOT / "tests/fixtures/benchmark_campo").iterdir():
        assert path.suffix == ".json" and not path.is_symlink()
        if path.name == "synthetic.json":
            assert '"ASR_REAL"' not in path.read_text()
    return hashlib.sha256(first.encode()).hexdigest()


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
        "PYTHONPATH": str(hook) + os.pathsep + str(ROOT),
        "HOMEX_DATA_GATE_NO_TRAINING": "1",
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
    ok = len(results) == len(commands) and all(r["exit_code"] == 0 for r in results)
    report_hash = verify() if ok else None
    result = {
        "passed": ok,
        "checks": results,
        "deterministic_report_sha256": report_hash,
        "training_commands_executed": 0,
        "HUMAN_GOLD": "NO",
        "real_sessions": 0,
    }
    (dest / "result.json").write_text(canonical(result))
    print(json.dumps(result))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
