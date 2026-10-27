"""Only data checks and tests. Commands are enumerated; training APIs are blocked."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from training.corpus_v2_rc2.no_training import check_command


def commands(evidence):
    py = sys.executable
    return [
        [py, "-m", "pytest", "-q"],
        [py, "-m", "ruff", "check", "src", "tests", "tools", "training"],
        [py, "-m", "ruff", "format", "--check", "src", "tests", "tools", "training"],
        [py, "tools/export_schemas.py", "--check"],
        [py, "-m", "training.corpus_v2.validate", "data/candidates/corpus_v2_rc1"],
        [py, "-m", "training.corpus_v2_rc2.validate", "data/candidates/corpus_v2_rc2"],
        [py, "-m", "training.corpus_v2_rc2.build", "--output", str(evidence / "rebuild-a")],
        [py, "-m", "training.corpus_v2_rc2.build", "--output", str(evidence / "rebuild-b")],
        [
            py,
            "-m",
            "training.corpus_v2_rc2.docbin",
            "data/candidates/corpus_v2_rc2",
            str(evidence / "docbin"),
        ],
        ["make", "corpus-check", "docbin-check"],
        ["git", "diff", "--check"],
    ]


def tree_hash(root):
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    a = parser.parse_args()
    dest = a.evidence.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    hook = dest / "guard"
    hook.mkdir(exist_ok=True)
    (hook / "sitecustomize.py").write_text(
        "from training.corpus_v2_rc2.no_training import install\ninstall()\n"
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join((str(hook), str(Path.cwd() / "src"), str(Path.cwd())))
    env["HOMEX_DATA_GATE_NO_TRAINING"] = "1"
    results = []
    for i, command in enumerate(commands(dest)):
        check_command(command)
        with (dest / f"command-{i:02d}.log").open("w") as f:
            run = subprocess.run(command, stdout=f, stderr=subprocess.STDOUT, env=env)
        results.append(
            {"command": command, "exit_code": run.returncode, "log": f"command-{i:02d}.log"}
        )
        if run.returncode:
            break
    success = len(results) == len(commands(dest)) and all(r["exit_code"] == 0 for r in results)
    same = success and tree_hash(dest / "rebuild-a") == tree_hash(dest / "rebuild-b") == tree_hash(
        Path("data/candidates/corpus_v2_rc2")
    )
    result = {
        "passed": success and same,
        "commands": results,
        "deterministic": same,
        "training_commands_executed": 0,
        "guard": "subprocess audit hook + spaCy training/weights loading API prohibition",
        "scope": "data/tests only; no training, promotion or model weights",
    }
    (dest / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": result["passed"],
                "commands": len(results),
                "deterministic": same,
                "training_commands_executed": 0,
            }
        )
    )
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
