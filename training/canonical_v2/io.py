"""Deterministic UTF-8 serialization and protected artifact paths."""

import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows))


def read(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def table(path, rows):
    rows = list(rows)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        w = csv.DictWriter(f, fieldnames=sorted({k for r in rows for k in r}))
        w.writeheader()
        w.writerows(rows)


def private_path(path):
    path = Path(path).resolve()
    probe = path
    while not probe.exists():
        probe = probe.parent
    if (
        subprocess.run(
            ["git", "-C", str(probe), "rev-parse", "--is-inside-work-tree"], capture_output=True
        ).returncode
        == 0
    ):
        raise ValueError("PRIVATE_ARTIFACT_INSIDE_GIT")
    return path


def protect(path):
    for p in [path, *path.rglob("*")]:
        os.chmod(p, 0o700 if p.is_dir() else 0o600)
