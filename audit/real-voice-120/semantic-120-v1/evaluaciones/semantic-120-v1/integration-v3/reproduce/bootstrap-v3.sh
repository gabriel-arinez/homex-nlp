#!/usr/bin/env bash
set -euo pipefail
umask 077
HERE=$(cd -- "$(dirname -- "$0")" && pwd)
CORPUS=${1:-$HOME/Descargas/HOMEX_Guiones_Evaluacion_Voz}
BACKEND_REPO=${2:-$HOME/HOMEX/homex-backend}
FRONTEND_REPO=${3:-$HOME/HOMEX/homex-frontend}
MODEL=${4:-$HOME/modelos/faster-whisper-small}
BACKEND_VENV=${5:-$BACKEND_REPO/.venv}
PG=${6:-/usr/lib/postgresql/16/bin}
BACKEND_COMMIT=704056430b19d55b8687de788392cb0198ed23e9
FRONTEND_COMMIT=feece0a99689c9a73c601f249ea1af3bf11e1b6e
WHEEL_SHA=c1a085f899a9f2f0797f332304fcf8eeea91f4837d5d06a9a2ca5a6c07815a80
for cmd in git tar cp uv node npm; do command -v "$cmd" >/dev/null; done
test -x "$BACKEND_VENV/bin/python" && test -d "$FRONTEND_REPO/node_modules" && test -d "$MODEL"
test -x "$PG/initdb" && test -x "$PG/pg_ctl"
test "$(git -C "$BACKEND_REPO" rev-parse "$BACKEND_COMMIT^{commit}")" = "$BACKEND_COMMIT"
test "$(git -C "$FRONTEND_REPO" rev-parse "$FRONTEND_COMMIT^{commit}")" = "$FRONTEND_COMMIT"
S=$(mktemp -d "${TMPDIR:-/tmp}/homex-semantic-reproduction.XXXXXX")
export HOMEX_REPRO_SCRATCH="$S" HOMEX_REPRO_CORPUS="$CORPUS" HOMEX_REPRO_MODEL="$MODEL" HOMEX_REPRO_PG="$PG"
unset PYTHONPATH PYTHONHOME
export PYTHONDONTWRITEBYTECODE=1
mkdir "$S/backend" "$S/frontend" "$S/socket" "$S/tmp" "$S/venv"
printf 'Private disposable scratch: %s\n' "$S"
# Archive exact published commits; never modify either source checkout.
git -C "$BACKEND_REPO" archive "$BACKEND_COMMIT" | tar -x -C "$S/backend"
git -C "$FRONTEND_REPO" archive "$FRONTEND_COMMIT" | tar -x -C "$S/frontend"
WHEEL="$S/backend/vendor/homex_nlp-0.1.22-py3-none-any.whl"
printf '%s  %s\n' "$WHEEL_SHA" "$WHEEL" | sha256sum --check --status
# Copy, never symlink, an existing dependency environment. Install only the local wheel.
cp -a "$BACKEND_VENV/." "$S/venv/"
cp -a "$FRONTEND_REPO/node_modules" "$S/frontend/node_modules"
PY="$S/venv/bin/python"
"$PY" -c 'import os,pathlib,sys; assert pathlib.Path(sys.prefix).resolve()==pathlib.Path(os.environ["HOMEX_REPRO_SCRATCH"],"venv").resolve()'
uv pip install --offline --no-deps --reinstall --python "$PY" "$WHEEL" > "$S/wheel-install.log" 2>&1
for name in setup-v3.py snapshot-v3.py worker-v3.py verify-v3.py runner-v3.sh; do cp "$HERE/$name" "$S/$name"; done
cp "$HERE/probe-v3.mjs" "$S/frontend/probe-v3.mjs"
"$PY" "$S/setup-v3.py"
"$PY" "$S/verify-v3.py" before
"$PG/initdb" -D "$S/pgdata-live" -U audit --auth=trust --no-locale --encoding=UTF8 > "$S/initdb.log" 2>&1
# initdb must complete before pg_ctl starts; avoid the bootstrap-server race.
set +e
bash "$S/runner-v3.sh" > "$S/evidence/live-e2e.log" 2>&1
LIVE_RC=$?
"$PY" "$S/verify-v3.py" after > "$S/evidence/postflight.log" 2>&1
POST_RC=$?
set -e
printf 'live_exit=%s postflight_exit=%s evidence=%s\n' "$LIVE_RC" "$POST_RC" "$S/evidence"
# Scratch, private audio copies, credentials and traces remain for local inspection.
test "$LIVE_RC" -eq 0 && test "$POST_RC" -eq 0
