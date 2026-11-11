#!/bin/bash
set -eu
SOURCE=$(cd "$(dirname "$0")" && pwd)
S=$(mktemp -d /tmp/homex-audit-reproduce.XXXXXX)
PY=/home/gabriel/HOMEX/homex-backend/.venv/bin/python
PG=/usr/lib/postgresql/16/bin
mkdir -p "$S/backend" "$S/frontend" "$S/socket" "$S/tmp"
git -C /home/gabriel/HOMEX/homex-backend archive ee6c80f13ff76e23c4c572c81042a0b9760db033 | tar -x -C "$S/backend"
git -C /home/gabriel/HOMEX/homex-frontend archive ecb7f23b4d7f25317ae1501733cc8c915bed63c1 | tar -x -C "$S/frontend"
cp -a /home/gabriel/HOMEX/homex-frontend/node_modules "$S/frontend/node_modules"
for file in live_setup_final.py run-backend-final.sh run-live-final.sh live-worker.py; do
 sed "s|/tmp/homex-audit-integration.WFXbW2|$S|g" "$SOURCE/$file" > "$S/$file"
done
cp "$SOURCE/live-probe-final.mjs" "$S/frontend/live-probe-final.mjs"
RUN_OUT="/home/gabriel/Descargas/HOMEX_Guiones_Evaluacion_Voz/evaluaciones/audit-120/live-e2e-poltronas"
mkdir -p "$RUN_OUT"
"$PY" - "$S/live_setup_final.py" "$RUN_OUT" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1]); t=p.read_text()
t=t.replace("out=corpus/'evaluaciones/audit-120/live-e2e-poltronas';", "out=pathlib.Path("+repr(sys.argv[2])+");")
p.write_text(t)
PY
"$PY" "$S/live_setup_final.py"
"$PG/initdb" -D "$S/pgdata-utf8" -U audit --auth=trust --no-locale --encoding=UTF8
"$PG/initdb" -D "$S/pgdata-live" -U audit --auth=trust --no-locale --encoding=UTF8
echo "$S" > "$RUN_OUT/scratch-path.txt"
echo "Disposable reproduction scratch: $S"
set +e
bash "$S/run-backend-final.sh" "$S" > "/home/gabriel/Descargas/HOMEX_Guiones_Evaluacion_Voz/logs/audit-120-poltronas-backend.log" 2>&1
BACKEND_RC=$?
bash "$S/run-live-final.sh" > "/home/gabriel/Descargas/HOMEX_Guiones_Evaluacion_Voz/logs/audit-120-poltronas-live-e2e.log" 2>&1
LIVE_RC=$?
echo "backend_exit=$BACKEND_RC live_e2e_exit=$LIVE_RC evidence=$RUN_OUT"
test "$BACKEND_RC" -eq 0 && test "$LIVE_RC" -eq 0
