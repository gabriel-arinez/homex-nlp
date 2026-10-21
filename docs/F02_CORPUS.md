# Corpus operativo PRF-04

Las cuatro fuentes activas están en `data/corpus/`; sus particiones selladas en
`data/splits/`, las etiquetas en `data/manifests/prf04_labels.json` y las referencias
estructuradas en `data/expected/`. Véase `training/policies/annotation_guide.md`.

El inventario PRF-04 documenta la sustitución de las fuentes históricas por los
675 ejemplos autorizados por el usuario el 21-10-2026. Las evidencias F02 previas
se consultan en Git; sus rutas ya no constituyen instrucciones operativas.

Verificación: `make corpus-check docbin-check` y `uv run pytest tests/training`.
