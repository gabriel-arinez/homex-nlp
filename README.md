# HOMEX NLP

Componente distribuible de reconocimiento de voz y extracción de información para
cotizaciones HOMEX. F00–F06 separaron el prototipo histórico del paquete,
formalizaron contratos estrictos, corpus reproducible, motor determinístico,
evaluación NER, ASR opcional y distribución instalable.

La versión de integración actual es **`homex-nlp 0.1.0`**, con contrato
**`schema_version = "1.0"`**. El motor operativo es **`RULES_ONLY`**; el primer
modelo NER fue evaluado y no promovido por métricas insuficientes.

La guía general está en
[Plan Maestro](docs/PLAN_MAESTRO_REFACTORIZACION_HOMEX.md), el contrato público en
[Contrato v1](docs/contract-v1.md) y la frontera con Django en
[Integración Django](docs/integration-django.md).

## Entorno reproducible

Baseline: Python 3.11.15 y uv 0.12.9.

```bash
uv sync --locked --extra dev --extra asr
make check
make distribution-check
```

`make distribution-check` construye wheel y sdist, los instala por separado en
entornos limpios con sus dependencias y ejecuta un smoke test equivalente al
consumidor de F08.0 del backend.

## Contrato para HOMEX Backend

El backend consume el paquete como dependencia inmutable. No debe importar
módulos internos fuera de las interfaces públicas documentadas ni usar una rama
flotante como dependencia de release.

Interfaz NLP v1:

```python
from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from homex_nlp.engine import RulesEngine

request = ExtractionRequest(
    request_id="...",
    text="tres muebles, total 100",
    currency_context="BOB",
)
result: ExtractionResult = RulesEngine().extract(request)
```

F08.0 debe validar `result.schema_version == "1.0"` antes de mapear la salida al
dominio Django. El paquete no autentica, no autoriza, no conoce modelos ORM y no
persiste información comercial.

Para HITL existe `homex_nlp.field_comparison.compare_fields` como función pura;
el original IA siempre debe recuperarse desde evidencia persistida por el backend.

## ASR

Faster-Whisper es opcional:

```bash
uv sync --locked --extra asr
```

El paquete **no descarga pesos automáticamente**. El consumidor proporciona una
ruta local absoluta al modelo. El adaptador ASR es perezoso y no carga el modelo
al importar el paquete.

El modelo ASR, Redis, Celery, Django y PostgreSQL no forman parte de la
distribución base de `homex-nlp`.

## Estado del repositorio

- `src/homex_nlp/contracts/`: contratos Pydantic públicos y estrictos.
- `src/homex_nlp/engine.py`: `RulesEngine` operativo en `RULES_ONLY`.
- `src/homex_nlp/asr/`: validación, servicio y adaptador Faster-Whisper opcional.
- `training/`: corpus, entrenamiento y evaluación NER reproducibles.
- `schemas/`, `examples/`: JSON Schema y fixtures contractuales.
- `tests/contract/`: contrato, schemas y smoke de consumidor backend.
- `backend/homex_trazabilidad.db`: evidencia histórica SQLite fuera de la ruta activa.
- `docs/`: arquitectura, decisiones, configuración e integración.

## CI y artefactos

Cada push/PR ejecuta calidad, esquemas, corpus, tests y
`make distribution-check`. Si todo pasa, CI publica como artifact el wheel y el
sdist con nombre que incluye el SHA del commit:

```text
homex-nlp-0.1.0-<commit-sha>
```

Eso permite a F08.0 seleccionar un artefacto y commit exactos. El backend no debe
depender de `refactor`, `main` u otra rama flotante.

El manifiesto de la primera versión consumible está en
[release 0.1.0](docs/release-v0.1.0.md).
