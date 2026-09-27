# NLP F09 — Cierre formal de integración Vue/backend/NLP

## Estado

**Implementación documental y evidencia contractual completadas y validadas local y remotamente. La rama está lista para fusionarse a `main`; el merge completa el cierre formal de F09.**

Esta fase no cambia el extractor, no promueve NER, no modifica `contract-v1` y no vuelve a entrenar modelos. Su objetivo es cerrar desde `homex-nlp` que el artefacto ya distribuido fue consumido correctamente por el sistema HOMEX real.

Referencias inmutables:

- fuente canónica del artefacto NLP: `b5fe2921320c9031f6d44dc5c91a18411daa393e`;
- frontend FE08 fusionado: `57c32d3aa2c2e46fbcc7136f6a90995b67c664ea`;
- backend F09 fusionado: `0659dc553af15b2125fad9b4ac0579669916e77b`.

La evidencia estructurada se conserva en [`integration-system-v0.1.0.json`](integration-system-v0.1.0.json) y tiene pruebas contractuales propias.

## Artefacto consumido por backend

Backend fija el paquete mediante tres controles concurrentes:

| Propiedad | Valor fijado |
|---|---|
| paquete | `homex-nlp==0.1.0` |
| fuente | `vendor/homex_nlp-0.1.0-py3-none-any.whl` |
| SHA-256 | `cfacc3a987f6158f43934cb64304fa50ea3e577cfa576f3db1e6d2a9576d19e6` |
| commit fuente documentado | `b5fe2921320c9031f6d44dc5c91a18411daa393e` |
| Python | 3.11 |
| contrato | `schema_version == "1.0"` |
| modo | `RULES_ONLY` |

`homex-backend` declara la versión exacta en `pyproject.toml`, apunta al wheel versionado mediante `[tool.uv.sources]` y conserva el mismo SHA-256 en `uv.lock`. El backend no instala una rama flotante ni depende de un checkout hermano.

El wheel fijado contiene el mismo código importable `homex_nlp` que el commit canónico. Un build posterior puede producir bytes distintos en el contenedor wheel por metadata de distribución o timestamps; la identidad desplegada es el SHA-256 del wheel efectivamente versionado en backend, no el hash de una reconstrucción posterior.

## Compatibilidad con contract-v1

La frontera integrada permanece exactamente en:

```python
from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from homex_nlp.engine import RulesEngine
from homex_nlp.field_comparison import compare_fields
```

Backend F08.0/F09 comprueba:

- `homex_nlp.__version__ == "0.1.0"`;
- `schema_version == "1.0"` antes del mapeo;
- `engine.mode == "RULES_ONLY"`;
- JSON v1 estricto, sin campos extra;
- rechazo explícito de versión, schema y modo desconocidos;
- uso exclusivo de APIs públicas;
- transformación al dominio Django sin renombrar el contrato externo;
- conservación de `resultado_raw` como evidencia original.

Las pruebas propias `tests/contract/test_backend_consumer.py` siguen demostrando extracción y roundtrip del consumidor mínimo. F09 añade `tests/contract/test_system_integration_evidence.py` para fijar las revisiones, CI y límites de autoridad demostrados por el sistema completo.

## Flujo integrado demostrado

La evidencia de FE08 y Backend F09 cubre el recorrido real:

```text
Vue /capturas/nueva
→ MediaRecorder
→ multipart/form-data
→ Django HTTP 202
→ PostgreSQL: captura + intento + outbox
→ Redis
→ Celery worker
→ faster-whisper-base
→ texto transcrito persistido
→ eliminación del audio temporal
→ homex-nlp 0.1.0 RULES_ONLY
→ ExtractionResult v1 / REQUIRES_REVIEW
→ resultado_raw + ItemIA
→ revisión humana HITL
→ ItemHumano
→ detalle + EspecificacionMueble
→ vínculo captura → detalle
→ proforma permanece BORRADOR
```

No es un smoke con dobles:

- Playwright opera la UI fusionada;
- Django usa PostgreSQL real;
- el outbox nace en PostgreSQL;
- Redis y Celery son procesos reales;
- ASR ejecuta `faster-whisper-base` sobre audio generado para el gate;
- el worker instala el wheel fijado de `homex-nlp`;
- un verificador posterior consulta la evidencia persistida;
- el directorio temporal de audio debe quedar vacío.

## Autoridad y límites confirmados

### NLP sólo propone

`homex-nlp` recibe texto y contexto, y devuelve una propuesta con evidencia. No recibe credenciales, no importa modelos Django, no escribe PostgreSQL, no publica en Redis y no conoce stock, permisos, pedidos o estados comerciales.

