from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import time
import tempfile
import logging
import magic

from config import settings
from audio_engine import transcribir_audio
from nlp_engine import procesar_texto

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Homex NLP API", version="1.0")

# Configuración de CORS restringida a dominios específicos
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
async def health_check():
    """Endpoint para verificación del estado del servicio"""
    return {"status": "healthy", "version": "1.0"}


@app.post("/api/quote/", status_code=status.HTTP_200_OK)
async def procesar_cotizacion(file: UploadFile = File(...)):
    """
    Procesa una cotización de mueble a partir de un archivo de audio.
    
    Args:
        file: Archivo de audio con las especificaciones del mueble
        
    Returns:
        dict: Resultado con texto transcrito y entidades extraídas
        
    Raises:
        HTTPException: Si hay errores en la validación o procesamiento
    """
    # Validar tipo MIME del archivo
    file_content = await file.read()
    
    # Verificar tamaño máximo
    file_size_mb = len(file_content) / (1024 * 1024)
    if file_size_mb > settings.MAX_FILE_SIZE_MB:
        logger.warning(f"Archivo demasiado grande: {file_size_mb:.2f} MB")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo excede el tamaño máximo de {settings.MAX_FILE_SIZE_MB} MB"
        )
    
    # Verificar tipo de archivo usando python-magic
    mime = magic.Magic(mime=True)
    detected_mime = mime.from_buffer(file_content)
    
    if detected_mime not in settings.ALLOWED_AUDIO_TYPES:
        logger.warning(f"Tipo de archivo no permitido: {detected_mime}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido: {detected_mime}. Tipos aceptados: {', '.join(settings.ALLOWED_AUDIO_TYPES)}"
        )
    
    # Crear archivo temporal seguro
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
            temp_file.write(file_content)
            temp_path = temp_file.name
        
        logger.info(f"Archivo recibido: {file.filename}, tamaño: {file_size_mb:.2f} MB, tipo: {detected_mime}")
        
        # Pipeline de IA
        inicio = time.time()
        
        texto_transcrito = transcribir_audio(temp_path)
        
        if not texto_transcrito.strip():
            logger.warning("Transcripción vacía recibida del motor de audio")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo transcribir el audio. Verifique que el archivo contenga audio válido."
            )
        
        datos_extraidos = procesar_texto(texto_transcrito)
        
        fin = time.time()
        tiempo_procesamiento = round(fin - inicio, 2)
        
        logger.info(f"Procesamiento completado en {tiempo_procesamiento}s")
        
        # Respuesta estructurada
        return {
            "status": "success",
            "tiempo_procesamiento_segundos": tiempo_procesamiento,
            "texto_crudo": texto_transcrito,
            "entidades": datos_extraidos
        }
        
    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.error(f"Error de archivo: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error inesperado durante el procesamiento: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno del servidor: {str(e)}")
    finally:
        # Limpieza segura del archivo temporal
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.remove(temp_file.name)
                logger.debug(f"Archivo temporal eliminado: {temp_file.name}")
            except Exception as e:
                logger.error(f"Error al eliminar archivo temporal: {str(e)}")