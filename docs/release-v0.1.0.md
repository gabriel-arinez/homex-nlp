# HOMEX NLP 0.1.0 — manifiesto de integración

## Identidad

- paquete: `homex-nlp`;
- versión: `0.1.0`;
- Python soportado: `>=3.11,<3.12`;
- contrato: `schema_version = "1.0"`;
- motor promovido: `RULES_ONLY`;
- ASR opcional: `faster-whisper==1.2.1`.

## Interfaces públicas para backend

```python
from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from homex_nlp.engine import RulesEngine
from homex_nlp.field_comparison import compare_fields
```

El backend puede leer `homex_nlp.__version__` para registrar la versión
instalada, pero la compatibilidad funcional se decide por `schema_version`.

## Artefactos

El build produce:

```text
homex_nlp-0.1.0-py3-none-any.whl
homex_nlp-0.1.0.tar.gz
```

CI sube ambos en un artifact cuyo nombre incluye el SHA de Git:

```text
homex-nlp-0.1.0-<commit-sha>
```

F08.0 debe fijar un commit/tag/artefacto inmutable. Una rama no es una referencia
de release válida.

## Gates

```bash
uv sync --locked --extra dev --extra asr --python 3.11.15
make check
make distribution-check
```

El segundo comando instala wheel y sdist en entornos limpios y ejecuta un smoke
test del consumidor backend.

## Límites deliberados

Esta versión no incluye:

- Django;
- PostgreSQL;
- Redis;
- Celery;
- pesos ASR;
- un modelo NER promovido;
- persistencia comercial.

Estos límites son parte de la arquitectura, no funcionalidades pendientes de
este paquete para iniciar F08.0.
