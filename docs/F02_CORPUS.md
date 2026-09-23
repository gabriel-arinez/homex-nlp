# F02 — Corpus preservado, curado y particionado

Las fuentes se copiaron byte a byte en `data/raw/`; los manifiestos registran sus
SHA-256 y conteos. `homex_original` conserva 200 registros y 2.378 entidades;
`catalogo_sillas` conserva 19 fichas y 182 entidades. Las fuentes nunca se usan
para entrenamiento directamente.

El validador con spaCy 3.8.13 encontró 11 desalineaciones de tokens en la fuente
comercial. La copia curada es válida: sus 11 cambios están en
`data/curated/homex_original_changes.jsonl`, con límites antes/después y motivo.
No cambia ningún texto, etiqueta ni registro. Las fichas de sillas ya eran válidas
y se mantienen aisladas del corpus de muebles.

Las particiones viven en `data/splits/`, agrupan por plantilla anotada, usan una
semilla registrada y se sellan después de F02. El borrador de catálogo de sillas
no crea productos: deja SKU, precio, stock y presentación por color como datos
pendientes de revisión comercial.

Ejecutar `make corpus-check` valida ambas copias curadas. La configuración inicial
de entrenamiento está en `training/configs/ner-v1.cfg`; F04 generará DocBin y
entrenará solo con train/dev.
