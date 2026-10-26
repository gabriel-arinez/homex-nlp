# Reproducción y evidencia

Entorno: Python 3.11.15, spaCy 3.8.13; dependencias del uv.lock base sin cambios.
Resultados ejecutados en ese entorno (repetidos en el cierre):

| Comando/control | Resultado |
|---|---|
| `pytest -q` | 277 aprobadas, incluye 26 pruebas V2 |
| `pytest tests/training` | 43 aprobadas al cierre |
| `make corpus-check docbin-check` | cuatro corpus V1 válidos; 675 DocBin V1 |
| `corpus_v2.validate` | 727/727 registros y referencias, cero errores |
| `corpus_v2.docbin` | 727/727 roundtrip, sin entrenamiento |
| `ruff check` y `ruff format --check` | aprobados |
| `export_schemas.py --check` | aprobado |
| dos reconstrucciones limpias | mismos bytes y hashes |
| V1, runtime y consumidores protegidos | hashes y diff sin cambios |
| `verify_private` | 3/3 originales, 120 ítems, 4 parciales, cero supervisados |
| `git diff --check` | aprobado |

La evidencia detallada de comandos, códigos de salida, entorno y hashes se entrega bajo evidence/
en el bundle privado. Las pruebas registradas se ejecutaron sobre este candidato, no se predicen.

```bash
uv run --locked --extra dev python -m training.corpus_v2.reproduce --output /tmp/homex-v2-rebuild-a
uv run --locked --extra dev python -m training.corpus_v2.reproduce --output /tmp/homex-v2-rebuild-b
uv run --locked --extra dev python -m training.corpus_v2.validate /tmp/homex-v2-rebuild-a
uv run --locked --extra dev pytest -q
make corpus-check docbin-check
uv run --locked --extra dev ruff check src tests tools training
uv run --locked --extra dev ruff format --check src tests tools training
uv run --locked --extra dev python tools/export_schemas.py --check
git diff --check
```

La reconstrucción de datos/documentación es determinista. Hashes en sha256.json cubren exactamente
los archivos del candidato salvo ese propio manifiesto. baseline_v1_sha256.json fija todos los
archivos V1, incluidos expected/splits/manifiestos. Las fechas de ejecución y resultados de comandos
se separan del dataset para no alterar sus hashes. Dos reconstrucciones desde cero deben coincidir
byte por byte con el candidato. No se entrena, evalúa RULES_ONLY en test ni mide WER.

El workflow base entrena NER y construye paquetes automáticamente en push/PR.
Este encargo prohíbe entrenamiento: los commits de publicación llevan [skip ci] para no dispararlo.
No se modifica el workflow; verificación local sí ejecutada, CI remoto de este candidato no afirmado.
No se construyeron wheels nuevos por este trabajo. PR solo draft, sin merge ni despliegue.
