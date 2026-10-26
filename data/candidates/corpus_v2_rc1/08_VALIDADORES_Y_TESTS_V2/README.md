# Implementación única y comandos opt-in

Código versionado en `training/corpus_v2/`: `build.py`, `semantic.py`, `validate.py`,
`record.schema.json`, `recipes.json`, `private_ingest.py`, `verify_private.py`, `docbin.py`,
`report.py`, `reproduce.py`, `reconcile.py`. Tests independientes en `tests/training/test_corpus_v2.py`.
Este índice no duplica las implementaciones.

```bash
uv sync --locked --extra dev --python 3.11.15
uv run --locked --extra dev python -m training.corpus_v2.reproduce --output /tmp/homex-v2-rebuild
uv run --locked --extra dev python -m training.corpus_v2.validate /tmp/homex-v2-rebuild
uv run --locked --extra dev pytest tests/training
uv run --locked --extra dev python -m training.corpus_v2.docbin /tmp/homex-v2-rebuild /tmp/homex-v2-docbin
make corpus-check docbin-check
```

No se ejecuta train_prf04 ni se sustituye V1. Para experimentar después de homologación,
seleccionar esta raíz explícitamente y diseñar un consumidor opt-in; los consumidores actuales
siguen fijados a V1. No copiar este candidato sobre data/corpus, expected o splits.

Privados, fuera de Git: `private_ingest --sources <tres TXT> --output <directorio privado fuera de Git> --review-recipes <recetas privadas>`
y `verify_private <directorio privado>`. El ingestor rechaza un destino dentro de un checkout.
Conservar permisos 700/600. El script verifica bytes originales, rangos, cobertura de cada carácter
no blanco y exclusión de originales de supervisión. No imprime textos comerciales.
