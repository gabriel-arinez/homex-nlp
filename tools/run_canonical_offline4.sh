#!/usr/bin/env bash
# Rebuild and train only in private storage; never installs a production model.
set -euo pipefail
umask 077

if [ "$#" -ne 3 ]; then
    echo 'USO: bash tools/run_canonical_offline4.sh PROFORMAS.txt SILLAS-PISOS-OTROS.txt "inventario de sillas.txt"' >&2
    exit 2
fi

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
if [ -n "$(git status --porcelain)" ]; then
    echo "BLOQUEADO: worktree con modificaciones." >&2
    exit 2
fi
if ! grep -q 'VERSION = "2.0.0-offline.4"' training/canonical_v2/build.py; then
    echo "BLOQUEADO: generador offline.4 no disponible." >&2
    exit 2
fi

verify_source() {
    local source_path="$1"
    local source_name="$2"
    local expected_hash="$3"
    if [ ! -f "$source_path" ] || [ "$(basename "$source_path")" != "$source_name" ]; then
        echo "BLOQUEADO: fuente original ausente o nombre incorrecto: $source_name" >&2
        exit 2
    fi
    local actual_hash
    actual_hash="$(sha256sum "$source_path" | cut -d ' ' -f1)"
    if [ "$actual_hash" != "$expected_hash" ]; then
        echo "BLOQUEADO: SHA-256 distinto de la fuente original $source_name" >&2
        exit 2
    fi
}
verify_source "$1" "PROFORMAS.txt" "f9497615494ba59c8b76c79c21c5411bbc919aa895c1eff2cc70c88bec0b8020"
verify_source "$2" "SILLAS-PISOS-OTROS.txt" "8e22fc29be4d2ed1d75d9745409df02c24cd953bca25a79dc06c083a77fd7ca0"
verify_source "$3" "inventario de sillas.txt" "43417573bc0ec98b90d63de89bd9b7dab236760724bbe74377a03fd63d4a0089"

DESTINO="$HOME/Descargas"
if [ ! -d "$DESTINO" ]; then
    echo "BLOQUEADO: no existe ~/Descargas/." >&2
    exit 2
fi
RUN="$(mktemp -d "$DESTINO/HOMEX_V2_OFFLINE4_XXXXXXXX")"
echo "EVIDENCIA_PRIVADA=$RUN"

(
    set -euo pipefail
    export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
    date -Is
    git rev-parse HEAD
    uv --version
    uv run --locked --extra dev --extra asr --python 3.11.15 \
        python -m training.canonical_v2.build --output "$RUN/corpus" \
        --sources "$1" "$2" "$3"
    uv run --locked --extra dev --extra asr --python 3.11.15 \
        python -m training.canonical_v2.validate "$RUN/corpus"
    uv run --locked --extra dev --extra asr --python 3.11.15 \
        python -m training.canonical_v2.audit "$RUN/corpus" "$RUN/audit"
    make check docbin-check distribution-check
    uv audit --locked
    uv run --locked --extra dev --extra asr --python 3.11.15 \
        python -m training.canonical_v2.experiment run \
        --bundle "$RUN/corpus" --output "$RUN/models"
    git diff --check
    git status --short
    echo "PRIVATE_REBUILD_AND_TRAINING=PASS"
) > "$RUN/execution.log" 2>&1 && RESULT=PASS || RESULT=FAIL

echo "RESULTADO=$RESULT"
echo "LOG_PRIVADO=$RUN/execution.log"
echo "CORPUS_PRIVADO=$RUN/corpus"
echo "MODELOS_PRIVADOS=$RUN/models"
if [ "$RESULT" != "PASS" ]; then
    echo "BLOQUEADO: consulta el log privado; no se declara entrenamiento aprobado."
    exit 1
fi
echo "Experimentos finalizados offline, sin promoción ni cambios productivos."
