"""Opt-in local Faster-Whisper adapter; no download or runtime NLP integration."""

import hashlib
import importlib.metadata
import io
import json
import os
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from training.benchmark_campo.pipeline import digest

from .dataset import PilotError


@dataclass(frozen=True)
class Decode:
    language: str = "es"
    beam_size: int = 5
    best_of: int = 5
    temperature: float = 0.0
    vad_filter: bool = False
    condition_on_previous_text: bool = True
    cpu_threads: int = 2
    device: str = "cpu"
    compute_type: str = "int8"
    variant: str = "base"
    expected_model_sha256: str | None = None

    def validate(self):
        if (
            self.language not in {"es", "en"}
            or self.beam_size < 1
            or self.best_of < 1
            or self.cpu_threads < 1
            or self.temperature != 0.0
            or self.device not in {"cpu", "cuda"}
            or self.compute_type not in {"int8", "float32", "float16"}
            or self.variant not in {"base", "small"}
        ):
            raise PilotError("INVALID_DECODING_PARAMETERS")
        if self.expected_model_sha256 is not None and not re.fullmatch(
            r"[a-f0-9]{64}", self.expected_model_sha256
        ):
            raise PilotError("INVALID_EXPECTED_MODEL_SHA256")
        return asdict(self)


def model_manifest(directory, variant):
    root = Path(directory)
    if not root.is_dir():
        raise PilotError("MODEL_NOT_INSTALLED")
    if any(p.is_symlink() for p in [root, *root.parents]):
        raise PilotError("MODEL_SYMLINK_REJECTED")
    if not all((root / name).is_file() for name in ("model.bin", "config.json", "tokenizer.json")):
        raise PilotError("MODEL_FILES_MISSING")
    files = {}
    allowed = {
        "model.bin",
        "config.json",
        "tokenizer.json",
        "vocabulary.txt",
        "vocabulary.json",
        "preprocessor_config.json",
    }
    for p in sorted(root.iterdir()):
        if p.name not in allowed:
            continue
        if p.is_symlink():
            raise PilotError("MODEL_SYMLINK_REJECTED")
        if p.is_file():
            h = hashlib.sha256()
            with p.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    h.update(block)
            files[str(p.relative_to(root))] = h.hexdigest()
    config = json.loads((root / "config.json").read_text())
    # Verify architecture instead of trusting directory basename or a model alias.
    width = config.get("d_model")
    if width is not None and width != {"base": 512, "small": 768}[variant]:
        raise PilotError("MODEL_VARIANT_ARCHITECTURE_MISMATCH")
    if variant == "base" and root.name in {"small", "faster-whisper-small"}:
        raise PilotError("MODEL_VARIANT_LABEL_CONTRADICTION")
    return {
        "variant_declared": variant,
        "architecture_verified": width is not None,
        "variant_provenance": "OPERATOR_DECLARATION_NOT_AUTHENTICATED_BY_DIRECTORY_NAME",
        "files": files,
        "model_digest": digest(files),
    }


class LocalWhisper:
    def __init__(self, directory, parameters):
        if os.environ.get("CI") or os.environ.get("HOMEX_DATA_GATE_NO_TRAINING"):
            raise PilotError("REAL_ASR_FORBIDDEN_IN_CI")
        self.parameters = parameters
        parameters.validate()
        self.manifest = model_manifest(directory, parameters.variant)
        if (
            parameters.expected_model_sha256 is not None
            and self.manifest["files"]["model.bin"] != parameters.expected_model_sha256
        ):
            raise PilotError("EXPECTED_MODEL_SHA256_MISMATCH")
        self.manifest["expected_binary_sha256_matched"] = (
            parameters.expected_model_sha256 is not None
        )
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise PilotError("ASR_EXTRA_NOT_INSTALLED") from exc
        self.versions = {
            name: importlib.metadata.version(name)
            for name in ("faster-whisper", "ctranslate2", "av")
        }
        start = time.perf_counter()
        try:
            self.model = WhisperModel(
                str(Path(directory).absolute()),
                device=parameters.device,
                compute_type=parameters.compute_type,
                cpu_threads=parameters.cpu_threads,
                num_workers=1,
                local_files_only=True,
            )
        except Exception as exc:
            raise PilotError("MODEL_LOAD_FAILED") from exc
        self.load_seconds = time.perf_counter() - start

    def transcribe(self, payload):
        p = self.parameters
        # The caller supplies hash-verified bytes, never a path vulnerable to swap.
        segments, _ = self.model.transcribe(
            io.BytesIO(payload),
            language=p.language,
            beam_size=p.beam_size,
            best_of=p.best_of,
            temperature=p.temperature,
            vad_filter=p.vad_filter,
            condition_on_previous_text=p.condition_on_previous_text,
            word_timestamps=False,
            initial_prompt=None,
        )
        return [{"start": float(s.start), "end": float(s.end), "text": s.text} for s in segments]
