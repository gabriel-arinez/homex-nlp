#!/bin/bash
set -eu
SCRATCH=$1
export TMPDIR="$SCRATCH/tmp"
PG=/usr/lib/postgresql/16/bin
PORT=$(/home/gabriel/HOMEX/homex-backend/.venv/bin/python -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')
trap '"$PG/pg_ctl" -D "$SCRATCH/pgdata-utf8" -m fast -w stop' EXIT
"$PG/pg_ctl" -D "$SCRATCH/pgdata-utf8" -l "$SCRATCH/postgres.log" -o "-h 127.0.0.1 -p $PORT -k $SCRATCH/socket" -w start
"$PG/createdb" -h 127.0.0.1 -p "$PORT" -U audit homex_final_audit
export DATABASE_URL="postgresql://audit@127.0.0.1:$PORT/homex_final_audit"
export DJANGO_SECRET_KEY=audit-only-not-production
export DJANGO_SETTINGS_MODULE=config.settings.test
export PYTHONPATH="/home/gabriel/HOMEX/homex-nlp/src:$SCRATCH/backend"
export PYTHONDONTWRITEBYTECODE=1
cd "$SCRATCH/backend"
/home/gabriel/HOMEX/homex-backend/.venv/bin/python -c 'import homex_nlp; print("candidate_import="+homex_nlp.__file__)'
set +e
/home/gabriel/HOMEX/homex-backend/.venv/bin/python -m pytest -q -p no:cacheprovider --basetemp="$SCRATCH/pytest-temp-final" tests/api/test_catalogo_captura.py tests/integration/test_f082_worker_audio.py tests/integration/test_nlp_final.py tests/unit/test_f080_contrato_nlp.py tests/unit/test_prf04_nlp_v*_adapter.py
rc=$?
echo "BACKEND_EXIT_CODE=$rc"
exit "$rc"
