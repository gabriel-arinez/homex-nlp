from faster_whisper import WhisperModel
import os

# Cargamos el modelo en CPU (Small)
# compute_type="int8" reduce el consumo de RAM.
print("Cargando modelo Whisper...")
model = WhisperModel("small", device="cpu", compute_type="int8")
print("Modelo cargado.")

def transcribir_audio(ruta_archivo: str) -> str:
    """Recibe un archivo de audio y devuelve el texto transcrito"""
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")
        
    # beam_size=5 mejora la precisión al evaluar múltiples opciones de transcripción
    segments, info = model.transcribe(ruta_archivo, beam_size=5, language="es")
    
    texto_completo = []
    for segment in segments:
        texto_completo.append(segment.text)
        
    return " ".join(texto_completo).strip()

# --- PRUEBA EN CONSOLA ---
if __name__ == "__main__":
    ruta = "prueba2.m4a" 
    if os.path.exists(ruta):
        texto = transcribir_audio(ruta)
        print("Transcripción final:", texto)
    else:
        print("Archivo no encontrado.")