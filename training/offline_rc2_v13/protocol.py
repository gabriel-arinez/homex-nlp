"""Fixed sources, split boundaries and independently installed authentic v13."""

import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import zipfile
from pathlib import Path

from training.benchmark_campo.pipeline import digest, private_path, write_private

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/candidates/corpus_v2_rc2"
BASE = "9b2d57d145c09d6ac354ee3d8ecef4f294db94ee"
V13 = "27aad1f4dc1e29093317a8a5ebf04a730496b325"
WHEEL = "abeee2738b4b6c81d8428e244dddc3cbf0555c06fe00137a6f34d0e1801d4c69"
FAMILIES = ("muebles_pedido", "otros_productos", "pisos_flotantes", "sillas")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def config():
    return json.loads(Path(__file__).with_name("config.json").read_text())


def check_files():
    c = config()
    for name, expected in c["protected_files"].items():
        path = ROOT / name
        if path.is_symlink() or sha(path) != expected:
            raise ValueError("PROTECTED_SOURCE_DIGEST")
    return c


def load_split(split):
    if split not in {"train", "dev"}:
        raise ValueError("ONLY_RC2_DEVELOPMENT_SPLITS")
    check_files()
    rows = []
    for family in FAMILIES:
        path = DATA / "development_v2" / split / (family + ".jsonl")
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if (
                row["split"] != split
                or row["category"] != family
                or row["collection"] != "development_" + split
                or row["human_gold"]
                or row["human_reviewed"]
                or not row["origin"].startswith("SINTETICO")
                or hashlib.sha256(row["text"].encode()).hexdigest() != row["text_sha256"]
            ):
                raise ValueError("UNAUTHORIZED_TRAINING_OR_SPLIT_SOURCE")
            rows.append(row)
    if len(rows) != {"train": 39, "dev": 27}[split] or len({r["id"] for r in rows}) != len(rows):
        raise ValueError("EXACT_SPLIT_MEMBERSHIP")
    return sorted(rows, key=lambda r: r["id"])


def disjoint(train, dev):
    for key in (
        "id",
        "source_case_id",
        "paraphrase_group_id",
        "template_id",
        "leakage_group",
        "text_sha256",
    ):
        if {r[key] for r in train} & {r[key] for r in dev}:
            raise ValueError("CROSS_SPLIT_LEAK")


def references(split):
    check_files()
    result = {}
    for family in FAMILIES:
        for line in (DATA / "expected" / split / (family + ".jsonl")).read_text().splitlines():
            row = json.loads(line)
            if row["human_reviewed"] or row["id"] in result:
                raise ValueError("REFERENCE_PROVENANCE")
            result[row["id"]] = row
    return result


def require_manual(allowed):
    if not allowed or os.environ.get("CI") or os.environ.get("HOMEX_DATA_GATE_NO_TRAINING"):
        raise RuntimeError("EXPLICIT_LOCAL_TRAINING_ONLY_NO_CI")
    if os.environ.get("OMP_NUM_THREADS") != "1" or os.environ.get("OPENBLAS_NUM_THREADS") != "1":
        raise RuntimeError("DECLARED_SINGLE_THREAD_ENV_REQUIRED")


def runtime(wheel):
    if sha(wheel) != WHEEL:
        raise ValueError("NOT_THE_APPROVED_V13_WHEEL")
    import homex_nlp
    from homex_nlp.contracts import ExtractionRequest
    from homex_nlp.engine import RulesEngine

    source = Path(homex_nlp.__file__).resolve().parent
    info = {
        "commit": V13,
        "wheel_sha256": sha(wheel),
        "package_version": importlib.metadata.version("homex-nlp"),
        "rules_version": RulesEngine()
        .extract(ExtractionRequest(request_id="provenance", text="mesa", currency_context="BOB"))
        .engine.rules_version,
    }
    check_runtime(info)
    if source.is_relative_to(ROOT):
        raise ValueError("EDITABLE_BASELINE_IS_NOT_V13")
    with zipfile.ZipFile(wheel) as archive:
        for name in archive.namelist():
            if name.startswith("homex_nlp/") and name.endswith(".py"):
                content = archive.read(name)
                if (source.parent / name).read_bytes() != content:
                    raise ValueError("IMPORTED_CODE_DIFFERS_FROM_WHEEL")
                original = subprocess.check_output(["git", "show", V13 + ":src/" + name], cwd=ROOT)
                if content != original:
                    raise ValueError("WHEEL_DIFFERS_FROM_V13_COMMIT")
    if (
        importlib.metadata.version("spacy") != "3.8.13"
        or importlib.metadata.version("pydantic") != "2.13.4"
    ):
        raise ValueError("LOCKED_RUNTIME_DEPENDENCIES")
    return info | {
        "import_path_private": str(source),
        "python": platform.python_version(),
        "spacy": importlib.metadata.version("spacy"),
        "pydantic": importlib.metadata.version("pydantic"),
    }


def check_runtime(info):
    if any(
        info.get(k) != v
        for k, v in {
            "commit": V13,
            "wheel_sha256": WHEEL,
            "package_version": "0.1.12",
            "rules_version": "prf04-rules-v13",
        }.items()
    ):
        raise ValueError("AUTHENTIC_V13_REQUIRED")


def prepare(wheel, output):
    private_path(output)
    c = check_files()
    from training.corpus_v2_rc2.validate import validate

    validation = validate(DATA)
    if not validation["valid"]:
        raise ValueError("RC2_VALIDATION_FAILED")
    train, dev = load_split("train"), load_split("dev")
    disjoint(train, dev)
    machine = {
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python": sys.version.split()[0],
        "cpu_model": next(
            (
                line.split(":", 1)[1].strip()
                for line in Path("/proc/cpuinfo").read_text().splitlines()
                if line.startswith("model name")
            ),
            "unknown",
        ),
        "ram_kib": int(Path("/proc/meminfo").read_text().splitlines()[0].split()[1]),
    }
    manifest = {
        "rc2_validation": validation,
        "protocol": c,
        "protocol_digest": digest(c),
        "runtime": runtime(wheel),
        "machine": machine,
        "train_ids": [r["id"] for r in train],
        "dev_ids": [r["id"] for r in dev],
        "groups": {
            s: len({r["leakage_group"] for r in rows})
            for s, rows in (("train", train), ("dev", dev))
        },
        "family_counts": {
            s: {f: sum(r["category"] == f for r in rows) for f in FAMILIES}
            for s, rows in (("train", train), ("dev", dev))
        },
        "HUMAN_GOLD": "NO",
        "TEST_VOZ_REAL": "NO",
        "PROMOCION": "NO",
        "HOLDOUT_EXTERNO": 0,
    }
    write_private(output, manifest)
    return manifest


def tree_hash(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob("*")) if p.is_file()}
