# F03 — Motor determinístico y propuesta singular

`RulesEngine` es el motor activo de esta fase. Recibe un `ExtractionRequest` y
devuelve el contrato `ExtractionResult`; no carga modelos, no usa SQLite, no crea
productos ni realiza llamadas de red. Su modo siempre es `RULES_ONLY` y declara
la versión `f03-rules-v1`.

Las reglas conservan offsets Unicode del texto original y producen candidatos
aceptados, rechazados o pendientes. Detectan producto, cantidad, precios,
dimensiones, espesores y accesorios. Una captura con catálogo de sillas/pisos o
varios productos principales devuelve `NO_PROPOSAL`; una rectificación explícita
conserva el producto anterior como evidencia rechazada y requiere revisión.

El precio con `total` se expresa como `TOTAL_NEGOCIADO`: el total dictado es la
fuente autoritativa y el unitario es solo una referencia. El patrón `a 1000 cada
uno` usa `PRECIO_UNITARIO` y calcula el total únicamente si existe cantidad.
Los formatos monetarios se parsean por completo o emiten `INVALID_PRICE`; nunca
se acepta el prefijo de una cifra malformada.

Uso local:

```bash
uv run homex-nlp --request-id prueba "dos escritorios a 1000 cada uno"
printf '%s' 'tres muebles, total 100' | uv run homex-nlp
```

La salida estándar es un único JSON. F04 podrá añadir NER bajo modo `HYBRID`,
pero deberá conservar la misma política de propuesta singular y evidencia.
