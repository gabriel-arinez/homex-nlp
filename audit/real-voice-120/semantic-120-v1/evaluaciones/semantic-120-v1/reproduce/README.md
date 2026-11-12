# Reproduce the semantic audit without overwriting evidence

Run from the homex-nlp checkout containing baseline Git object `b851b5a` and the final0.1.22 source. Supply the original local corpus and hashed Whisper Small model separately; neither is distributed in Git. These commands create a new run, not a replacement of observed results.

```bash
CORPUS="$HOME/Descargas/HOMEX_Guiones_Evaluacion_Voz"
MODEL="$HOME/modelos/faster-whisper-small"
RUN=$(mktemp -d "$CORPUS/evaluaciones/semantic-reproduction-XXXXXX")
LOGS=$(mktemp -d "$CORPUS/logs/semantic-reproduction-XXXXXX")
BASE="$CORPUS/evaluaciones/audit-120/baseline-routing-v2/cases"
VALUES="$CORPUS/evaluaciones/audit-120/catalog-fixture.json"
uv sync --locked --extra dev --extra asr
make check > "$LOGS/check.log" 2>&1
SOURCE_DATE_EPOCH=0 uv build
UV_OFFLINE=1 .venv/bin/python tools/verify_distribution.py > "$LOGS/distribution.log" 2>&1
.venv/bin/python -m tools.annotate_real_voice --corpus "$CORPUS" \
  --baseline "$BASE" --output "$RUN/references" > "$LOGS/references.log" 2>&1
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m tools.experiment_real_voice_asr \
  --corpus "$CORPUS" --model "$MODEL" --output "$RUN/asr-experiments" \
  > "$LOGS/asr.log" 2>&1
.venv/bin/python -m tools.evaluate_semantic_voice --references "$RUN/references" \
  --original-asr "$BASE" --candidate-asr "$RUN/asr-experiments" --values "$VALUES" \
  --output "$RUN/comparison" > "$LOGS/comparison.log" 2>&1
```

Five full CPU decode settings took approximately58minutes in the observed mixed workload. Timing is diagnostic, not a dedicated benchmark. Exact settings, model hashes, software versions, CPU/wall and process-peak memory are in each run's identity/case artifacts. Original fallback-temperature ASR remains frozen. Do not pass references as prompts, select the best configuration per case, or feed original recordings to a deleting CLI.

The annotation output is proposals with explicit verification state. Human acoustic/association denominators remain zero until actual review. All120 recordings are development data; follow `references-v2/holdout-protocol.json` for new independent recordings, with connected family/source grouping.

## Actual backend and browser reproduction

See `../integration-v3/reproduce/README.md` and its `bootstrap-v3.sh`. It archives pinned backend7040564 and frontendfeece0a into a new private scratch, reinstalls the local wheel into a copied dependency environment, generates fresh credentials and runs eight real audio scenarios. It does not reuse the original live session or change production. The portable wrapper was structurally checked, not rerun after portability changes; observed integration-v3 itself passed8/8.

## Safety and scope

Historical `references/`, `comparison-v1` through `v4`, failed console runs and old integrations are retained. Current references are `references-v2`; final source comparison is `comparison-v5`. Source/export hashes and all omissions/redactions are listed in the publication manifest. Private replay clips and full large traces stay local; public trace text events are sanitized, not complete screencast archives. Source/product specifications were retained; no source recording, credential or productive database is published.
