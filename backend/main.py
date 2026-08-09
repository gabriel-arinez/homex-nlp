# =============================================================================
# Orquestar el pipeline ASR → NLP → persistencia
# NO contiene lógica de negocio, NO importa sqlite3, NO calcula métricas
# Toda persistencia delega a database.py; toda extracción a nlp_engine.py
#
# Endpoints:
#   POST /api/pipeline/process/     → audio → CotizacionCapturada
#   POST /api/pipeline/save-hitl/   → validación HITL → métricas guardadas
#   GET  /api/metricas/             → resumen estadístico para panel académico
#   GET  /api/health/               → estado del servidor
# =============================================================================

import os
import time
import json
import uuid
import shutil
import logging

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from faster_whisper import WhisperModel

from database import (
    init_db,
    guardar_captura_inicial,
    guardar_items_ia,
    guardar_validacion_hitl,
    obtener_metricas_resumen,
)
from nlp_engine import MotorNLP, CotizacionCapturada

# =============================================================================
# CONFIGURACIÓN DE LOGGING
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("homex.main")

# =============================================================================
# VERSIÓN DEL PIPELINE
# Se actualiza manualmente cuando cambia el modelo ASR o NER.
# Se persiste en la base de datos para trazabilidad de experimentos.
# =============================================================================
PIPELINE_VERSION = "Whisper-Small-INT8 + spaCy-HOMEX-v4"

