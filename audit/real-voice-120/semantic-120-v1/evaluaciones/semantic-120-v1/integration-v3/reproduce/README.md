# Reproduce the final eight-case audio-to-form verification

Run this bootstrap from an ordinary local user account (not PostgreSQL root). It creates a **new private scratch directory and new evidence**, never overwriting the observed integration-v3 results.

```bash
bash bootstrap-v3.sh
```

Optional positional paths, in order:

```bash
bash bootstrap-v3.sh "$HOME/Descargas/HOMEX_Guiones_Evaluacion_Voz" \
  "$HOME/HOMEX/homex-backend" "$HOME/HOMEX/homex-frontend" \
  "$HOME/modelos/faster-whisper-small" "$HOME/HOMEX/homex-backend/.venv" \
  /usr/lib/postgresql/16/bin
```

## Prerequisites and pinned inputs

- Local Git repositories containing backend `704056430b19d55b8687de788392cb0198ed23e9` and frontend `feece0a99689c9a73c601f249ea1af3bf11e1b6e`. Neither checkout is changed; exact commits are archived.
- Backend commit vendors homex-nlp `0.1.22`, SHA256 `c1a085f899a9f2f0797f332304fcf8eeea91f4837d5d06a9a2ca5a6c07815a80`.
- Existing Python3.11 backend environment with backend/worker dependencies, installed frontend node_modules, Node/npm, uv, PostgreSQL16 binaries, installed Playwright Chromium and the offline faster-whisper-small model. No dependency download is performed.
- Original corpus manifest and `evaluaciones/audit-120/audio-ledger.json`, all240 original AAC/WAV files.

The Python environment is copied, **never symlinked**. Only the local pinned wheel is reinstalled offline without dependencies into that copy. The bootstrap verifies its import path, version and every packaged Python module. No NLP source directory is added to PYTHONPATH; only isolated backend/settings directories are used. Existing model/dependency artifacts are read-only inputs, not ambient sessions or credentials.

## What runs

1. Exclusive system scratch, fresh credentials and Django secret, private UTF8 PostgreSQL, loopback-only API/worker/frontend preview.
2. Real WAV copies for MP-0001, SIL-0001, PIS-0001, MP-0005, MP-0036, MP-0045, MP-0067 and PIS-0006. Each scenario uses a fresh page and fresh synthetic login, isolating both authentication and unsaved draft sessionStorage.
3. Actual Whisper and backend proposal processing, then semantic control assertions for allfour forms, mapped furniture dimensions/units, quantities/prices, catalog names/models/thicknesses and retained evidence. Ambiguous component geometry is not forced into general dimensions.
4. No commercial browser writes; exact before/after snapshots of authoritative models, including an existing synthetic product with approved-price sentinel999 and stock0. Password hashes and login timestamps are intentionally excluded. Permissions, stored prices, stock and authoritative states must remain unchanged.
5. All240 original audio hashes and installed-wheel byte identity are checked before and after. API, worker, preview and PostgreSQL processes owned by the runner stop through traps; scratch remains for inspection.

The command prints the fresh evidence path and exits nonzero for browser, snapshot or postflight failures. Logs, raw JSON, screenshots and trace are private. **Never publish trace.zip, audio copies, config credentials or request authorization headers.** Latencies under concurrent workloads are diagnostic, not a benchmark. Eight cases are not120-case browser coverage or independent acoustic validation.

## Provenance and validation status

Observed final integration-v3 passed8/8 scenarios. Its original `live-probe-executed.mjs`, `live_setup_final.py`, `run-live-final.sh`, `snapshot.py` and `live-worker.py` remain here as historical observations; the historical runner contains private runtime paths/secret and is **not a runnable entry point or public artifact**. Use only `bootstrap-v3.sh` and its `*-v3` helpers for fresh runs.

The portable bootstrap preserves the observed scenario assertions and seed/settings behavior, but obtains paths and secrets at runtime. It was **structurally checked, not rerun end-to-end** after portability changes. Check syntax without starting any service:

```bash
bash -n bootstrap-v3.sh runner-v3.sh
python3 - <<'PY'
from pathlib import Path
for name in ('setup-v3.py', 'snapshot-v3.py', 'worker-v3.py', 'verify-v3.py'):
    compile(Path(name).read_text(), name, 'exec')
PY
node --check probe-v3.mjs
```
