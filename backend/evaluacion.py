import jiwer
from nlp_engine import procesar_texto

# 1. Cálculo de WER (Word Error Rate) para el audio
referencia = "necesito un ropero de melamina de dos metros"
hipotesis_whisper = "necesito un ropero de melamina de 2 metros" # Lo que sacó la IA

error_tasa = jiwer.wer(referencia, hipotesis_whisper)
print(f"Word Error Rate (WER): {error_tasa * 100:.2f}%") 
# (Mientras más cerca de 0%, mejor)