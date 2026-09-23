"""CONTRACT-02: importar el wheel no inicia infraestructura ni crea archivos."""

import os
import subprocess
import sys
from pathlib import Path


def test_import_is_inert_outside_repository(tmp_path: Path) -> None:
    script = r"""
import importlib.abc
import pathlib
import sys

blocked = {
    "spacy", "pydantic", "faster_whisper", "ctranslate2", "sqlite3",
    "django", "celery", "fastapi", "backend",
}

class ForbidInfrastructure(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in blocked:
            raise AssertionError(f"Importación con efectos externos: {fullname}")
        return None

def guard(event, args):
    if event.startswith("socket.") or event == "subprocess.Popen":
        raise AssertionError(f"Efecto externo al importar: {event}")
    if event == "open":
        mode = args[1]
        if isinstance(mode, str) and any(flag in mode for flag in "wax+"):
            raise AssertionError(f"Escritura al importar: {args[0]}")

sys.meta_path.insert(0, ForbidInfrastructure())
sys.addaudithook(guard)
import homex_nlp
assert homex_nlp.__file__ is not None
assert not blocked.intersection(sys.modules)
assert list(pathlib.Path.cwd().iterdir()) == []
print("CONTRACT-02 OK")
"""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [sys.executable, "-I", "-B", "-c", script],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    assert completed.stdout.strip() == "CONTRACT-02 OK"
    assert completed.stderr == ""
    assert list(tmp_path.iterdir()) == []
