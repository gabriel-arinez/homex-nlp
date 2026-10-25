"""Comprueba el wheel operativo NLP v6 del backend PRF-04 histórico.

El código de trabajo v7 evoluciona sin reescribir la procedencia del wheel 0.1.5.
El futuro wheel v7 requiere una versión y un gate de integración independientes.
"""

import argparse
import hashlib
import subprocess
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
NLP_SOURCE_REVISION = "449a5cf34db2202bdb27aed74c61923ea3176dde"
WHEEL_SHA256 = "ccf0b0d87af865faa51ee23d6857565e26599d3b28a52c3a55193e8c5742965f"


def verificar(backend, revision):
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=backend, text=True).strip()
    if head != revision:
        raise ValueError(f"Checkout backend no coincide: {head} != {revision}")
    proyecto = (backend / "pyproject.toml").read_text()
    lock = (backend / "uv.lock").read_text()
    if '"homex-nlp==0.1.5"' not in proyecto:
        raise ValueError("Backend no fija homex-nlp 0.1.5.")
    if '"faster-whisper==1.2.1"' not in proyecto:
        raise ValueError("Versión ASR de backend no fijada.")
    wheel = backend / "vendor/homex_nlp-0.1.5-py3-none-any.whl"
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    if digest != WHEEL_SHA256 or digest not in lock:
        raise ValueError("La huella del wheel PRF-04 histórico no coincide con el lock.")
    with ZipFile(wheel) as paquete:
        empaquetados = {
            nombre: paquete.read(nombre)
            for nombre in paquete.namelist()
            if nombre.startswith("homex_nlp/") and nombre.endswith(".py")
        }
    rutas_fuente = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", NLP_SOURCE_REVISION, "src/homex_nlp"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    fuente_historica = {
        ruta.removeprefix("src/"): subprocess.check_output(
            ["git", "show", f"{NLP_SOURCE_REVISION}:{ruta}"], cwd=ROOT
        )
        for ruta in rutas_fuente
        if ruta.endswith(".py")
    }
    if empaquetados != fuente_historica:
        raise ValueError(
            "La fuente histórica NLP v6 diverge del wheel 0.1.5: "
            f"fuente={len(fuente_historica)}, wheel={len(empaquetados)}."
        )
    adapter = (backend / "apps/capturas/nlp/adapter.py").read_text()
    if 'MODO_OPERATIVO = "RULES_ONLY"' not in adapter:
        raise ValueError("Backend alteró el motor operativo.")
    proyector = (backend / "apps/capturas/proyeccion_prf03.py").read_text()
    if 'VERSION_PROYECCION = "PRF04_2"' not in proyector:
        raise ValueError("Backend no contiene la proyección aprobada.")
    print(
        f"prf04-backend-nlp-v6-ok backend={head} "
        f"source={NLP_SOURCE_REVISION} wheel_sha256={digest}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("backend", type=Path)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    verificar(args.backend.resolve(), args.revision)
