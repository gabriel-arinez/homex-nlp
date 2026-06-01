from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import time

# Importamos nuestros motores
from audio_engine import transcribir_audio
from nlp_engine import procesar_texto

app = FastAPI(title="Homex NLP API", version="1.0")

# Permitir CORS para que el frontend pueda comunicarse sin bloqueos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/quote/")
async def procesar_cotizacion(file: UploadFile = File(...)):
    # 1. Guardar archivo temporal (el navegador enviará un .webm)
    temp_path = f"temp_{int(time.time())}.webm"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Pipeline de IA
        inicio = time.time()
        
        texto_transcrito = transcribir_audio(temp_path)
        datos_extraidos = procesar_texto(texto_transcrito)
        
        fin = time.time()
        
        # 3. Respuesta estructurada
        return {
            "status": "success",
            "tiempo_procesamiento_segundos": round(fin - inicio, 2),
            "texto_crudo": texto_transcrito,
            "entidades": datos_extraidos
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # 4. Limpieza (Súper importante para no llenar el disco duro)
        if os.path.exists(temp_path):
            os.remove(temp_path)