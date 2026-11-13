# Focused engine review: evidence, corrections and remaining human uncertainty

All ten actual Sourcery observations were reproduced and classified before runtime edits: **seven confirmed, two partially confirmed, one false positive**. Confirmed parser defects are corrected and locally verified. **This report does not claim improved commercial precision:** frozen original-ASR scalar coverage decreases **549 → 520/1000**, while conservative abstentions increase **7 → 13**. The six affected cases remain included and await human contextual review.

Final head-bound live integration and CI are published in the original [NLP #43](https://github.com/gabriel-arinez/homex-nlp/pull/43), [backend #60](https://github.com/gabriel-arinez/homex-backend/pull/60) and [frontend #68](https://github.com/gabriel-arinez/homex-frontend/pull/68) summaries/checks. Auxiliary #44/#45 are review slices and must never merge. No main merge or deployment is authorized by this report.

## Ten-observation disposition

Exact comment IDs/links and detailed outcomes: [`ten-observations.json`](ten-observations.json).

| # | Classification | Demonstrated outcome |
|---|---|---|
| 1 | Confirmed | Bound repeated trailing-negation scans to local context; explicitly reject over20,000-character requests. JSON/multipart rejection occurs before capture/attempt/outbox persistence, without truncation. |
| 2 | Confirmed | A bare comma and similar description no longer justify silently merging independent/ambiguous mentions. Explicit references remain supported. |
| 3 | Confirmed | Composed casillero is retained as a component with source evidence, not an extra commercial line. |
| 4 | Confirmed | Determiner-bearing drawer composition is distinguished from independent coordinated products; component counts do not become the main quantity. |
| 5 | Confirmed | Restore independently valued adjacent axes, preserve adjective guards, and prevent postfix axes from consuming the next measure. |
| 6 | Partial | Supplied monetary examples already abstained correctly. The separate explicit `USB, 2 unidades` omission is corrected; prices/protocol numbers are not counts. |
| 7 | Confirmed | Complete strict cardinal corrections replace superseded quantities and retire stale accepted evidence; different-product corrections abstain. |
| 8 | False positive | Canonical source/manifest/ordinary installed0.1.23 wheel agreed before edits. Auxiliary partial-PR omissions and stale editable metadata were not a published-version defect. New0.1.24 is justified by actual code changes. |
| 9 | Partial | Complete letter-O codes decode under strict grammar; alternatives/incomplete spelling remain unresolved rather than fused or silently selected. |
| 10 | Confirmed | Ordinary leading `a`/`de` model prose is distinguished from a real incomplete-code warning; original prose is preserved. |

Initial read-only evidence contains all ten original comments,41 public API replays, source hashes and three-repeat bounded timings. The initial wrong-category OTRO model probes were corrected using the supported SILLA/PISO paths before implementation; no false-positive classification rests on unsupported fields.

## Frozen120-case comparison

All **14 cells ×120 cases =1680 outputs** completed without execution errors. Inputs are the original frozen ASR, five previously frozen configurations and script controls; no ASR was rerun or promoted. Categories remain73/27/7/13, including sillones/poltronas in OTRO. Historical results and all original recordings remain unchanged.

| Category | Cases | Before supported scalar matches | After |
|---|---:|---:|---:|
| Made-to-order furniture |73|430/767|401/767|
| Chairs |27|78/185|78/185|
| Floating floors |7|21/28|21/28|
| Other |13|20/20|20/20|
| Total |120|549/1000|520/1000|

The complete script denominator is1087:1000 supported tuples plus87 unmatched unsupported-category tuples. No case was removed. These metrics count scalar/literal presence, **not acoustic correctness, component ownership or integral commercial precision**. Script controls remain549/1000 and7 abstentions.

All29 original scalar-match losses come from new abstentions in **MP-0022,MP-0023,MP-0026,MP-0050,MP-0051,MP-0055**. Their ASR uses bare-comma desk/drawer restatements without definite/coreferential cues; script sentence-boundary controls retain proposals. The new behavior follows the requested conservative ambiguity policy. It is **not automatically a safety improvement or a human-confirmed interpretation**. Before-value presence did not establish correct component ownership. These six cases form an explicit human-review queue, not excluded failures.

Artifacts:

- [`case-index.json`](case-index.json), [`case-index.csv`](case-index.csv): all120 IDs/categories, original hashes, output hashes and before/after counts.
- [`supported-fields.json`](supported-fields.json): per-field denominators and match/absence/mismatch outcomes.
- [`comparison-summary.json`](comparison-summary.json): all categories/fields/configurations.
- [`regression-disposition.json`](regression-disposition.json): losses, abstentions and corrected extras.
- Full private raw outputs, references, field associations and traces: local corpus `evaluaciones/sourcery-review-v1/comparison-v2/`.

## Regressions found during this intervention

An initial1051-test pass did not establish absence of commercial regressions. The full frozen comparison exposed two introduced dimension false positives. Complete-set public probes reproduced them; a bounded postfix/prefix ownership correction passed77 focused and1053 full independent tests. Final comparison removes those false values and an additional pre-existing same-class width leak: **three case-pairs, four incorrect values removed, zero new predictions versus the intermediate candidate**. Correct dimensions remain; headline scalar scores alone hid these changes.

Intermediate comparison-v1 and unpublished package candidates remain preserved privately. The initially failed expectation of exactly two changed pairs was retained and corrected only after investigating the third pre-existing leak. No result was silently overwritten or relabeled as a pass.

## Distribution and local verification

Final package **0.1.24** preserves the result shape and deliberately documents the20,000-character request boundary. The longest original/script text checked was645 characters. This is an explicit contract limit, not a claim to accept arbitrary-length dictations.

| Artifact | SHA-256 |
|---|---|
| Wheel | `12d1dab78a5e1ea04780e0e3345e1885cc5dc9edf5c7b2aa1b989f8349379ec6` |
| Source archive | `ff74aa3492439ce9a10556c93fc3f099ac78c1e6b4e91cd73196c475cf5bb053` |

Two epoch-zero builds are byte-identical. Ordinary isolated installation under `python -I` matches all26 Python modules and all31 packaged files against wheel/source; no NLP source-path substitution counts as consumer proof. Earlier0.1.23 and preceding artifacts are unchanged. Unpublished0.1.24 candidates are separately preserved; only the designated final build is consumed.

Observed local checks:

- NLP: **1056 passed**, scoped Ruff passed. Independent semantic core:1053 passed;77 focused probes. Benchmark CLI help/rejection/default JSON:3 passed.
- Backend: **576 passed**, offline lock and scoped lint/format passed. Installed wheel and public text boundaries verified independently.
- Frontend: **309 passed**, types/lint/format/build/generated-contract checks passed. Application/styles/tests remain byte-identical to frontend `ffa2495`; only four required contract/peer/documentation files changed. Its manual missing-quantity HITL test correction is preserved.
- OpenAPI: no errors; one existing CategoryEnum naming warning. Repository-wide Ruff still reports338 pre-existing historical audit/docs errors; those immutable archived scripts were not modified to hide them.

Final live E2E/a11y/Whisper/Celery/PostgreSQL and current CI results are head-bound in the original PR summaries and local final-delivery ledger, not inferred from these local counts or earlier green revisions. PostgreSQL16 local versus17 CI is recorded explicitly.

## Final consumer correction and cross-stack proof

Final live integration exposed a pre-existing backend loss: accessories carrying
an explicit `component_ref` were removed from the global list but never routed
to their component. Backend `55cc7486605abcb362ccfa33a96189d81db4d374`
preserves them in the existing component `atributos` array, one ordered
`Accesorios` value. It neither guesses scope nor fills an absent quantity.
The global route remains unchanged; dangling references remain rejected.
No schema, frontend application or NLP wheel change was needed.

Seven public-API regressions reproduced three failures before the fix and all
seven pass afterward. Independent isolated verification passed **576 tests**;
parent source hashes and Ruff agree. Exact published backend/frontend live checks
passed **576 backend, 15 real integration and 109 E2E/a11y** with **one existing
attachment skip**. Component accessories survive public text, explicit simulated
human confirmation, persisted BORRADOR and actual browser editor readback without
manual insertion. Prior authority rows and all240 original AAC/WAV hashes are
unchanged. This controlled synthetic exercise is not human acoustic adjudication.

Both post-fix exact-peer CI dispatches passed13/13 jobs:
[backend43519395154](https://github.com/gabriel-arinez/homex-backend/actions/runs/43519395154)
and [frontend43519400634](https://github.com/gabriel-arinez/homex-frontend/actions/runs/43519400634).
Backend push/PR and frontend current-head PR runs also passed13/13 each.
The final passive NLP report commit is checked separately in PR43; its final
31-file installed-wheel identity readback and complete final SHA triple are in
the original PR summaries and local `final-delivery.json`. This avoids embedding
a self-referential CI claim into the commit it would need to certify.

Private full evidence: `final-head-live-v2/`, `final-ci-v2/` and
`component-accessory-verifier-v1/` under the local evaluation/log roots.
Initial stale scratch-source verifier failures and an incorrect UI action-menu
selector remain preserved; corrected candidate-origin and UI checks passed.
No test was disabled, no arbitrary wait added and no historical result deleted.

## Reproduce

From the NLP repository with Python3.11 and its frozen lock:

```bash
uv sync --locked --extra dev
uv run --frozen pytest -q
uv run --frozen ruff check src tests tools
uv run --frozen python tools/benchmark_accessory_context.py --help
uv run --frozen python tools/benchmark_accessory_context.py
CORPUS="$HOME/Descargas/HOMEX_Guiones_Evaluacion_Voz"
uv run --frozen python tools/evaluate_semantic_voice.py \
  --base-ref 62127a92d0b310127feb803e807f28adecee16f8 \
  --references "$CORPUS/evaluaciones/semantic-120-v1/references-v2" \
  --original-asr audit/real-voice-120/evaluaciones/audit-120/baseline-routing-v2/cases \
  --candidate-asr "$CORPUS/evaluaciones/semantic-120-v1/asr-experiments" \
  --values "$CORPUS/evaluaciones/audit-120/catalog-fixture.json" \
  --output "$CORPUS/evaluaciones/sourcery-reproduction-$(date +%s)"
```

The controlled benchmark has three repetitions at1k/5k/10k/20k characters. The measured focal-stage median speedups were1.23×/1.58×/2.22×/2.81×; these are machine-local diagnostics, not a wall-clock CI threshold or end-to-end latency claim. Its structural regression bounds local lookback. Source-baseline benchmarking using `PYTHONPATH` is diagnostic only, never an installed-consumer proof.

For backend use the exact vendored wheel via `uv sync --locked --extra dev --extra worker`, fresh disposable PostgreSQL/Redis and the existing integration preparation scripts. Run `uv run pytest -q`, `uv run python manage.py makemigrations --check --dry-run`, and `uv run python manage.py spectacular --validate --file <new-scratch-file>`; compare to `docs/openapi.yaml`. Never use production settings/data.

For frontend use `npm ci`, `VITE_API_BASE_URL=http://localhost:8000 npm run check:all`, `npm run contract:check`, and the workflow's real-stack fixtures with `HOMEX_INTEGRATION_API_URL` set to the owned API origin. E2E and accessibility commands/configuration are versioned in `.github/workflows/ci.yml`. Final remote integrations explicitly select the other repository's final HEAD via `integration_peer_ref` and record both SHAs.

## Evidence locations and review boundary

All complete consoles: local corpus `logs/sourcery-review-v1/`. Full references/results/decisions: `evaluaciones/sourcery-review-v1/`. New directories preserve diagnosis, failed RED runs, intermediate dimension regressions, corrected comparison-v2, candidate archives, installed distribution proofs and final head-bound integration separately.

Human acoustic and component-association gold remains **zero**. No integral commercial precision or independent generalization is asserted; all120 recordings are development data. Privacy cleanup/repository visibility decisions remain deferred. No original audio, new private commercial transcript/proforma, credential, `.atl`, production data, historical deletion or Git history rewrite is part of this publication.

Risk: items2/3/5 (bounded untrusted input, shared semantic/request contracts and release/CI integration). No permission, stock or authoritative commercial-state guard is relaxed.
