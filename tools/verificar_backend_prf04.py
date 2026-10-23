"""Comprueba el consumo real de homex-nlp 0.1.3 en backend PRF-04.

Independiente del gate histórico F10, que permanece fijado a wheel 0.1.0.
"""

import argparse
import hashlib
import subprocess
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def verificar(backend, revision):
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=backend, text=True).strip()
    if head != revision:
        raise ValueError(f"Checkout backend no coincide: {head} != {revision}")
    proyecto = (backend / "pyproject.toml").read_text()
    lock = (backend / "uv.lock").read_text()
    if '"homex-nlp==0.1.3"' not in proyecto:
        raise ValueError("Backend no fija homex-nlp 0.1.3.")
    if '"faster-whisper==1.2.1"' not in proyecto:
        raise ValueError("Versión ASR de backend no fijada.")
    wheel = backend / "vendor/homex_nlp-0.1.3-py3-none-any.whl"
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    if digest != "673d3291c4b211f280364748e10a10462c0d45e2797f8301a799a299588ff7c9":
        raise ValueError("Hash del wheel PRF-04 incorrecto.")
    if digest not in lock:
        raise ValueError("El digest del wheel no figura en el lock de backend.")
    with ZipFile(wheel) as paquete:
        empaquetados = {
            nombre: paquete.read(nombre)
            for nombre in paquete.namelist()
            if nombre.startswith("homex_nlp/") and nombre.endswith(".py")
        }
    locales = {
        ruta.relative_to(ROOT / "src").as_posix(): ruta.read_bytes()
        for ruta in (ROOT / "src/homex_nlp").rglob("*.py")
    }
    if empaquetados != locales:
        raise ValueError(
            f"Fuente/wheel divergen; fuente={len(locales)}, wheel={len(empaquetados)}."
        )
    adapter = (backend / "apps/capturas/nlp/adapter.py").read_text()
    if 'MODO_OPERATIVO = "RULES_ONLY"' not in adapter:
        raise ValueError("Backend alteró el motor operativo.")
    proyector = (backend / "apps/capturas/proyeccion_prf03.py").read_text()
    if 'VERSION_PROYECCION = "PRF04_2"' not in proyector:
        raise ValueError("Backend no contiene la proyección aprobada.")
    print(f"prf04-backend-nlp-ok backend={head} wheel_sha256={digest}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("backend", type=Path)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    verificar(args.backend.resolve(), args.revision)
