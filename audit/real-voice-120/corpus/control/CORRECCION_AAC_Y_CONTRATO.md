# Corrección de formato de grabaciones: AAC

## Evidencia técnica revisada (ramas por defecto; 8 de noviembre de 2026)

- Backend: [apps/capturas/audio.py](https://github.com/gabriel-arinez/homex-backend/blob/main/apps/capturas/audio.py) declara `SUFIJOS_AUDIO={'.wav','.mp3','.m4a','.ogg','.webm'}`. `guardar_audio` preserva extensión; `copiar_audio_para_asr` también.
- NLP: [src/homex_nlp/asr/audio_validation.py](https://github.com/gabriel-arinez/homex-nlp/blob/main/src/homex_nlp/asr/audio_validation.py) declara los mismos sufijos. Su servicio valida archivo antes de llamar al decodificador.
- Backend: [apps/capturas/pipeline.py](https://github.com/gabriel-arinez/homex-backend/blob/main/apps/capturas/pipeline.py) valida duración, transcribe la copia temporal y borra el original temporal **del backend** al completar ASR; no contiene una conversión AAC.
- NLP: [src/homex_nlp/asr_cli.py](https://github.com/gabriel-arinez/homex-nlp/blob/main/src/homex_nlp/asr_cli.py) elimina el archivo pasado al CLI; por eso toda prueba CLI debe pasar una copia temporal, nunca el único WAV convertido.
- Backend: [config/settings/base.py](https://github.com/gabriel-arinez/homex-backend/blob/main/config/settings/base.py) define 20 MB máximo y duración máxima de 300 segundos.

## Decisiones

1. Originales `MP-xxxx.aac`, `SIL-xxxx.aac`, `PIS-xxxx.aac`, `OTR-xxxx.aac` en carpetas `audios/`.
2. Conversión previa local con `control/preparar_audios_asr.py`; resultados WAV mono PCM16 16kHz en `audios_asr/` sin alterar los originales.
3. Identificación sin ambigüedad mediante `manifiesto.csv` + JSONL de referencia, ambos contienen las dos rutas por ID.
4. Registro comprobable por hash en `evaluaciones/conversiones.csv` y registros de consola con `tee`.
5. Los guiones dictados no se reescribieron; solo el etiquetado de formato y las herramientas de comparación.
6. No se afirma que la aplicación productiva acepte directamente `.aac`, ni se modifica su código sin pruebas cruzadas. Se debe tratar como tarea aparte si se desea esa función en producción.

## Controles para Codex

El paquete evita la pérdida de originales. Se desaconseja enviar `*.aac` directo al backend sin normalizar o modificar su validación. La verificación de *calidad de voz* (WER) no es automática hasta disponer de audio y de referencia humana de lo efectivamente pronunciado. La correspondencia `id → WAV → guion` sí queda completamente establecida.
