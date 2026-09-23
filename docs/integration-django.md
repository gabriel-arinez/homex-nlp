# Contrato de integración Django — HOMEX NLP 0.1.0

Este documento fija la frontera que debe utilizar F08 del backend. Las interfaces
de extracción están definidas por el [contrato v1](contract-v1.md).

## Propietarios

Django autentica, autoriza, coordina casos de uso y persiste. El worker pertenece
al backend e instala una versión inmutable de HOMEX NLP.

`homex-nlp`:

- transforma texto/ASR en propuesta y evidencia;
- expone contratos Pydantic v1;
- ofrece comparación HITL pura;
- no recibe credenciales;
- no conoce modelos ORM;
- no persiste datos comerciales;
- no aprueba proformas;
- no publica trabajos en Redis.

## Interfaz pública soportada para F08.0

El consumidor puede depender de:

```python
import homex_nlp
from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from homex_nlp.engine import RulesEngine
from homex_nlp.field_comparison import compare_fields
```

No debe importar helpers internos de `rules.py`, recursos privados ni módulos de
entrenamiento.

Contrato inicial:

- paquete: `homex-nlp 0.1.0`;
- Python: 3.11;
- `schema_version`: `1.0`;
- modo operativo: `RULES_ONLY`;
- una captura produce cero o una propuesta;
- moneda: BOB/USD explícita, sin conversión.

F08.0 debe fallar explícitamente ante una versión de esquema no soportada. No debe
renombrar campos públicos del contrato externo.

## Flujo NLP

```text
texto confiable del servidor
        ↓
ExtractionRequest
        ↓
RulesEngine
        ↓
ExtractionResult
        ↓
validación schema_version
        ↓
adapter/mapper Django
        ↓
persistencia del backend
```

`resultado_raw` del intento es la evidencia original del servidor; `items_ia`
es su proyección consultable. El navegador nunca vuelve a enviar el original IA
como autoridad.

## Persistencia prevista

1. Captura: `clave_idempotencia` UUID validada contra usuario, proforma y
   contenido. Mismo POST compatible recupera la captura; conflicto se rechaza.
2. Intento: número único bajo bloqueo de captura. El trigger crea outbox en esa
   transacción; Django no inserta un segundo trabajo.
3. Worker: procesamiento fuera de transacciones largas; estados de captura:
   PENDIENTE/PROCESANDO/COMPLETADA/ERROR; intento:
   PENDIENTE/PROCESANDO/FINALIZADO/ERROR.
4. Audio: temporal privado excluido de backups y eliminado inmediatamente tras
   ASR. Reintentar NLP reutiliza texto.
5. HITL: corrección, evaluación, detalle/especificaciones y vínculo de captura en
   la misma transacción. Confirmar captura no aprueba la proforma.

## ASR y worker

F08.2 instala el extra `asr` en el worker. El paquete no descarga el modelo; el
backend/deploy aporta una ruta local absoluta y controla su ciclo de vida.

Redis y Celery son infraestructura del backend. Redis nunca es fuente de verdad.

## Operaciones comerciales

- Bloqueo común `FOR UPDATE` de proforma en edición y aprobación.
- Cliente editable en BORRADOR; primera ENVIADA congela cliente y snapshots.
- `PRECIO_UNITARIO` y `TOTAL_NEGOCIADO` mantienen su semántica exacta.
- BOB/USD explícitos sin conversión.
- Aprobación comercial sigue siendo independiente del HITL.
- Pedido con recibos EMITIDOS no se cancela.

Las migraciones Django son la fuente operativa; el SQL histórico no se ejecuta
encima de tablas creadas por migraciones.

## Pruebas de consumidor obligatorias en F08.0

- importación sin side effects;
- versión de paquete fijada;
- `schema_version == "1.0"` aceptada;
- versión desconocida rechazada explícitamente;
- fixture/resultado v1 se transforma sin perder evidencia;
- JSON v1 hace roundtrip estricto;
- backend no exige NER experimental;
- backend no depende de internals de `homex-nlp`.

El repositorio NLP incluye `tests/contract/test_backend_consumer.py` y el smoke
de distribución como contrato mínimo previo.
