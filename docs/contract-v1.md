# Contrato de extracción v1

F01 define datos intercambiables y sus invariantes. No implementa el extractor:
los archivos de `examples/expected/` son resultados normativos que F03 deberá
producir. Los JSON Schema de `schemas/` se generan desde los modelos Pydantic y se
verifican en CI con Draft 2020-12 e identificadores URN estables.

## Entrada y salida

`ExtractionRequest` conserva el texto exacto, contexto BOB/USD y tipo esperado
MUEBLE_MEDIDA. No recibe URL de audio, IDs Django ni un producto maestro. Si hay
metadatos ASR, el texto del request debe coincidir exactamente con la transcripción.

`ExtractionResult` contiene una propuesta o `null`, nunca una lista. Sus estados:

| Estado | Condición |
|---|---|
| `REQUIRES_REVIEW` | Existe exactamente una propuesta; no significa lista para aprobar. |
| `NO_PROPOSAL` | Propuesta nula y advertencia que explica ausencia, catálogo fuera de voz o multiproducto. |
| `ERROR` | Propuesta nula y error seguro; no oculta fallo como resultado vacío. |

`proposed_item_count` solo puede ser 0 o 1 por coherencia con la propuesta. Una
propuesta puede omitir cantidad, precio o dimensiones, pero cada ausencia relevante
se comunica; un objeto sin contenido se rechaza y se representa como `null`.

## Precio

El transporte usa strings decimales, no `float`. `PRECIO_UNITARIO` exige cantidad
para calcular total y valida cantidad × unitario. `TOTAL_NEGOCIADO` conserva el
total dictado; el unitario es opcional, derivado y puede llevar más de dos decimales.
Por ejemplo, 3 por 100 conserva `line_total="100.00"` y referencia `33.333333`.
La moneda del resultado debe concordar con el contexto comercial; el paquete no
convierte BOB/USD.

## Evidencia y offsets

Cada candidato tiene ID único, origen NER/RULE/PARSER, decisión y span `[start,end)`
sobre `text_original`. El contrato comprueba límites y que el slice sea idéntico.
Los IDs usados por campos/componentes deben existir. Un candidato rechazado incluye
motivo; los pendientes permanecen en `unresolved`.

Los offsets son índices de puntos de código Unicode como los usa Python. JavaScript
usa unidades UTF-16: el frontend debe convertir para resaltar, sin modificar los
offsets persistidos. Ningún proceso normaliza el texto antes de interpretar estos
índices.

## Medidas, componentes y perfiles

Medidas conservan valor/unidad/texto original y pueden incluir milímetros canónicos.
La conversión debe ser exacta. Eje y unidad pueden ser `null` para una propuesta
pendiente. Componentes tienen IDs estables dentro del resultado; dos espesores
iguales asociados a componentes distintos no se deduplican.

`furniture_profiles.json` está expresamente `UNCONFIGURED`. La ausencia de perfiles
no crea requisitos de ancho/color/espesor ni bloquea por sí sola. Cuando HOMEX los
entregue, se publicará una nueva versión del recurso y sus pruebas.

## Compatibilidad

- Agregar un campo opcional o un código de advertencia exige documentar la versión
  menor y actualizar primero consumidores estrictos.
- Quitar o renombrar campos, cambiar semántica, tipo, moneda, offsets o modo de
  precio incrementa la versión mayor del esquema/ruta.
- Una nueva versión de modelo no cambia el schema; se registra en `engine`.
- `schema_version` del contrato no es `schema_version` del JSONB comercial.
- Los consumidores validan la versión antes de deserializar y no ignoran errores.

La aplicación declara de forma explícita qué versiones acepta. No interpreta una
versión desconocida como 1.0 ni acepta automáticamente campos adicionales: los
modelos usan `extra=forbid`. Una ampliación opcional solo se despliega después de
actualizar el rango de compatibilidad del consumidor correspondiente.

El original IA procede del servidor. El navegador solo envía la corrección humana;
el comparador futuro usa valores canónicos y devuelve precisión `null` sin
denominador. La persistencia final se describe en `integration-django.md`.
