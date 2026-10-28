#!/usr/bin/env bash
# Six private inputs: originals (3), adjudications, certificates, oral reviews.
set -euo pipefail
umask 077
if [ "$#" -ne 6 ]; then
    echo 'USO: bash tools/run_integral_offline5.sh ORIGINAL1 ORIGINAL2 ORIGINAL3 ADJUDICATIONS CERTIFICATES ORAL_REVIEWS' >&2
    exit 2
fi
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
if [ -n "$(git status --porcelain)" ]; then
    echo 'BLOQUEADO: guardar el código y congelar un worktree limpio antes de entrenar.' >&2
    exit 2
fi
if [ "$(git branch --show-current)" != 'codex/corpus-v2-final' ]; then
    echo 'BLOQUEADO: este cierre requiere la rama autorizada del PR #37.' >&2
    exit 2
fi
SCANNER="${GITLEAKS_BIN:-gitleaks}"
if ! command -v "$SCANNER" >/dev/null 2>&1; then
    echo 'BLOQUEADO: configurar GITLEAKS_BIN con el ejecutable de auditoría.' >&2
    exit 2
fi
RUN="$(mktemp -d "$HOME/Descargas/HOMEX_V2_OFFLINE5_FINAL_XXXXXXXX")"
echo "EVIDENCIA_PRIVADA=$RUN"
if bash -euo pipefail -s -- "$REPO" "$RUN" "$SCANNER" "$@" > "$RUN/execution.log" 2>&1 <<'RUN_SCRIPT'
    REPO="$1"
    RUN="$2"
    SCANNER="$3"
    shift 3
    cd "$REPO"
    export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONHASHSEED=0
    date -Is
    git rev-parse HEAD
    for DEST in corpus rebuild; do
        uv run --locked --extra dev --extra asr python -m training.integral_v2.build \
            --sources "$1" "$2" "$3" --adjudications "$4" --certificates "$5" \
            --oral-reviews "$6" --output "$RUN/$DEST"
        uv run --locked --extra dev --extra asr python -m training.integral_v2.validate "$RUN/$DEST" --training
    done
    cmp "$RUN/corpus/sha256.json" "$RUN/rebuild/sha256.json"
    uv run --locked --extra dev --extra asr python -m training.integral_v2.verify_prf03 \
        --bundle "$RUN/corpus" --backend "${BACKEND_PRF03_GIT:-$HOME/HOMEX/homex-backend}" \
        --report "$RUN/backend-structural.json"
    make check docbin-check distribution-check
    uv run --locked --extra dev pytest tests/operations/test_f10_runtime.py -q
    uv audit --locked
    "$SCANNER" git --log-opts="origin/main..HEAD" --no-banner --redact
    uv run --locked --extra dev --extra asr python -m training.integral_v2.experiment run \
        --bundle "$RUN/corpus" --output "$RUN/models"
    uv run --locked --extra dev --extra asr python -m training.integral_v2.validate "$RUN/corpus" --training
    git diff --check
    test -z "$(git status --porcelain)"
    echo 'BUILD_VALIDATION_TRAINING_EVALUATION=PASS'
RUN_SCRIPT
then
    RESULT=PASS
else
    RESULT=FAIL
fi
# Also protect logs/outputs created by subprocesses with their own defaults.
find "$RUN" -type d -exec chmod 700 {} +
find "$RUN" -type f -exec chmod 600 {} +
echo "RESULTADO=$RESULT"
echo "LOG_PRIVADO=$RUN/execution.log"
[ "$RESULT" = PASS ]