# =============================================================================
# INICIALIZACIÓN DE LA APLICACIÓN
# =============================================================================
app = FastAPI(
    title="HOMEX Academic NLP Core",
    description="Pipeline de captura por voz y extracción NER para cotizaciones de carpintería.",
    version="4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# INICIALIZACIÓN DE BASE DE DATOS Y MODELOS (SINGLETON)
# Se ejecutan una sola vez al arrancar el servidor, no por request.
# Esto evita recargar modelos pesados (Whisper ~500MB, spaCy ~50MB) en cada llamada.
# =============================================================================
init_db()

logger.info("[ASR] Cargando Whisper small (CPU, INT8)...")
whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
logger.info("[ASR] Whisper listo.")

logger.info("[NLP] Inicializando MotorNLP HOMEX...")
motor_nlp = MotorNLP()
logger.info("[NLP] Motor NLP listo.")


# =============================================================================
# SCHEMAS DE ENTRADA (para el endpoint HITL)
# El frontend envía JSON en el body, no form-encoded.
# Esto elimina el acoplamiento a URLSearchParams y permite arrays reales.
# =============================================================================

class ItemMuebleHITL(BaseModel):
    """Datos de un mueble corregidos por el operador."""
    producto: Optional[str] = None
    material: Optional[str] = None
    espesor: Optional[str] = None
    color: Optional[str] = None
    dimensiones: List[str] = Field(default_factory=list)
    cantidad: Optional[int] = None
    precio_total: Optional[float] = None
    accesorios: List[str] = Field(default_factory=list)
    observaciones: Optional[str] = None


class PayloadHITL(BaseModel):
    """
    Payload completo que envía el frontend al guardar la validación HITL.
    Incluye referencia a la captura original y los muebles corregidos.
    """
    captura_id: int = Field(description="ID de la captura original retornado por /process/")
    items_ia_ids: List[int] = Field(
        description="IDs de los ítems IA guardados, en el mismo orden que los muebles."
    )
    muebles_ia: List[Dict[str, Any]] = Field(
        description="Copia de los muebles tal como los devolvió la IA (para calcular diff)."
    )
    muebles_humano: List[ItemMuebleHITL] = Field(
        description="Muebles después de corrección humana, uno por ítem."
    )
    latencia_total_ms: int = Field(description="Latencia total del proceso desde grabación.")
    latencia_asr_ms: int = Field(description="Latencia solo del ASR (Whisper).")
    latencia_nlp_ms: int = Field(description="Latencia solo del NLP (spaCy).")
    labels_encontrados: List[str] = Field(
        default_factory=list,
        description="Labels NER que detectó el motor, para análisis de cobertura."
    )


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/api/health/")
async def health_check():
    """Verifica que el servidor y los modelos estén activos."""
    return {
        "status": "online",
        "pipeline_version": PIPELINE_VERSION,
        "modelos": {
            "asr": "Whisper small CPU INT8",
            "nlp": motor_nlp.ruta_modelo,
        }
    }


@app.post("/api/pipeline/process/")
async def procesar_audio(file: UploadFile = File(...)):
    """
    Endpoint principal del pipeline ASR → NLP.

    Recibe un archivo de audio .webm del navegador y retorna:
    - texto_crudo: transcripción de Whisper
    - entidades_ia: CotizacionCapturada con todos los muebles detectados
    - captura_id: ID de la fila guardada en capturas (para usarlo en HITL)
    - items_ia_ids: IDs de los ítems IA guardados (para usarlos en HITL)
    - latencias desglosadas por etapa

    El archivo temporal usa UUID para evitar colisión en entornos multi-request.
    """
    nombre_temporal = f"temp_{uuid.uuid4().hex}.webm"
    t_inicio_total = time.time()

    try:
        # --- Guardar audio temporal ---
        with open(nombre_temporal, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # --- Etapa ASR: Whisper ---
        t_inicio_asr = time.time()
        segmentos, _ = whisper_model.transcribe(
            nombre_temporal,
            beam_size=5,
            language="es",
        )
        texto_transcrito = " ".join([seg.text for seg in segmentos]).strip()
        latencia_asr_ms = int((time.time() - t_inicio_asr) * 1000)

        if not texto_transcrito:
            raise HTTPException(
                status_code=400,
                detail="Whisper no detectó audio comprensible. Verificar micrófono o calidad del audio."
            )

        logger.info(f"[ASR] Transcripción ({latencia_asr_ms}ms): {texto_transcrito[:80]}...")

        # --- Etapa NLP: Motor NER ---
        t_inicio_nlp = time.time()
        cotizacion: CotizacionCapturada = motor_nlp.procesar_cotizacion(texto_transcrito)
        latencia_nlp_ms = int((time.time() - t_inicio_nlp) * 1000)
        latencia_total_ms = int((time.time() - t_inicio_total) * 1000)

        logger.info(
            f"[NLP] {cotizacion.num_items_detectados} ítems detectados "
            f"({latencia_nlp_ms}ms). Labels: {cotizacion.labels_detectados}"
        )

        # --- Persistencia de captura inicial ---
        captura_id = guardar_captura_inicial(
            texto_transcrito=texto_transcrito,
            texto_normalizado=cotizacion.texto_normalizado,
            modelo_version=PIPELINE_VERSION,
            latencia_total_ms=latencia_total_ms,
            latencia_asr_ms=latencia_asr_ms,
            latencia_nlp_ms=latencia_nlp_ms,
            num_items_ia=cotizacion.num_items_detectados,
            labels_detectados=cotizacion.labels_detectados,
            advertencias_motor=cotizacion.advertencias,
        )

        muebles_ia_dicts = [m.model_dump() for m in cotizacion.muebles]
        items_ia_ids = guardar_items_ia(captura_id, muebles_ia_dicts)

        return {
            "status": "success",
            "captura_id": captura_id,
            "items_ia_ids": items_ia_ids,
            "latencia_total_ms": latencia_total_ms,
            "latencia_asr_ms": latencia_asr_ms,
            "latencia_nlp_ms": latencia_nlp_ms,
            "texto_crudo": texto_transcrito,
            "entidades_ia": cotizacion.model_dump(),
            "modelo_version": PIPELINE_VERSION,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Pipeline] Error inesperado: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno del pipeline: {str(e)}")
    finally:
        if os.path.exists(nombre_temporal):
            os.remove(nombre_temporal)


@app.post("/api/pipeline/save-hitl/")
async def guardar_validacion_humana(payload: PayloadHITL):
    """
    Guarda la validación HITL del operador y calcula métricas de precisión.

    Recibe JSON (no form-encoded) para soportar arrays reales de muebles.
    Delega completamente la lógica de métricas y persistencia a database.py.

    Retorna las métricas calculadas para mostrarlas en el frontend.
    """
    try:
        muebles_humano_dicts = [m.model_dump() for m in payload.muebles_humano]

        metricas = guardar_validacion_hitl(
            captura_id=payload.captura_id,
            items_ia_ids=payload.items_ia_ids,
            muebles_ia=payload.muebles_ia,
            muebles_humano=muebles_humano_dicts,
            latencia_total_ms=payload.latencia_total_ms,
            latencia_asr_ms=payload.latencia_asr_ms,
            latencia_nlp_ms=payload.latencia_nlp_ms,
            labels_encontrados=payload.labels_encontrados,
        )

        logger.info(
            f"[HITL] Validación guardada: captura_id={payload.captura_id}, "
            f"precisión={metricas.get('precision_global', 0):.2%}"
        )

        return {
            "status": "persisted",
            "captura_id": payload.captura_id,
            "metricas": metricas,
        }

    except Exception as e:
        logger.error(f"[HITL] Error al guardar validación: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al persistir validación: {str(e)}")


@app.get("/api/metricas/")
async def obtener_metricas():
    """
    Retorna resumen estadístico de todas las capturas.
    Usado por el panel académico del frontend para demostrar el aporte del modelo.
    """
    try:
        resumen = obtener_metricas_resumen()
        return {"status": "ok", "resumen": resumen}
    except Exception as e:
        logger.error(f"[Métricas] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))