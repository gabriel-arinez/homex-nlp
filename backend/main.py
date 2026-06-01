import os
import time
import json
import sqlite3
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from faster_whisper import WhisperModel
import spacy
from spacy.matcher import Matcher
import jiwer

# ==========================================
# 1. INICIALIZACIÓN Y CONFIGURACIÓN BASE
# ==========================================
app = FastAPI(title="HOMEX Academic NLP Core", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "homex_trazabilidad.db"

def init_db():
    """Inicializa la base de datos de trazabilidad académica"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs_procesamiento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            texto_transcrito TEXT,
            json_ia_extraido TEXT,
            json_humano_validado TEXT,
            wer_calculado REAL,
            latencia_ms INTEGER,
            modelo_version TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Carga de Modelos Inteligentes en Memoria (Singleton de Servidor)
print("[IA] Cargando Componentes ASR de alta resolución (Whisper CPU Offline)...")
whisper_model = WhisperModel("small", device="cpu", compute_type="int8")

print("[IA] Inicializando Pipeline NLP Avanzado de spaCy...")
nlp = spacy.load("es_core_news_sm")
matcher = Matcher(nlp.vocab)

# Patrones estructurados basados en la proforma real de HOMEX
patrones_muebles = [
    [{"LOWER": "escritorio"}, {"LOWER": "ejecutivo"}],
    [{"LOWER": "credenza"}, {"LOWER": "mesa"}, {"LOWER": "auxiliar"}],
    [{"LOWER": "silla"}, {"LOWER": "ejecutiva"}],
    [{"LOWER": "credenza"}]
]
matcher.add("PRODUCTO_COMPUESTO", patrones_muebles)

# ==========================================
# 2. MODELOS DE DATOS PYDANTIC (NORMALIZACIÓN)
# ==========================================
class DetalleMueble(BaseModel):
    producto: Optional[str] = Field(None, description="Nombre normalizado del mueble")
    ambiente: Optional[str] = Field("No especificado", description="Ubicación física o ambiente")
    material: Optional[str] = Field(None, description="Material y espesor")
    dimensiones: Optional[str] = Field(None, description="Dimensiones estructuradas (Ancho x Alto x Profundidad)")
    detalles_adicionales: List[str] = Field(default_factory=list, description="Accesorios o requerimientos mecánicos")

# ==========================================
# 3. PIPELINE SEMÁNTICO (NLP ENGINE)
# ==========================================
def normalizar_texto(texto: str) -> str:
    """Normaliza términos técnicos del lenguaje de carpintería"""
    cambios = {
        "mts": "metros",
        "cm": "centímetros",
        " de espesor": " mm",
        "grosor de": "espesor de",
        "melamina de dieciocho": "melamina de 18mm"
    }
    texto_limpio = texto.lower()
    for llave, valor in cambios.items():
        texto_limpio = texto_limpio.replace(llave, valor)
    return texto_limpio

def extraer_parametros_homex(texto: str) -> dict:
    """Analiza la estructura gramatical para extraer las variables de la proforma"""
    texto_norm = normalizar_texto(texto)
    doc = nlp(texto_norm)
    
    mueble = DetalleMueble()
    
    # 1. Extracción de Productos mediante Matcher Avanzado
    coincidencias = matcher(doc)
    if coincidencias:
        _, inicio, fin = coincidencias[0]
        mueble.producto = doc[inicio:fin].text.upper()
    else:
        # Fallback a sustantivos base
        for token in doc:
            if token.text in ["ropero", "estante", "mesa", "escritorio", "credenza"]:
                mueble.producto = token.text.upper()

    # 2. Búsqueda de Ambientes (ej: Oficina 2)
    for i in range(len(doc) - 1):
        if doc[i].text in ["oficina", "ambiente", "sala"]:
            mueble.ambiente = f"{doc[i].text.upper()} {doc[i+1].text}"

    # 3. Identificación de Materiales
    if "melamina" in texto_norm:
        mueble.material = "Melamina de 18 mm"
        if "15" in texto_norm: mueble.material = "Melamina de 15 mm"
        elif "25" in texto_norm: mueble.material = "Melamina de 25 mm"
    elif "pino" in texto_norm or "madera" in texto_norm:
        mueble.material = "Madera Pino Seleccionada"

    # 4. Aislamiento Estructurado de Dimensiones (Ancho x Alto x Profundidad)
    # Busca patrones numéricos concatenados
    medidas = []
    for token in doc:
        if token.like_num or (token.text.replace('.', '', 1).isdigit()):
            # Evitar capturar espesores de melamina como dimensiones de estructura
            if i > 0 and doc[token.i - 1].text == "melamina":
                continue
            medidas.append(token.text)
            
    if len(medidas) >= 3:
        mueble.dimensiones = f"{medidas[0]} mts Ancho x {medidas[1]} mts Alto x {medidas[2]} mts Profundidad"
    elif len(medidas) == 2:
        mueble.dimensiones = f"{medidas[0]} x {medidas[1]} m"

    # 5. Captura de Accesorios Críticos (Basado en Diccionario Dinámico de Ingeniería)
    palabras_clave_accesorios = ["cajoneria", "rieles", "telescopicas", "jaladores", "chapa", "bisagras", "pasacable"]
    for termino in palabras_clave_accesorios:
        if termino in texto_norm:
            mueble.detalles_adicionales.append(termino.capitalize())

    return mueble.model_dump()

# ==========================================
# 4. ENDPOINTS OPERATIVOS
# ==========================================
@app.post("/api/pipeline/process/")
async def procesar_audio_endpoint(file: UploadFile = File(...)):
    """Recibe el archivo multimedia del navegador y ejecuta la cascada de procesamiento IA"""
    ruta_temporal = f"temp_{int(time.time())}.webm"
    t_inicio = time.time()
    
    try:
        with open(ruta_temporal, "wb") as buffer:
            shutil_stream(file.file, buffer)
            
        # Ejecución del subsistema ASR
        segmentos, _ = whisper_model.transcribe(ruta_temporal, beam_size=5, language="es")
        texto_transcrito = " ".join([seg.text for seg in segmentos]).strip()
        
        if not texto_transcrito:
            raise HTTPException(status_code=400, detail="El sistema no logró percibir audio comprensible.")
            
        # Ejecución del subsistema NLP
        datos_extraidos = extraer_parametros_homex(texto_transcrito)
        t_final = time.time()
        
        return {
            "status": "success",
            "latencia_ms": int((t_final - t_inicio) * 1000),
            "texto_crudo": texto_transcrito,
            "entidades_ia": datos_extraidos,
            "modelo_version": "Whisper-Small-INT8 + spaCy-HOMEX-v2"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)

def shutil_stream(src, dst):
    import shutil
    shutil.copyfileobj(src, dst)

@app.post("/api/pipeline/save-hitl/")
async def guardar_validacion_humana(
    texto_crudo: str = Form(...),
    json_ia: str = Form(...),
    json_humano: str = Form(...),
    latencia_ms: int = Form(...),
    modelo_version: str = Form(...)
):
    """Guarda la auditoría del Human-in-the-Loop y calcula el error para la defensa"""
    try:
        dict_humano = json.loads(json_humano)
        texto_humano_esperado = f"{dict_humano.get('producto', '')} {dict_humano.get('material', '')} {dict_humano.get('dimensiones', '')}"
        
        # Calcular WER instrumental para el registro académico
        wer_score = jiwer.wer(texto_humano_esperado.lower(), texto_crudo.lower())
    except:
        wer_score = 1.0  # Fallback si hay discrepancia estructural extrema

    # Persistencia en SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO logs_procesamiento 
        (texto_transcrito, json_ia_extraido, json_humano_validado, wer_calculado, latencia_ms, modelo_version)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (texto_crudo, json_ia, json_humano, float(wer_score), latencia_ms, modelo_version))
    conn.commit()
    conn.close()
    
    return {"status": "persisted", "calculated_wer": round(wer_score, 4)}