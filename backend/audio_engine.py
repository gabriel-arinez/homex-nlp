from faster_whisper import WhisperModel
import os
import logging
from functools import lru_cache

from config import settings

# Configurar logging
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def cargar_modelo():
    """
    Carga el modelo Whisper una sola vez usando singleton con LRU cache.
    Esto evita consumo excesivo de memoria al no cargar múltiples instancias.
    """
    logger.info(f"Cargando modelo Whisper '{settings.WHISPER_MODEL}' en {settings.WHISPER_DEVICE}...")
    model = WhisperModel(
        settings.WHISPER_MODEL,
        device=settings.WHISPER_DEVICE,
        compute_type=settings.WHISPER_COMPUTE_TYPE
    )
    logger.info("Modelo Whisper cargado exitosamente.")
    return model


def transcribir_audio(ruta_archivo: str) -> str:
    """
    Recibe un archivo de audio y devuelve el texto transcrito.
    
    Args:
        ruta_archivo: Path absoluto o relativo al archivo de audio
        
    Returns:
        str: Texto transcrito del audio
        
    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si el archivo está vacío o corrupto
    """
    if not os.path.exists(ruta_archivo):
        logger.error(f"Archivo no encontrado: {ruta_archivo}")
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")
    
    # Verificar que el archivo no esté vacío
    if os.path.getsize(ruta_archivo) == 0:
        logger.error(f"Archivo vacío: {ruta_archivo}")
        raise ValueError(f"El archivo de audio está vacío: {ruta_archivo}")
    
    try:
        model = cargar_modelo()
        
        # beam_size=5 mejora la precisión al evaluar múltiples opciones de transcripción
        segments, info = model.transcribe(
            ruta_archivo,
            beam_size=settings.WHISPER_BEAM_SIZE,
            language=settings.WHISPER_LANGUAGE
        )
        
        logger.info(f"Audio procesado - Idioma detectado: {info.language}, confianza: {info.language_probability:.2f}")
        
        texto_completo = []
        for segment in segments:
            texto_completo.append(segment.text)
        
        resultado = " ".join(texto_completo).strip()
        
        if not resultado:
            logger.warning("La transcripción resultó en texto vacío")
            
        return resultado
        
    except Exception as e:
        logger.error(f"Error durante la transcripción: {str(e)}")
        raise