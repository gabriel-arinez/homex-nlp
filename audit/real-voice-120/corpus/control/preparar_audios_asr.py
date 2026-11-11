#!/usr/bin/env python3
"""Convierte cada AAC identificado en WAV PCM16 mono 16kHz SIN modificar el original.

Invocación:
    python3 control/preparar_audios_asr.py
    python3 control/preparar_audios_asr.py --exigir-completos

Requiere ffmpeg y ffprobe en PATH. No instala dependencias ni consume los originales.
Cada conversión exitosa registra hashes en evaluaciones/conversiones.csv.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import wave
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOLDERS = {"muebles_pedido": "01_muebles_pedido", "sillas": "02_sillas", "pisos": "03_pisos", "otros": "04_otros"}
MAX_BYTES = 20_000_000  # Límite backend observado en config/settings/base.py
MAX_SECONDS = 300        # Límite backend observado (5 minutos)
FIELDS = ["id", "archivo_aac", "sha256_aac", "archivo_wav", "sha256_wav", "duracion_s", "bytes_aac", "bytes_wav"]


def sha256(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def valid_wav(path: Path) -> float:
    if not path.is_file() or path.is_symlink() or not 0 < path.stat().st_size <= MAX_BYTES:
        raise ValueError("WAV vacío, inseguro o superior a 20 MB")
    with wave.open(str(path), "rb") as wav:
        if wav.getnchannels() != 1 or wav.getsampwidth() != 2 or wav.getframerate() != 16000:
            raise ValueError("WAV no cumple el contrato mono PCM16 16 kHz")
        duration = wav.getnframes() / wav.getframerate()
        if not 0 < duration <= MAX_SECONDS:
            raise ValueError(f"duración {duration:.2f}s fuera de 0–{MAX_SECONDS}s")
        return duration


def validate_aac(path: Path) -> None:
    if not path.is_file() or path.is_symlink() or not 0 < path.stat().st_size <= MAX_BYTES:
        raise ValueError("AAC vacío, inseguro o superior a 20 MB")
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name", "-of", "json", str(path)],
        capture_output=True, text=True, check=False,
    )
    if p.returncode != 0:
        raise ValueError("AAC no decodificable: " + p.stderr.strip()[:220])
    streams = json.loads(p.stdout or "{}").get("streams", [])
    if not streams or streams[0].get("codec_name") != "aac":
        raise ValueError("el contenido de archivo .aac no utiliza el códec AAC")


def load_existing(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    if any(set(row) != set(FIELDS) for row in rows):
        raise ValueError(f"Formato de auditoría inesperado: {path}")
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError("IDs duplicados en el registro de conversiones")
    return {row["id"]: row for row in rows}


def write_audit(path: Path, audit: dict[str, dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(prefix=".conversiones-", suffix=".csv", dir=str(path.parent))
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as f:
            out = csv.DictWriter(f, fieldnames=FIELDS, delimiter=";", lineterminator="\n")
            out.writeheader()
            out.writerows(audit[rid] for rid in sorted(audit))
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def main() -> int:
    ap = argparse.ArgumentParser(description="Prepara WAV compatibles con HOMEX ASR a partir de los AAC originales.")
    ap.add_argument("--exigir-completos", action="store_true", help="Fallar si faltan grabaciones AAC.")
    args = ap.parse_args()
    for binary in ("ffmpeg", "ffprobe"):
        if not shutil.which(binary):
            print(f"ERROR: falta {binary}; instalar mediante sudo apt install ffmpeg", file=sys.stderr)
            return 2

    with (ROOT / "manifiesto.csv").open(encoding="utf-8-sig", newline="") as file:
        items = list(csv.DictReader(file, delimiter=";"))
    if len(items) != 120 or len({r["id"] for r in items}) != 120:
        print("ERROR: faltan registros o hay IDs duplicados en manifiesto.csv", file=sys.stderr)
        return 2

    audit_path = ROOT / "evaluaciones" / "conversiones.csv"
    audit = load_existing(audit_path)
    tally = Counter()
    print("===== HOMEX — AAC ORIGINAL → WAV PARA ASR =====")
    print("Originales: .aac | Convertidos: .wav PCM16 / mono / 16000 Hz")
    print("Los originales nunca se eliminan, alteran ni sobrescriben.\n")
    for r in items:
        rid, cat = r["id"], r["categoria"]
        if cat not in FOLDERS:
            print(f"[ERROR] {rid}: categoría no reconocida: {cat}"); tally["error"] += 1; continue
        base = ROOT / FOLDERS[cat]
        source = base / "audios" / f"{rid}.aac"
        dest = base / "audios_asr" / f"{rid}.wav"
        if (r["ruta_audio_esperada"] != source.relative_to(ROOT).as_posix()
            or r["ruta_audio_compatible_asr"] != dest.relative_to(ROOT).as_posix()):
            print(f"[ERROR] {rid}: manifiesto inconsistente"); tally["error"] += 1; continue
        if not source.exists():
            print(f"[PENDIENTE] {rid}: aún no existe {source.relative_to(ROOT)}")
            tally["pendiente"] += 1
            continue
        try:
            validate_aac(source)
            src_sha = sha256(source)
            old = audit.get(rid)
            if dest.exists():
                if not old or old["sha256_aac"] != src_sha or old["sha256_wav"] != sha256(dest):
                    raise ValueError("WAV existente sin procedencia verificable o el AAC cambió; no se sobrescribe")
                valid_wav(dest)
                print(f"[EXISTENTE/VERIFICADO] {rid}: {dest.relative_to(ROOT)}")
                tally["verificado"] += 1
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            fd, tmpname = tempfile.mkstemp(prefix=f".{rid}-", suffix=".wav", dir=str(dest.parent))
            os.close(fd)
            tmp = Path(tmpname)
            try:
                cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-xerror",
                       "-y", "-i", str(source), "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000",
                       "-c:a", "pcm_s16le", "-f", "wav", str(tmp)]
                p = subprocess.run(cmd, capture_output=True, text=True, check=False)
                if p.returncode != 0:
                    raise ValueError("ffmpeg falló: " + p.stderr.strip()[:280])
                duration = valid_wav(tmp)
                if dest.exists():
                    raise ValueError("WAV destino apareció durante la conversión; no sobrescribir")
                os.replace(tmp, dest)
            finally:
                tmp.unlink(missing_ok=True)
            audit[rid] = {"id": rid, "archivo_aac": source.relative_to(ROOT).as_posix(),
                          "sha256_aac": src_sha, "archivo_wav": dest.relative_to(ROOT).as_posix(),
                          "sha256_wav": sha256(dest), "duracion_s": f"{duration:.3f}",
                          "bytes_aac": str(source.stat().st_size), "bytes_wav": str(dest.stat().st_size)}
            write_audit(audit_path, audit)
            print(f"[CONVERTIDO] {rid}: {source.name} → {dest.name} ({duration:.2f}s; {dest.stat().st_size} bytes)")
            tally["convertido"] += 1
        except Exception as exc:
            print(f"[ERROR] {rid}: {exc}")
            tally["error"] += 1
    print("\n===== RESUMEN =====")
    for k in ("convertido", "verificado", "pendiente", "error"):
        print(f"{k.upper()}: {tally[k]}")
    print("TOTAL: ", len(items))
    print("LOG DE AUDITORÍA: ", audit_path.relative_to(ROOT))
    if tally["error"] or (args.exigir_completos and tally["pendiente"]):
        print("ESTADO: INCOMPLETO / CON ERRORES")
        return 1
    print("ESTADO: " + ("LISTO PARA ASR" if not tally["pendiente"] else "EN PREPARACIÓN"))
    return 0

if __name__ == "__main__":
    sys.exit(main())
