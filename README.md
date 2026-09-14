# HOMEX NLP

Refactorización incremental del componente de reconocimiento de voz y extracción
para cotizaciones HOMEX. F00 preparó el paquete, F01 definió contratos, F02
preservó ambos corpus, F03 incorporó el extractor determinístico y F04 dejó un
entrenamiento/evaluación NER reproducible. El modelo no se promovió por métricas
insuficientes; todavía no implementa ASR ni backend.

La guía es [Plan Maestro](docs/PLAN_MAESTRO_REFACTORIZACION_HOMEX.md) y el contrato
actual está en [Contrato v1](docs/contract-v1.md).
Las decisiones finales están en [requisitos](docs/requirements.md) y la evidencia
del punto de partida en [informe F00](docs/F00_PREPARACION.md).

## Entorno reproducible

Python 3.11 (baseline comprobado: 3.11.15) y uv 0.12.9. Desde la raíz:

```bash
uv sync --locked --extra dev
make check
uv build
```

`uv.lock` fija dependencias transitivas. `pyproject.toml` separa runtime de texto
(spaCy/Pydantic/click), extras `asr` y `demo`, y herramientas `dev`. No instala modelos
lingüísticos ni descarga pesos ASR. Instalar dependencias requiere acceso al índice
o una caché preparada; los tests de F00 no usan red ni modelos.

El `.venv` de la raíz es nuevo. `backend/.venv` y el experimento anterior se
conservan; no mezclar entornos ni copiar su `pip freeze` como dependencias directas.
Para fases posteriores, `uv sync --locked --extra dev --extra asr` instala el
adaptador ASR, pero su existencia como extra no significa que esté implementado.

## Estado del repositorio

- `src/homex_nlp/`: contratos Pydantic, configuración y recursos v1; sin extractor.
- `schemas/`, `examples/`: JSON Schema y fixtures normativos comprobados en CI.
- `tests/contract/`: contratos, ejemplos, schemas e importación aislada.
- `backend/`, `frontend/`: experimento previo, preservado durante F00.
- `data/raw/`, `data/curated/`, `data/manifests/`, `data/splits/`: fuentes
  verificables, copias curadas, cambios trazables y test sellado de F02.
- `homex_bd_final_v3.sql`: referencia preservada; ampliaciones finales pendientes
  de migraciones F07/F08, no esquema ya corregido.
- `docs/`: arquitectura, integración, requisitos y manifiesto del baseline.

La CI instala desde el lock, revisa formato/lint, ejecuta el contrato y construye
el wheel. También verifica su importación en un entorno separado sin dependencias.
No ejecuta el servidor experimental ni inicializa SQLite. El wheel y el sdist
excluyen el prototipo, SQLite y datasets; las fuentes se conservan en Git.
