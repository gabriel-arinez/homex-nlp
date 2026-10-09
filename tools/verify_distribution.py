"""Verifica wheel y sdist como los consumirá HOMEX Backend."""

from __future__ import annotations

import hashlib
import os
import subprocess
import tarfile
import tempfile
import tomllib
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
PYTHON_VERSION = "3.11.15"
SOURCE_DATE_EPOCH = "0"
FORBIDDEN_SUFFIXES = {".wav", ".mp3", ".m4a", ".ogg", ".webm"}
FORBIDDEN_NAMES = {".env", "model.bin", "model.safetensors"}


def forbidden_env_name(name: str) -> bool:
    """Rechaza .env y derivados sin bloquear documentación .env.example."""
    lower = name.lower()
    return lower == ".env" or lower.startswith(".env.") and lower != ".env.example"


def project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as source:
        return tomllib.load(source)["project"]["version"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def smoke_script(version: str) -> str:
    return f"""
from importlib.metadata import requires
import sys
import homex_nlp
from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine
assert homex_nlp.__version__ == {version!r}
assert 'faster_whisper' not in sys.modules
request = ExtractionRequest(request_id='backend-distribution-smoke', text='tres muebles, total 100', currency_context='BOB')
result = RulesEngine().extract(request)
assert result.schema_version == '1.0'
assert result.status == 'REQUIRES_REVIEW'
assert result.engine.mode == 'RULES_ONLY'
assert result.item_proposal is not None and result.item_proposal.quantity == 3
assert result.item_proposal.price is not None
assert result.item_proposal.price.mode == 'TOTAL_NEGOCIADO'
assert result.item_proposal.price.line_total == '100.00'
requirements = requires('homex-nlp') or []
assert any("faster-whisper==1.2.1" in item and "extra == 'asr'" in item for item in requirements)
print('backend-consumer-smoke: OK')
"""


def members(artifact: Path) -> list[str]:
    if artifact.suffix == ".whl":
        with ZipFile(artifact) as archive:
            return archive.namelist()
    with tarfile.open(artifact, "r:gz") as archive:
        return archive.getnames()


def check_privacy(artifact: Path) -> None:
    unsafe = []
    for raw in members(artifact):
        path = Path(raw)
        if (\n            path.name.lower() in FORBIDDEN_NAMES\n            or forbidden_env_name(path.name)\n            or path.suffix.lower() in FORBIDDEN_SUFFIXES\n        ):
            unsafe.append(raw)
        if any(
            part.lower() in {"audio", "audio-temporal", "models", "secrets"} for part in path.parts
        ):
            unsafe.append(raw)
    if unsafe:
        raise SystemExit(f"Artefacto contiene archivos privados/pesados: {sorted(set(unsafe))}")


def check_required_sdist(artifact: Path) -> None:
    names = members(artifact)
    required_suffixes = (
        "docs/F10_DESPLIEGUE_RECUPERACION.md",
        "docs/deployment-f10-v0.1.0.json",
    )
    missing = [
        suffix for suffix in required_suffixes if not any(name.endswith(suffix) for name in names)
    ]
    if missing:
        raise SystemExit(f"sdist no incluye evidencia F10: {missing}")


def check_install(artifact: Path, version: str) -> None:
    with tempfile.TemporaryDirectory(prefix="homex-dist-") as temporary:
        env = Path(temporary) / "venv"
        subprocess.run(
            ["uv", "venv", "--no-project", "--python", PYTHON_VERSION, str(env)], check=True
        )
        python = env / "bin" / "python"
        subprocess.run(["uv", "pip", "install", "--python", str(python), str(artifact)], check=True)
        subprocess.run(
            [str(python), "-I", "-B", "-c", smoke_script(version)], cwd=temporary, check=True
        )


def check_reproducible(reference: dict[str, str]) -> None:
    with tempfile.TemporaryDirectory(prefix="homex-rebuild-") as temporary:
        out = Path(temporary)
        env = {**os.environ, "SOURCE_DATE_EPOCH": SOURCE_DATE_EPOCH}
        subprocess.run(["uv", "build", "--out-dir", str(out)], cwd=ROOT, env=env, check=True)
        rebuilt = {
            path.name: digest(path)
            for path in out.iterdir()
            if path.is_file() and (path.suffix == ".whl" or path.name.endswith(".tar.gz"))
        }
    if rebuilt != reference:
        raise SystemExit(f"Build no reproducible: reference={reference}, rebuilt={rebuilt}")


def main() -> int:
    version = project_version()
    dist = ROOT / "dist"
    artifacts = (
        dist / f"homex_nlp-{version}-py3-none-any.whl",
        dist / f"homex_nlp-{version}.tar.gz",
    )
    missing = [path.name for path in artifacts if not path.is_file()]
    if missing:
        raise SystemExit(f"Artefactos de distribución ausentes: {', '.join(missing)}")

    reference = {path.name: digest(path) for path in artifacts}
    for artifact in artifacts:
        check_privacy(artifact)
        if artifact.name.endswith(".tar.gz"):
            check_required_sdist(artifact)
        check_install(artifact, version)
    check_reproducible(reference)

    print(f"Distribución HOMEX NLP {version}: reproducible, privada y backend-ready {reference}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
