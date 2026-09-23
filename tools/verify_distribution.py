"""Verifica wheel y sdist como los consumirá HOMEX Backend."""

from __future__ import annotations

import subprocess
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_VERSION = "3.11.15"


def project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as source:
        return tomllib.load(source)["project"]["version"]


def smoke_script(version: str) -> str:
    return f"""
from importlib.metadata import requires

import homex_nlp
from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine

assert homex_nlp.__version__ == {version!r}

request = ExtractionRequest(
    request_id="backend-distribution-smoke",
    text="tres muebles, total 100",
    currency_context="BOB",
)
result = RulesEngine().extract(request)

assert result.schema_version == "1.0"
assert result.status == "REQUIRES_REVIEW"
assert result.engine.mode == "RULES_ONLY"
assert result.item_proposal is not None
assert result.item_proposal.quantity == 3
assert result.item_proposal.price is not None
assert result.item_proposal.price.mode == "TOTAL_NEGOCIADO"
assert result.item_proposal.price.line_total == "100.00"

requirements = requires("homex-nlp") or []
assert any("faster-whisper==1.2.1" in item and "extra == 'asr'" in item for item in requirements)
print("backend-consumer-smoke: OK")
"""


def check(artifact: Path, version: str) -> None:
    with tempfile.TemporaryDirectory(prefix="homex-dist-") as temporary:
        env = Path(temporary) / "venv"
        subprocess.run(
            ["uv", "venv", "--no-project", "--python", PYTHON_VERSION, str(env)],
            check=True,
        )
        python = env / "bin" / "python"
        subprocess.run(
            ["uv", "pip", "install", "--python", str(python), str(artifact)],
            check=True,
        )
        subprocess.run(
            [str(python), "-I", "-B", "-c", smoke_script(version)],
            cwd=temporary,
            check=True,
        )


def main() -> int:
    version = project_version()
    dist = ROOT / "dist"
    wheel = dist / f"homex_nlp-{version}-py3-none-any.whl"
    sdist = dist / f"homex_nlp-{version}.tar.gz"

    missing = [str(path.name) for path in (wheel, sdist) if not path.is_file()]
    if missing:
        raise SystemExit(f"Artefactos de distribución ausentes: {', '.join(missing)}")

    for artifact in (wheel, sdist):
        check(artifact, version)

    print(f"Distribución HOMEX NLP {version}: wheel y sdist backend-ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
