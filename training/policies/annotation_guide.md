# Anotación PRF-04

Las únicas fuentes operativas son los cuatro JSONL de `data/corpus/`. El usuario
confirmó el 21-10-2026 que los 675 registros son su fuente de trabajo y que varios
son originales. `metadata.fuente_autorizada_prf04` registra esta decisión sin
reescribir la procedencia previa por registro. No equivale a audio real revisado.

Offsets Unicode Python `[start,end)` sobre texto literal inmutable; etiquetas
permitidas en `data/manifests/prf04_labels.json`. `COMPONENTE` identifica piezas;
`CANTIDAD` representa exclusivamente cantidad comercial. La cantidad interna
se conserva en la referencia semántica como `cantidad_interna`, asociada a una
pieza: `CANTIDAD_INTERNA` no pertenece a las 24 etiquetas NER del manifiesto.
El DTO de candidatos puede transportarla como evidencia auxiliar sin ampliar
el esquema de entrenamiento. Material, color, acabado y espesor no se propagan entre ámbitos.
`PRECIO_TOTAL` y `PRECIO_UNITARIO` conservan significados distintos.

Las referencias de `data/expected/` tienen ID y hash de fuente. Se generan desde
anotaciones, independientemente del motor operativo, y declaran explícitamente
que requieren revisión de dominio antes de tratarlas como gold humano. No se
publican como métricas de productividad ni se usan para promover un modelo.

Las particiones existentes se conservaron por familia y se sellaron con hash.
No cambiar familias, texto o anotaciones tras observar test para ajustar un
candidato; una nueva edición de corpus requiere una versión y evaluación nueva.

`make corpus-check docbin-check` valida las cuatro fuentes. Los originales
anteriores, sus scripts exclusivos y copias se retiraron del árbol operativo;
el inventario previo conserva hashes/conteos y Git conserva contenido histórico.
