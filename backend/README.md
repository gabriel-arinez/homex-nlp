# HOMEX NLP API - Backend

Sistema de IA para capturar cotizaciones de muebles por voz utilizando Whisper (transcripción) y spaCy (extracción de entidades).

## Requisitos Previos

- Python 3.10+
- pip

## Instalación

1. Crear entorno virtual (recomendado):
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno (opcional):
```bash
cp .env.example .env
# Editar .env según sea necesario
```

## Ejecución

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en `http://localhost:8000`

## Endpoints

### Health Check
```
GET /health
```
Verifica el estado del servicio.

### Procesar Cotización
```
POST /api/quote/
Content-Type: multipart/form-data

Parámetros:
- file: Archivo de audio (webm, mp4, mp3, ogg, wav)
```

Respuesta:
```json
{
  "status": "success",
  "tiempo_procesamiento_segundos": 2.5,
  "texto_crudo": "Necesito un ropero de melamina de 2 metros",
  "entidades": {
    "producto": "ropero",
    "material": "melamina",
    "color": null,
    "dimensiones": ["2 metros"]
  }
}
```

## Configuración

Las siguientes variables de entorno pueden configurarse en `.env`:

| Variable | Descripción | Default |
|----------|-------------|---------|
| HOST | Host del servidor | 0.0.0.0 |
| PORT | Puerto del servidor | 8000 |
| ALLOWED_ORIGINS | Dominios CORS permitidos | localhost:3000, localhost:8080 |
| MAX_FILE_SIZE_MB | Tamaño máximo de archivo | 10 |
| WHISPER_MODEL | Modelo Whisper a usar | small |
| WHISPER_DEVICE | Dispositivo para Whisper | cpu |
| LOG_LEVEL | Nivel de logging | INFO |

## Estructura del Proyecto

```
backend/
├── config.py          # Configuración centralizada
├── main.py            # Aplicación FastAPI principal
├── audio_engine.py    # Motor de transcripción (Whisper)
├── nlp_engine.py      # Motor de procesamiento NLP (spaCy)
├── requirements.txt   # Dependencias
├── .env.example       # Ejemplo de configuración
└── .gitignore         # Archivos ignorados por git
```

## Notas Importantes

- El modelo Whisper se carga una sola vez usando caching para optimizar memoria
- Los archivos temporales se eliminan automáticamente después del procesamiento
- Se valida el tipo MIME y tamaño de los archivos de audio
- El logging está configurado para producción
