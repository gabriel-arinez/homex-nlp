"""Instala wheel y sdist en venvs temporales y prueba el import sin editable."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(artifact: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="homex-dist-") as temporary:
        env = Path(temporary) / "venv"
        subprocess.run(["uv", "venv", "--no-project", env], check=True)
        python = env / "bin" / "python"
        subprocess.run(
            ["uv", "pip", "install", "--python", python, "--no-deps", str(artifact)], check=True
        )
        subprocess.run([python, "-c", "import homex_nlp; print(homex_nlp.__version__)"], check=True)


def main() -> int:
    artifacts = sorted((ROOT / "dist").glob("homex_nlp-0.1.0*"))
    if len(artifacts) != 2:
        raise SystemExit("Construya wheel y sdist antes de verificar distribución")
    for artifact in artifacts:
        check(artifact)
    print("Distribución: wheel y sdist instalables sin editable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