`REQUIRES_REVIEW` significa que existe una propuesta revisable. No significa aprobación, aceptación contractual ni autorización de stock.

### HITL no aprueba la proforma

Django recupera `resultado_raw` desde su propia evidencia; el navegador envía únicamente la corrección humana. La confirmación HITL persiste `ItemHumano`, detalle, especificación y vínculo con la captura dentro de la transacción backend.

Backend F09 exige después de confirmar:

```text
estado proforma = BORRADOR
```

La transición `ENVIADA → APROBADA`, la creación del pedido, el descuento de stock y la OT siguen siendo acciones comerciales separadas y protegidas por Django/PostgreSQL.

### PostgreSQL conserva la autoridad

PostgreSQL mantiene capturas, intentos, outbox, evidencia IA, corrección humana y línea comercial. Redis sólo transporta identidades de trabajo. Una respuesta aceptada por Redis sin persistencia final no satisface el gate.

### No existe audio histórico

El archivo se mantiene en almacenamiento temporal privado únicamente hasta que ASR produce y persiste la transcripción. Después se elimina antes de ejecutar NLP. La verificación F09 exige:

- transcripción ASR presente en PostgreSQL;
- versión ASR registrada;
- captura `COMPLETADA` e intento `FINALIZADO`;
- cero archivos restantes en `HOMEX_AUDIO_TEMP_ROOT`.

El audio no forma parte de `homex-nlp`, media persistente, documentos, R2 ni backups.

## Evidencia remota referenciada

### Frontend FE08

- commit funcional/documental: `3661d43e7374131f3ed34a0b375102860c406d6a`;
- merge a `main`: `57c32d3aa2c2e46fbcc7136f6a90995b67c664ea`;
- GitHub Actions sobre el commit fusionado a `main`: run `36328986617`;
- resultado: **11/11 jobs verdes**;
- integración real: **2 passed**.

### Backend F09

- commit funcional: `e6cf01ba3bc6e7c381fff2866c0ae66229311ab3`;
- merge a `main`: `0659dc553af15b2125fad9b4ac0579669916e77b`;
- GitHub Actions sobre el commit fusionado a `main`: run `36333805267`;
- resultado: **10/10 jobs verdes**;
- PostgreSQL: **175 passed**;
- concurrencia: **12 passed**;
- E2E Vue/backend: **2 passed**;
- OpenAPI frontend/backend: equivalente;
- evidencia final: `f09-frontend-backend-ok`;
- documentos/media: `f09-public-surfaces-ok`.

Esta fase referencia esos gates inmutables. No los copia a CI de `homex-nlp`, porque Django, PostgreSQL, Redis y Celery pertenecen al backend. Duplicar el stack aquí crearía dos orquestaciones del mismo recorrido y debilitaría la propiedad de cada repositorio.

## Validación propia de homex-nlp

Los gates de este repositorio siguen siendo:

```bash
uv sync --locked --extra dev --extra asr --python 3.11.15
make check
make distribution-check
```

Validan:

- Ruff y formato;
- JSON Schemas;
- corpus curado y manifiestos;
- suite contractual/unitaria;
- construcción de wheel y sdist;
- instalación de cada artefacto en entornos limpios;
- smoke del consumidor backend.

La evidencia F09 añade comprobaciones del manifiesto de integración, pero no altera el paquete distribuido ni sus APIs públicas.

## Evidencia propia F09

- `make check`: verde;
- suite propia: **43 passed**;
- pruebas nuevas del manifiesto sistémico: **3 passed**;
- Ruff: verde;
- formato Ruff: verde;
- JSON Schemas v1: sin drift;
- corpus original: **200 registros, 2378 entidades, 0 errores**;
- catálogo de sillas: **19 registros, 182 entidades, 0 errores**;
- `make distribution-check`: verde;
- wheel instalado en entorno limpio: `backend-consumer-smoke: OK`;
- sdist instalado en entorno limpio: `backend-consumer-smoke: OK`;
- documentación y manifiesto F09 incluidos en el sdist;
- `git diff --check`: limpio;
- CI de la rama publicada: run `36335111789`, job `package` verde.

No se modificó ningún archivo bajo `src/homex_nlp`, schema público, recurso del motor, corpus o configuración de entrenamiento.

## Condición de cierre

NLP F09 queda formalmente cerrado cuando:

1. `make check` pasa local y remotamente;
2. `make distribution-check` pasa;
3. el manifiesto de evidencia permanece verde;
4. CI de esta rama termina verde;
5. el documento queda fusionado a `main`.

F10 — despliegue reproducible y recuperación pertenece al repositorio de despliegue y no se adelanta aquí.
