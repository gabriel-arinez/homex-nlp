# HOMEX NLP

Componente independiente de reconocimiento de voz y extracción de información para
cotizaciones HOMEX. F00 preparó el paquete, F01 definió contratos, F02 preservó y
curó ambos corpus, F03 incorporó el extractor determinístico, F04 dejó un
entrenamiento/evaluación NER reproducible, F05 añadió ASR con Faster-Whisper y F06
cerró el alcance distribuible del paquete.

El primer modelo NER no se promovió por métricas insuficientes. El motor operativo
actual es `RULES_ONLY`: reglas, expresiones regulares, parsing y normalización
sobre una propuesta singular. No hay persistencia comercial dentro de este
repositorio.

La guía es [Plan Maestro](docs/PLAN_MAESTRO_REFACTORIZACION_HOMEX.md), el contrato
actual está en [Contrato v1](docs/contract-v1.md) y las decisiones finales en
[requisitos](docs/requirements.md).

## Entorno reproducible

Python 3.11 (baseline comprobado: 3.11.15) y uv 0.12.9. Desde la raíz:

```bash
uv sync --locked --extra dev
make check
uv build
```

`uv.lock` fija dependencias transitivas. `pyproject.toml` separa runtime de texto
(spaCy/Pydantic/click), extras `asr` y `demo`, y herramientas `dev`. Los pesos
ASR no se descargan automáticamente.

## Demostración rápida: voz → Faster-Whisper → NLP → JSON

La demostración local sirve únicamente para exhibir el componente refactorizado.
No es el backend comercial Django y no utiliza SQLite, PostgreSQL, Redis ni Celery.

1. Instalar los extras:

```bash
uv sync --locked --extra dev --extra asr --extra demo
```

2. Disponer de un modelo Faster-Whisper ya descargado en una ruta local absoluta y
configurarlo:

```bash
export HOMEX_ASR_MODEL_PATH=/ruta/absoluta/al/modelo
export HOMEX_ASR_DEVICE=cpu
export HOMEX_ASR_COMPUTE_TYPE=int8
```

3. Arrancar el demo:

```bash
make demo
```

4. Abrir en el navegador:

```text
http://127.0.0.1:8001
```

El recorrido mostrado es:

```text
MediaRecorder
    ↓
audio temporal WebM
    ↓
Faster-Whisper
    ↓
TranscriptionResult
    ↓
RulesEngine
    ↓
ExtractionResult JSON
```

El archivo temporal se elimina después del intento de transcripción. La pantalla
muestra transcripción, campos extraídos, modo de precio, latencias y el JSON
estructurado del contrato v1.

## Estado del repositorio

- `src/homex_nlp/engine.py`: extractor determinístico activo `RulesEngine`.
- `src/homex_nlp/asr/`: validación, adaptador Faster-Whisper y servicio ASR.
- `src/homex_nlp/contracts/`: contratos Pydantic de entrada, transcripción,
  propuesta, evidencia y salida.
- `training/`: validación de corpus, conversión, configuración spaCy NER y
  evaluación reproducible.
- `schemas/`, `examples/`: JSON Schema y fixtures normativos comprobados.
- `frontend/index.html` + `tools/demo_api.py`: demostrador visual local, sin
  persistencia comercial.
- `backend/homex_trazabilidad.db`: evidencia SQLite del prototipo anterior,
  conservada fuera de la ruta activa.
- `data/raw/`, `data/curated/`, `data/manifests/`, `data/splits/`: fuentes
  verificables, copias curadas y particiones.
- `homex_bd_final_v3.sql`: referencia del futuro backend; su formalización en
  migraciones pertenece a F07/F08.

La CI instala desde el lock, revisa formato/lint, valida esquemas y corpus, ejecuta
tests y construye el wheel. No ejecuta el servidor demo ni inicializa SQLite.
