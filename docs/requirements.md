# Matriz de requisitos finales — F01

Autoridad: respuestas finales del usuario G01–G03, T01–T09 y P29–P32. Sustituyen
propuestas incompatibles previas; no implican que el SQL v3 ya implemente cambios.
F00 implementó preparación; F01 materializa contratos/configuración. El plan
detalla las fases restantes.

| ID | Regla | Destino/fase | Criterio de aceptación |
|---|---|---|---|
| G01/P29 | Dos modos PRECIO_UNITARIO/TOTAL_NEGOCIADO | Contrato F01; precios/BD F07 | 3 por 100 = 100.00 exacto; unitario derivado nunca recalcula total negociado. |
| G02/P30 | Nota al emitir para entregar, no al aprobar | Entregas F07/F09 | LISTO_ENTREGA → emitir nota única, fecha de emisión; confirmación física separada. |
| G03/P31 | Cancelación bloqueada con EMITIDOS; error se ANULA | Recibos/pedidos F07 | Solo EMITIDOS suman; no borrar ni devolver dentro del sistema. |
| T01 | Totales protegidos en BD | SQL F07 | UPDATE arbitrario de total/subtotal/descuento_total rechazado o recalculado. |
| T02 | Cliente/snapshot congelados desde primera ENVIADA | Proforma F07 | BORRADOR editable; luego no cambiar cliente ni snapshot. |
| T03 | Detalle no migra; especificaciones congeladas al aprobar | SQL F07 | Reasignación y edición/borrado posterior rechazados. |
| T04 | FOR UPDATE de proforma | Servicios/SQL F07 | Edición y aprobación serializadas con dos conexiones, sin versión optimista. |
| T05 | Una REVERSA_VENTA por venta, solo en cancelación | Inventario F07 | Mismo producto/VENTA, cantidad completa; carrera no duplica reversa. |
| T06 | Recibo inmutable salvo EMITIDO→ANULADO | Recibos F07 | No UPDATE comercial, DELETE, traslado ni cobro de cancelado. |
| T07 | IA e intentos cerrados inmutables | Capturas F08 | No UPDATE/DELETE IA ni mutación de input/modelo/relaciones/resultado cerrado. |
| T08 | Promoción/JSON validados; perfiles flexibles | Validación F01/F07 | Sin obligatorios inventados ni restricción de descuento cero por categoría. |
| T09 | clave_idempotencia UNIQUE de frontend | Capturas F08 | Reenvío idéntico recupera captura; distinto contenido/actor/proforma no la reutiliza. |
| P32 | Producto/SKU por presentación con stock propio | Catálogo F07 | Sin variantes ni truncamiento de colores; carga exige mapa de SKU real. |
| P21 | Audio temporal, borrado inmediato tras ASR | ASR F05, backend F08 | Sin backup/consulta histórica; errores con TTL acotado. |
| P22 | Stock general; pendientes solo referencia | Inventario F07 | Stock 8, pendientes 3, referencia 5; no reserva. |
| P27 | Cobros solo desde pedido confirmado | Recibos F07 | No pago sobre proforma sin pedido. |
| P28 | Validación comercial distinta de técnica NER | Corpus F02 | Offsets/tokenizador validados antes de entrenar. |
| CONTRACT-02 | Importación sin efectos externos | F00 | Wheel importable sin dependencias, red, DB, modelos ni escritura. |
| CONTRACT-01 | Contrato y ejemplos versionados | F01 | Pydantic estricto, cinco JSON Schema vigentes y siete fixtures validados. |

## Insumos que siguen faltando

SKU/precio/color/stock real de sillas; catálogo de pisos/OTRO/promociones; documentos
físicos para validar plantillas; sesiones/referencias para demostrar desempeño.
Los perfiles de muebles son útiles pero no bloqueantes. RPO/RTO y retención formal
se definen antes de producción/piloto; no bloquean desarrollo.

No quedan preguntas empresariales bloqueantes para F00. No ampliar política de
descuentos de muebles por inferencia: T08 retira su restricción automática, sin
crear un nuevo flujo de descuentos manuales.
