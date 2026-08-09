"""
Configuración centralizada para el backend de HOMEX NLP API
Usa variables de entorno con valores por defecto seguros
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Configuración del servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Configuración de CORS (dominios permitidos)
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ]
    
    # Configuración de archivos
    MAX_FILE_SIZE_MB: int = 10  # Tamaño máximo de archivo en MB
    ALLOWED_AUDIO_TYPES: List[str] = [
        "audio/webm",
        "audio/mp4",
        "audio/mpeg",
        "audio/ogg",
        "audio/wav"
    ]
    
    # Configuración del modelo Whisper
    WHISPER_MODEL: str = "small"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"
    WHISPER_LANGUAGE: str = "es"
    WHISPER_BEAM_SIZE: int = 5
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
