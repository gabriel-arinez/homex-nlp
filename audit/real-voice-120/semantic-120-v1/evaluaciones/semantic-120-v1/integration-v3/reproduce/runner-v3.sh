#!/bin/bash
set -euo pipefail
S=${HOMEX_REPRO_SCRATCH:?}
PY="$S/venv/bin/python"
PG=${HOMEX_REPRO_PG:?}
export HOMEX_REPRO_CONFIG="$S/live-final-config.json"
read -r PGPORT APIPORT FRONTPORT < <("$PY" -c "import json; c=json.load(open('$S/live-final-config.json')); print(c['pgport'],c['apiport'],c['frontport'])")
export PYTHONPATH="$S:$S/backend"
export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$S/tmp"
export DATABASE_URL="postgresql://audit@127.0.0.1:$PGPORT/homex_final_live"
export DJANGO_SECRET_KEY=$("$PY" -c 'import json,os;print(json.load(open(os.environ["HOMEX_REPRO_CONFIG"]))["django_secret"])')
export DJANGO_SETTINGS_MODULE=audit_live_settings
export HOMEX_ASR_MODEL_PATH="$HOMEX_REPRO_MODEL" HOMEX_ASR_DEVICE=cpu HOMEX_ASR_COMPUTE_TYPE=int8
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PIDS=""
cleanup() {
 for pid in $PIDS; do kill "$pid" 2>/dev/null || true; done
 for pid in $PIDS; do wait "$pid" 2>/dev/null || true; done
 "$PG/pg_ctl" -D "$S/pgdata-live" -m fast -w stop
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
"$PG/pg_ctl" -D "$S/pgdata-live" -l "$S/postgres-live.log" -o "-h 127.0.0.1 -p $PGPORT -k $S/socket" -w start
"$PG/createdb" -h 127.0.0.1 -p "$PGPORT" -U audit homex_final_live
cd "$S/backend"
"$PY" manage.py migrate --noinput
"$PY" - <<'PY'
import django,json
django.setup()
from django.contrib.auth import get_user_model
import os
c=json.load(open(os.environ['HOMEX_REPRO_CONFIG']))
get_user_model().objects.create_superuser(username=c['username'],password=c['password'])
import homex_nlp
print('candidate_import='+homex_nlp.__file__)
PY
"$PY" manage.py runserver "127.0.0.1:$APIPORT" --noreload > "$S/live-api-final.log" 2>&1 &
PIDS="$PIDS $!"
"$PY" -u "$S/worker-v3.py" > "$S/live-worker-final.log" 2>&1 &
PIDS="$PIDS $!"
cd "$S/frontend"
VITE_API_BASE_URL="http://127.0.0.1:$APIPORT" npm run build-only
./node_modules/.bin/vite preview --host 127.0.0.1 --port "$FRONTPORT" --strictPort > "$S/live-preview-final.log" 2>&1 &
PIDS="$PIDS $!"
"$PY" "$S/snapshot-v3.py" authority-before.json
set +e
node "$S/frontend/probe-v3.mjs"
LIVE_RC=$?
set -e
"$PY" "$S/snapshot-v3.py" authority-after.json
"$PY" - "$S" <<'VERIFY'
import json,pathlib,sys
s=pathlib.Path(sys.argv[1]);c=json.load(open(s/'live-final-config.json'));out=pathlib.Path(c['out'])
before=json.loads((out/'authority-before.json').read_text()); after=json.loads((out/'authority-after.json').read_text())
assert before==after, 'Authoritative database records changed'
(out/'authority-verification.json').write_text(json.dumps({'unchanged':True,'models':list(before),'excluded_fields':['password','last_login'],'seeded_product':before['catalogo.Producto']},indent=2))
VERIFY
exit "$LIVE_RC"
