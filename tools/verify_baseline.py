"""Comprueba conservación de los archivos previos a F00, sin ejecutar el prototipo."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Cambios explícitamente requeridos por F00; las otras fuentes se preservan.
AUTHORIZED_CHANGES = {".gitignore", "docs/PLAN_MAESTRO_REFACTORIZACION_HOMEX.md"}


def main() -> int:
    manifest = json.loads((ROOT / "docs/baseline/f00-manifest.json").read_text())
    changed = []
    preserved = 0
    for entry in manifest["files"]:
        path = ROOT / entry["path"]
        if not path.is_file():
            changed.append(f"Ausente: {entry['path']}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest == entry["sha256"]:
            preserved += 1
        elif entry["path"] not in AUTHORIZED_CHANGES:
            changed.append(f"Modificado: {entry['path']}")
    if changed:
        print("\n".join(changed))
        return 1
    print(f"F00 baseline OK: {preserved} archivos intactos; cambios autorizados delimitados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
