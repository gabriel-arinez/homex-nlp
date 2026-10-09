#!/usr/bin/env python3
"""Verifica que backend F10 consume exactamente el artefacto público NLP esperado."""

from __future__ import annotations

import argparse
import hashlib
import io
import re
import subprocess
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
BACKEND_REVISION = "bc375894036d30cefbc8cdf7c512315aaf1ab971"
WHEEL_PATH = "vendor/homex_nlp-0.1.0-py3-none-any.whl"
WHEEL_SHA256 = "cfacc3a987f6158f43934cb64304fa50ea3e577cfa576f3db1e6d2a9576d19e6"


def git_bytes(repository: Path, revision: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=repository)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("backend", type=Path)
    parser.add_argument("--revision", default=BACKEND_REVISION)
    args = parser.parse_args()
    backend = args.backend.resolve()

    resolved = subprocess.check_output(
        ["git", "rev-parse", args.revision], cwd=backend, text=True
    ).strip()
    if resolved != BACKEND_REVISION:
        raise SystemExit(f"Backend no fijado: esperado={BACKEND_REVISION}, real={resolved}")

    pyproject = git_bytes(backend, resolved, "pyproject.toml").decode()
    lock = git_bytes(backend, resolved, "uv.lock").decode()
    if '"homex-nlp==0.1.0"' not in pyproject or '"faster-whisper==1.2.1"' not in pyproject:
        raise SystemExit("Backend F10 no fija las versiones NLP/ASR esperadas")

    wheel = git_bytes(backend, resolved, WHEEL_PATH)
    digest = hashlib.sha256(wheel).hexdigest()
    if digest != WHEEL_SHA256 or WHEEL_SHA256 not in lock:
        raise SystemExit("El wheel NLP consumido por backend no coincide con uv.lock")

    with ZipFile(io.BytesIO(wheel)) as archive:
        packaged = {
            name: archive.read(name)
            for name in archive.namelist()
            if name.startswith("homex_nlp/") and name.endswith(".py")
        }
    source = {
        path.relative_to(ROOT / "src").as_posix(): path.read_bytes()
        for path in (ROOT / "src/homex_nlp").rglob("*.py")
    }
    if packaged != source:
        missing = sorted(source.keys() - packaged.keys())
        extra = sorted(packaged.keys() - source.keys())
        changed = sorted(
            name for name in source.keys() & packaged.keys() if source[name] != packaged[name]
        )
        raise SystemExit(
            f"Fuente y wheel backend divergen: missing={missing}, extra={extra}, changed={changed}"
        )

    f10 = git_bytes(
        backend, resolved, "docs/implementacion/F10_DESPLIEGUE_RECUPERACION.md"
    ).decode()
    for fragment in ("D07", "audio temporal", "outbox"):
        if not re.search(re.escape(fragment), f10, re.IGNORECASE):
            raise SystemExit(f"Evidencia backend F10 incompleta: falta {fragment}")

    adapter = git_bytes(backend, resolved, "apps/capturas/nlp/adapter.py").decode()
    if 'MODO_OPERATIVO = "RULES_ONLY"' not in adapter:
        raise SystemExit("Backend F10 no conserva RULES_ONLY como modo operativo")

    print(
        "f10-backend-contract-ok "
        f"backend={resolved} package=0.1.0 wheel_sha256={digest} d07_pending=true"
    )


if __name__ == "__main__":
    main()
