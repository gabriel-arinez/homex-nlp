# Published frontend and real-stack CI closure

The frontend integration failures are resolved without reverting the unified editor,
weakening business assertions or changing ASR/NLP behavior. Both final consumer
workflows pass. This closes the frontend/CI follow-up, **not** the pending human
acoustic/association adjudication of the 120 development recordings.

## Frozen delivery

| Repository | Branch | Final commit | Observed CI |
| --- | --- | --- | --- |
| Frontend | `fix/real-voice-120-f09` | `7b83694310239551e45d8a8a30ab96e2724c72c1` | [43160479820](https://github.com/gabriel-arinez/homex-frontend/actions/runs/43160479820): 13/13 jobs passed |
| Backend | `feat/real-voice-120-semantic` | `850c250d0e673a296f4f0d772800aae89dd395b1` | [43160776481](https://github.com/gabriel-arinez/homex-backend/actions/runs/43160776481): 13/13 jobs passed |

Frontend CI consumes backend `54c8b91`; backend `54c8b91` → `850c250` changes only
its workflow peer pin and documentation, not runtime code or the wheel. Backend
CI consumes exact frontend `7b83694`, never an unmerged assumption about `main`.
The installed package remains `homex-nlp==0.1.22`, wheel SHA-256
`c1a085f899a9f2f0797f332304fcf8eeea91f4837d5d06a9a2ca5a6c07815a80`.
No merge, production deployment or public package release occurred.

## Changes and proof

- Deliberate editor unification in `18ffcea` had left integration selectors on the
  removed detail route/menu. Tests now use exact editor actions and retain all
  approval, cancellation, receipt, delivery-note, stock and gallery checks.
- Persisted order confirmation is identified through its order link, not an
  arbitrary first match between a persistent banner and a transient toast.
- A newly unblocked audio test also assumed the removed detail view after reload.
  It now checks the restored product line and the visible persisted `BORRADOR`
  code/label on the Review step. ASR and stored commercial values were not repaired
  or fabricated to satisfy this test.
- Voice instructions at opacity 0.9 failed Axe contrast (4.38:1). Full opacity
  restores readability without changing institutional red or disabling Axe.
- Both real-stack CI suites pass **14/14** cases, including worker/ASR, catalogue
  categories, manual-save authority and galleries. Backend postchecks confirm
  PostgreSQL evidence, capture linkage/snapshot, audio deletion and public media.
- Local frontend quality checks: **306/306** unit/component tests, typecheck,
  lint and formatting. Independent frozen E2E: **109 passed, 1 pre-existing skip**.
  Final backend CI: **552 passed, 5 skips** (missing Poppler geometry/token proof).
  A separate concurrency suite passes 16 tests; its counts are not added as unique
  tests. No skip was introduced by these changes.

## Evidence and limits

- [Final delivery/root causes](evaluaciones/delivery-report.json)
- [Frontend final CI](evaluaciones/frontend-final-ci.json),
  [backend final CI](evaluaciones/backend-final-ci.json)
- [Independent frontend check](evaluaciones/independent-verification.json),
  [final peer check](evaluaciones/backend-final-peer-independent.json),
  [historical CI-status wording clarification](evaluaciones/independent-ci-status-clarification.json)
- [Selected complete console logs, with path-prefix redaction only](logs/)
- [Source/export hashes, omissions and canonical full CI console](PUBLICATION-MANIFEST.json)

Initial setup-origin/interpreter failures and intermediate semantic failures are
preserved, not counted as successful proof. Earlier independent reports describe
frozen intermediate checks; the final CI JSON/logs establish later-head success.
Raw CI consoles remain in the corpus `logs/frontend-f09-v1/` and the canonical
Actions links above. Private traces, disposable credentials/databases and all
recordings remain local. This intervention changes no 120-case ASR/NLP metrics,
commercial classification, acoustic gold status or generalization claim.

## Reproduce

Check out the exact commits above. Use Node 24 and the locked dependencies.
For isolated local fixtures and the exact focused commands, see the frozen
[frontend integration instructions](https://github.com/gabriel-arinez/homex-frontend/blob/7b83694310239551e45d8a8a30ab96e2724c72c1/docs/GALERIAS.md).
Never run fixture seeders against an existing commercial database.

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run check:all
VITE_API_BASE_URL=http://localhost:8000 npm run test:e2e
npm run contract:check
# Requires an isolated, migrated and seeded backend, plus CORS for port4174:
HOMEX_INTEGRATION_API_URL=http://127.0.0.1:8000 npm run test:integration -- \
  src/tests/integration/fe08-real.spec.ts src/tests/integration/galerias-real.spec.ts \
  --grep 'recorrido comercial completo|Galería real de mueble'
```

The full real-ASR setup, synthetic audio generation, worker/outbox startup,
Playwright command and backend authority postchecks are reproduced exactly by
these immutable workflow definitions, whose complete execution passed:
[frontend](https://github.com/gabriel-arinez/homex-frontend/blob/7b83694310239551e45d8a8a30ab96e2724c72c1/.github/workflows/ci.yml),
[backend](https://github.com/gabriel-arinez/homex-backend/blob/850c250d0e673a296f4f0d772800aae89dd395b1/.github/workflows/ci.yml).
The focused local commands alone do not substitute for those full-stack gates.

Risk: item5 — exact CI consumer references, independently checked and exercised by
both final real-stack workflows.
