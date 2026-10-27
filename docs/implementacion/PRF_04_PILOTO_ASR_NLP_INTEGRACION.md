# HOMEX PRF-04 — Replay aislado ASR→NLP del piloto real

## Alcance y fuente de verdad

El PR #26 produce `run.json` privado a partir de los 20 WAV reales y reutiliza
el benchmark #23. El PR #25, commit exacto
`eae7b003cc2932a21823efb17d1c32ec07e94ecc`, implementa el
correctivo determinístico v13 de productos, repeticiones, precios y anomalías observadas en audios 02/05.
Esta herramienta une **las salidas ASR ya obtenidas** y ese motor NLP,
sin transcribir de nuevo, sin hacer merge, sin instalar otro wheel, sin
guardar proformas y sin tocar el backend.

La rama que contiene esta integración parte del PR #26. Codex prepara
HUMAN_GOLD/WER en otra rama; esta herramienta **no** escribe ni lee esas
anotaciones, no asigna WER y no acredita comparación con los 22 intentos
históricos ni con un holdout.

## Preparación (solo una vez)

Usar dos worktrees independientes. El del PR #25 debe estar
**desacoplado y limpio** en el SHA exacto. El del PR #27 contiene la
herramienta, dependencias y contratos del PR #26.

```bash
git -C "$HOME/HOMEX/homex-nlp" fetch origin \
  feat/prf04-piloto-asr-nlp-integration-20261026 \
  fix/prf04-piloto-real-v13-reconocimiento-precios-20261026

git -C "$HOME/HOMEX/homex-nlp" worktree add --detach \
  "$HOME/Descargas/homex-piloto-asr-nlp-pr27" \
  origin/feat/prf04-piloto-asr-nlp-integration-20261026

git -C "$HOME/HOMEX/homex-nlp" worktree add --detach \
  "$HOME/Descargas/homex-piloto-nlp-pr25-fijado" \
  eae7b003cc2932a21823efb17d1c32ec07e94ecc

cd "$HOME/Descargas/homex-piloto-asr-nlp-pr27"
uv sync --locked --extra dev
uv run --locked --extra dev pytest -q tests/training/test_audio_pilot_nlp_replay.py
```

Comprobar que los dos directorios aún no existen antes de crear los
worktrees. Si ya existen, **verificar su SHA y estado** en vez de
sobrescribirlos. No ejecutar `git reset` ni limpiar archivos locales.

## Ejecutar con la evidencia ASR REAL

Usar `--asr-run-dir` con el directorio **privado** de una corrida
ASR del PR #26, que contenga `run.json` íntegro. No usar el ZIP
público, `summary.json` aislado ni datos sintéticos.

```bash
cd "$HOME/Descargas/homex-piloto-asr-nlp-pr27"
uv run --locked --extra dev python -m training.audio_pilot.nlp_replay \
  --asr-run-dir "/RUTA/PRIVADA/CORRIDA_ASR_PR26" \
  --nlp-source-dir "$HOME/Descargas/homex-piloto-nlp-pr25-fijado/src" \
  --expected-nlp-commit eae7b003cc2932a21823efb17d1c32ec07e94ecc \
  --currency BOB \
  --output-dir "$HOME/Descargas/homex-piloto-integracion-20-$(date +%Y%m%d-%H%M%S)"
```

**No crear ni publicar rutas reales de evidencia a GitHub.** El comando
no necesita PostgreSQL ni descarga de modelos. La carpeta de salida
se crea con permisos 0700 y sus JSON con permisos 0600, fuera del
repositorio. No se permite sobrescritura.

`summary-private.json` declara los 20 estados y las huellas de
ASR/NLP. `details-private.json` conserva exclusivamente en local el
texto ASR original y las propuestas NLP para revisión humana.
El stdout solo informa conteos y errores seguros, sin transcripciones.

## Gates

- Rechazar corridas parciales, faltantes, duplicados y datos sintéticos.
- Rechazar motor diferente, checkout sucio o fuente de módulo inesperada.
- No inferir WER, HUMAN_GOLD, independencia, promoción ni exactitud comercial.
- No escribir modelos, base de datos, catálogo, proformas ni usuario.
- No publicar `run.json`, `details-private.json` o audios en CI/Git.

**Siguiente etapa, no cubierta:** conectar el motor probado al backend
en un laboratorio aislado, probar guardado en PostgreSQL y verificar
interacción real de la UI. Tampoco se afirma equivalencia temporal o
de identidad con las 22 capturas históricas.
