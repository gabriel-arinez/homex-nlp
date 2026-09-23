# F06 — Distribución y cierre del alcance NLP

## Estado

**Backend-ready condicionado únicamente a CI verde y fusión a la rama canónica.**

La versión de integración es `homex-nlp 0.1.0` y el contrato externo es
`schema_version = "1.0"`.

## Artefacto distribuible

El artefacto se construye con:

```bash
uv build
```

El gate completo es:

```bash
uv sync --locked --extra dev --extra asr --python 3.11.15
make check
make distribution-check
```

`make distribution-check` verifica wheel y sdist desde entornos limpios, instala
dependencias reales y ejecuta el contrato mínimo que utilizará F08.0 del backend.

CI conserva ambos artefactos con un nombre ligado al SHA del commit. Una release
del backend debe fijar un SHA/tag/artefacto inmutable; nunca una rama flotante.

## Frontera con backend

El backend instala una versión fijada y usa únicamente la interfaz pública:

```python
from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from homex_nlp.engine import RulesEngine
```

La operación inicial es:

```python
result = RulesEngine().extract(ExtractionRequest(...))
```

El consumidor valida `schema_version == "1.0"` antes de mapear la respuesta.

Para HITL, el backend recupera su propia evidencia persistida y puede usar
`compare_fields` como cálculo puro. Este paquete no decide permisos, no recibe
modelos ORM, no persiste correcciones y no aprueba proformas.

## ASR

El extra `asr` fija `faster-whisper==1.2.1`. El paquete no descarga pesos ni
incorpora un modelo ASR. El worker del backend será responsable de proporcionar
la ruta local del modelo y de ejecutar el servicio ASR durante F08.2.

## Evidencia histórica

Los ejecutables del prototipo `backend/main.py`, `database.py`,
`nlp_engine.py`, `convert_to_spacy.py` y el frontend experimental no forman
parte de la ruta activa. La SQLite histórica se conserva solo como evidencia y
nunca se convierte en persistencia comercial.

## Condición de cierre

F06 queda cerrada para iniciar F08.0 cuando simultáneamente:

- `make check` está verde;
- `make distribution-check` está verde;
- CI del commit de integración está verde;
- wheel y sdist quedan disponibles como artifact ligado al SHA;
- el cambio está fusionado a la rama canónica;
- F08.0 fija ese commit/artefacto exacto.

No se requieren Django, Celery, Redis ni PostgreSQL dentro de este repositorio.
