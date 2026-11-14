# F09 frontend targeted integration RED baseline

Frontend candidate: `ef0a7f8` (`<workspace>`)
Backend: `54c8b91` (`<workspace>`)

Command: `HOMEX_INTEGRATION_API_URL=http://127.0.0.1:<scratch-api-port> npm run test:integration -- src/tests/integration/fe08-real.spec.ts src/tests/integration/galerias-real.spec.ts --grep 'recorrido comercial completo|Galería real de mueble'`

Environment: scratch PostgreSQL 16 cluster/database; copied Python 3.11 venv; scratch settings override for media/audio roots, allowed hosts and CORS; combined disposable fixtures seeded by `scripts/preparar_integracion_frontend_f09.py`; no Redis, production or ambient service use. Preview configured at 4174. No source edits or Git mutations.

Result: command exit code 1; 2 targeted tests failed with semantic assertions (Playwright reports 2 failed). FE08 expected `/proformas/{id}` but remained at `/proformas/1/editar`, failing `src/tests/integration/fe08-real.spec.ts:61`. Gallery test timed out locating `/ficha|configurar|técnica/i` at `src/tests/integration/galerias-real.spec.ts:100`. Logs and traces are local-only under `../logs/frontend-f09-v1` and the candidate worktree's ignored `test-results/playwright-integration/`; do not publish traces or private fixture data.

One prior attempt used incorrect API-origin setup and failed at login; that attempt is archived in scratch only, not treated as semantic evidence. All owned API/PostgreSQL/preview processes stopped after the successful baseline run.
