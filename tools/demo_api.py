"""Demo HTTP local: audio -> Faster-Whisper -> RulesEngine -> JSON.

No es el backend comercial de HOMEX. No usa base de datos, Redis ni Celery.
"""

from __future__ import annotations

import os
import tempfile
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool

from homex_nlp.asr.audio_validation import SUPPORTED_SUFFIXES
from homex_nlp.asr.faster_whisper_adapter import FasterWhisperAdapter
from homex_nlp.asr.service import AsrService
from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine
from homex_nlp.errors import HomexError

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "frontend" / "index.html"
MAX_AUDIO_BYTES = 25_000_000
CONTENT_TYPE_SUFFIX = {
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
}

app = FastAPI(
    title="HOMEX NLP Demo",
    version="0.1.0",
    description="Adaptador local de demostración; no es la API comercial Django.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class DemoConfigurationError(RuntimeError):
    """Configuración ausente o inválida del demostrador."""


@lru_cache(maxsize=1)
def get_asr_service() -> AsrService:
    raw_model_path = os.environ.get("HOMEX_ASR_MODEL_PATH", "").strip()
    if not raw_model_path:
        raise DemoConfigurationError(
            "Defina HOMEX_ASR_MODEL_PATH con la ruta absoluta del modelo Faster-Whisper local."
        )

    model_path = Path(raw_model_path).expanduser()
    if not model_path.is_absolute():
        raise DemoConfigurationError("HOMEX_ASR_MODEL_PATH debe ser una ruta absoluta.")

    device = os.environ.get("HOMEX_ASR_DEVICE", "cpu").strip() or "cpu"
    compute_type = os.environ.get("HOMEX_ASR_COMPUTE_TYPE", "int8").strip() or "int8"
    adapter = FasterWhisperAdapter(
        model_path,
        device=device,
        compute_type=compute_type,
    )
    return AsrService(adapter, max_bytes=MAX_AUDIO_BYTES)


def _suffix_for(upload: UploadFile) -> str:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix in SUPPORTED_SUFFIXES:
        return suffix
    return CONTENT_TYPE_SUFFIX.get(upload.content_type or "", ".webm")


async def _store_upload(upload: UploadFile) -> Path:
    path: Path | None = None
    total = 0
    suffix = _suffix_for(upload)

    try:
        with tempfile.NamedTemporaryFile(
            prefix="homex-demo-",
            suffix=suffix,
            delete=False,
        ) as target:
            path = Path(target.name)
            while chunk := await upload.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_AUDIO_BYTES:
                    raise HTTPException(status_code=413, detail="El audio supera el límite del demo.")
                target.write(chunk)
        return path
    except Exception:
        if path is not None:
            path.unlink(missing_ok=True)
        raise


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    if not INDEX.is_file():
        raise HTTPException(status_code=404, detail="No se encontró frontend/index.html")
    return FileResponse(INDEX)


@app.get("/api/demo/status")
def demo_status() -> dict[str, object]:
    raw_model_path = os.environ.get("HOMEX_ASR_MODEL_PATH", "").strip()
    model_path = Path(raw_model_path).expanduser() if raw_model_path else None
    return {
        "demo": True,
        "persistence": False,
        "queue": False,
        "nlp_mode": "RULES_ONLY",
        "asr_configured": bool(model_path and model_path.is_absolute() and model_path.is_dir()),
        "asr_model": model_path.name if model_path else None,
    }


@app.post("/api/pipeline/process/")
async def process_audio(file: UploadFile = File(...)) -> dict[str, object]:
    temp_path: Path | None = None
    try:
        temp_path = await _store_upload(file)
        service = get_asr_service()
        transcription = await run_in_threadpool(service.transcribe, temp_path)

        request = ExtractionRequest(
            request_id=f"demo-{uuid4()}",
            text=transcription.text_original,
            language="es",
            currency_context="BOB",
            transcription=transcription,
        )
        extraction = RulesEngine().extract(request)

        return {
            "texto_crudo": transcription.text_original,
            "transcription": transcription.model_dump(mode="json"),
            "extraction": extraction.model_dump(mode="json"),
        }
    except DemoConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except HomexError as error:
        raise HTTPException(
            status_code=422,
            detail=error.detail.model_dump(mode="json"),
        ) from error
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        await file.close()
