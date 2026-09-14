# Contrato de integración Django — preparación F00

Este documento fija responsabilidades; las interfaces de extracción se implementan
en F01 y Django en F07/F08. No hay endpoint comercial ni adapter nuevo ejecutable
en F00. Consultar §§6 y 9–14 del [plan](PLAN_MAESTRO_REFACTORIZACION_HOMEX.md).

## Propietarios

Django autentica, autoriza y persiste. El worker usa los servicios del backend e
instala un wheel fijado de HOMEX. El paquete entrega propuesta/evidencia y funciones
puras de comparación; no recibe credenciales ni modelos ORM. El backend transforma
el contrato rico a JSONB V1 sin perder información comercial legible.

`resultado_raw` del intento es fuente original; `items_ia` su proyección consultable.
Una corrección final por IA y una evaluación por corrección, con version_metrica.
No usar datos IA enviados por navegador como original confiable. Ni IA ni intentos
cerrados permiten alterar/borrar evidencia. No crear historia humana artificial.

## Persistencia prevista

1. Captura: clave_idempotencia UUID de frontend, única, validada contra usuario,
   proforma y contenido. Mismo POST devuelve la misma captura; conflicto de
   contenido se rechaza. Clave no equivale a autorización.
2. Intento: número único bajo bloqueo de captura. El trigger crea outbox en esa
   transacción; Django no inserta un segundo trabajo.
3. Worker: procesamiento fuera de transacciones largas; cierre condicionado por
   identidad/estado. Sin leases persistentes. Estados exactos de captura:
   PENDIENTE/PROCESANDO/COMPLETADA/ERROR; intento:
   PENDIENTE/PROCESANDO/FINALIZADO/ERROR.
4. Audio: temporal privado excluido de backups; se elimina inmediatamente tras
   transcribir. Reintentar NLP utiliza texto. Outbox no recupera audio eliminado.
5. HITL: misma transacción para corrección, evaluación, detalle/especificaciones y
   vínculo de captura. La confirmación no equivale a aprobación de proforma.

## Operaciones comerciales y migraciones

- Bloqueo común FOR UPDATE de proforma en edición y aprobación, sin versión
  optimista. Detalle no cambia de proforma. Tras aprobar, especificaciones y datos
  comerciales quedan congelados.
- Cliente editable en BORRADOR; primera ENVIADA congela cliente y snapshots.
- Añadir modo_calculo PRECIO_UNITARIO/TOTAL_NEGOCIADO e importe_negociado. El total
  negociado es autoritativo: 3 por 100 permanece 100.00. Nunca compensar redondeo
  con cantidad o descuento. Los cuatro totales se protegen en BD.
- BOB/USD explícitos sin conversión. Promoción automática de catálogo y JSON V1
  validados; sin perfiles obligatorios inventados ni CHECK general de descuento
  cero por categoría de mueble.
- Conservar aprobación por triggers: pedido+VENTA+OT. Emitir Nota de Entrega
  posteriormente para realizar la entrega; fecha de emisión, sin otro campo.
- Recibos EMITIDO→ANULADO solo por error. Datos originales inmutables. Acumulados
  actuales/saldo/sobrepago consideran solo EMITIDOS. Snapshots anteriores no se
  reescriben al anular otro recibo.
- Pedido con recibos EMITIDOS no se cancela; no hay devoluciones dentro del sistema.
  Anulación de error no simula devolución. Cobro, anulación y cancelación bloquean
  el mismo pedido. Una reversa de stock por VENTA y solo durante cancelación.

Django añadirá FK de actores a AUTH_USER_MODEL y timestamps transversales según
necesidad; no reemplaza los timestamps técnicos existentes. Las 24 tablas y sus
triggers se trasladan a migraciones una sola vez, sin ejecutar también el script
DDL contra tablas ya creadas. El SQL v3 se preserva como evidencia en F00.

## Verificación futura

Probar contrato de consumidor, JSON V1, igualdad de los dos modos de precio,
reenvíos HTTP, duplicación de mensajes, worker tardío, freeze de evidencia,
concurrencia de edición/aprobación, cobro/cancelación/anulación y unicidad de reversa.
La CI F00 solo acredita importación y distribución del paquete; no estos flujos.
