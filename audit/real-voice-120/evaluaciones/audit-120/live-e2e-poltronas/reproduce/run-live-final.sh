#!/bin/bash
set -eu
S=/tmp/homex-audit-integration.WFXbW2
PY=/home/gabriel/HOMEX/homex-backend/.venv/bin/python
PG=/usr/lib/postgresql/16/bin
read -r PGPORT APIPORT FRONTPORT < <("$PY" -c "import json; c=json.load(open('$S/live-final-config.json')); print(c['pgport'],c['apiport'],c['frontport'])")
export PYTHONPATH="/home/gabriel/HOMEX/homex-nlp/src:$S/backend"
export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$S/tmp"
export DATABASE_URL="postgresql://audit@127.0.0.1:$PGPORT/homex_final_live"
export DJANGO_SECRET_KEY=audit-live-synthetic-only DJANGO_SETTINGS_MODULE=audit_live_settings
export HOMEX_ASR_MODEL_PATH=/home/gabriel/modelos/faster-whisper-small HOMEX_ASR_DEVICE=cpu HOMEX_ASR_COMPUTE_TYPE=int8
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PIDS=""
cleanup() {
 for pid in $PIDS; do kill "$pid" 2>/dev/null || true; done
 for pid in $PIDS; do wait "$pid" 2>/dev/null || true; done
 "$PG/pg_ctl" -D "$S/pgdata-live" -m fast -w stop
}
trap cleanup EXIT
"$PG/pg_ctl" -D "$S/pgdata-live" -l "$S/postgres-live.log" -o "-h 127.0.0.1 -p $PGPORT -k $S/socket" -w start
"$PG/createdb" -h 127.0.0.1 -p "$PGPORT" -U audit homex_final_live
cd "$S/backend"
"$PY" manage.py migrate --noinput
"$PY" - <<'PY'
import django,json
django.setup()
from django.contrib.auth import get_user_model
c=json.load(open('/tmp/homex-audit-integration.WFXbW2/live-final-config.json'))
get_user_model().objects.create_superuser(username=c['username'],password=c['password'])
import homex_nlp
print('candidate_import='+homex_nlp.__file__)
PY
"$PY" manage.py runserver "127.0.0.1:$APIPORT" --noreload > "$S/live-api-final.log" 2>&1 &
PIDS="$PIDS $!"
"$PY" -u "$S/live-worker.py" > "$S/live-worker-final.log" 2>&1 &
PIDS="$PIDS $!"
cd "$S/frontend"
VITE_API_BASE_URL="http://127.0.0.1:$APIPORT" npm run build-only
./node_modules/.bin/vite preview --host 127.0.0.1 --port "$FRONTPORT" --strictPort > "$S/live-preview-final.log" 2>&1 &
PIDS="$PIDS $!"
node "$S/frontend/live-probe-final.mjs"
