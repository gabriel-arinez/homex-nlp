"""Read-only, no-follow validation of the exact external 20-WAV manifest."""

import csv
import hashlib
import io
import os
import re
import wave
from pathlib import Path

from training.benchmark_campo.pipeline import digest

IDS = tuple(f"{i:02d}" for i in range(1, 21))
MAX_AUDIO_BYTES = 128 * 1024 * 1024


class PilotError(ValueError):
    """Safe fixed error code, never a user path or transcription."""


def read_safe(root, relative, limit):
    """Open every directory with O_NOFOLLOW, including authorized root ancestors."""
    root = Path(root).absolute()
    parts = Path(relative).parts
    if not parts or Path(relative).is_absolute() or any(p in {".", ".."} for p in parts):
        raise PilotError("PATH_OUTSIDE_AUTHORIZED_ROOT")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in root.parts[1:] + parts[:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        child = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(child, "rb") as stream:
            import stat

            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise PilotError("REGULAR_FILE_REQUIRED")
            data = stream.read(limit + 1)
        if len(data) > limit:
            raise PilotError("INPUT_TOO_LARGE")
        return data
    except OSError as exc:
        raise PilotError("MISSING_FILE_OR_UNSAFE_SYMLINK") from exc
    finally:
        os.close(fd)


def audio_info(payload):
    if payload.startswith(b"version https://git-lfs.github.com/spec/v1"):
        raise PilotError("LFS_POINTER_NOT_HYDRATED")
    if len(payload) < 44 or payload[:4] != b"RIFF" or payload[8:12] != b"WAVE":
        raise PilotError("INVALID_WAV_HEADER")
    if int.from_bytes(payload[4:8], "little") + 8 != len(payload):
        raise PilotError("TRUNCATED_OR_TRAILING_WAV_BYTES")
    try:
        with wave.open(io.BytesIO(payload), "rb") as audio:
            channels, width, rate, frames = (
                audio.getnchannels(),
                audio.getsampwidth(),
                audio.getframerate(),
                audio.getnframes(),
            )
            if (
                audio.getcomptype() != "NONE"
                or channels not in {1, 2}
                or width not in {1, 2, 3, 4}
                or not 8000 <= rate <= 192000
                or frames < 1
            ):
                raise PilotError("UNSUPPORTED_PCM_WAV")
            data = audio.readframes(frames)
            if len(data) != frames * channels * width:
                raise PilotError("TRUNCATED_PCM_FRAMES")
    except (wave.Error, EOFError) as exc:
        raise PilotError("CORRUPT_WAV") from exc
    return {
        "channels": channels,
        "sample_width_bytes": width,
        "sample_rate_hz": rate,
        "frames": frames,
        "duration_seconds": frames / rate,
    }


def validated_audio(dataset_dir, entry):
    data = read_safe(dataset_dir, f"audios/{entry['id']}.wav", MAX_AUDIO_BYTES)
    if data.startswith(b"version https://git-lfs.github.com/spec/v1"):
        raise PilotError("LFS_POINTER_NOT_HYDRATED")
    if len(data) != entry["bytes"]:
        raise PilotError("AUDIO_SIZE_MISMATCH")
    if hashlib.sha256(data).hexdigest() != entry["audio_sha256"]:
        raise PilotError("AUDIO_SHA256_MISMATCH")
    audio_info(data)
    return data


def validate(dataset_dir, *, synthetic=False):
    root = Path(dataset_dir)
    raw = read_safe(root, "manifest.csv", 64 * 1024)
    try:
        table = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
        if table.fieldnames != ["guion", "archivo", "sha256", "bytes"]:
            raise PilotError("MANIFEST_COLUMNS")
        rows = list(table)
    except (UnicodeError, csv.Error) as exc:
        raise PilotError("INVALID_MANIFEST_CSV") from exc
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise PilotError("MANIFEST_MISSING_OR_EXTRA_COLUMNS")
    if len(rows) != 20 or sorted(r["guion"] for r in rows) != list(IDS):
        raise PilotError("EXACT_IDS_01_TO_20_REQUIRED")
    entries, hashes = [], set()
    for row in sorted(rows, key=lambda r: r["guion"]):
        case = row["guion"]
        if None in row or row["archivo"] != f"audios/{case}.wav":
            raise PilotError("EXACT_WAV_PATH_REQUIRED")
        if not re.fullmatch(r"[a-f0-9]{64}", row["sha256"] or "") or not re.fullmatch(
            r"[1-9][0-9]*", row["bytes"] or ""
        ):
            raise PilotError("MANIFEST_HASH_OR_SIZE")
        if row["sha256"] in hashes:
            raise PilotError("DUPLICATE_AUDIO_CONTENT")
        hashes.add(row["sha256"])
        entry = {"id": case, "audio_sha256": row["sha256"], "bytes": int(row["bytes"])}
        if entry["bytes"] > MAX_AUDIO_BYTES:
            raise PilotError("INPUT_TOO_LARGE")
        data = validated_audio(root, entry)
        entries.append(entry | audio_info(data))
    # Reject extras, renamed m4a, nested folders and symlinks; never ignore a case.
    try:
        if {p.name for p in (root / "audios").iterdir()} != {f"{i}.wav" for i in IDS}:
            raise PilotError("EXTRA_OR_MISSING_AUDIO_ENTRY")
    except OSError as exc:
        raise PilotError("AUDIO_DIRECTORY_UNAVAILABLE") from exc
    return {
        "schema_version": "audio-pilot-input-1",
        "source_type": "SINTETICO_SOLO_PRUEBA" if synthetic else "PILOTO_REAL_DIAGNOSTICO_CONOCIDO",
        "manifest_csv_sha256": hashlib.sha256(raw).hexdigest(),
        "dataset_digest": digest(entries),
        "entries": entries,
        "HUMAN_GOLD": "NO",
        "WER": "N/A",
        "HOLDOUT_EXTERNO": 0,
        "training_use": "PROHIBITED",
        "historical_22_attempts_mapping": "UNVERIFIED_NOT_1_TO_1",
    }
