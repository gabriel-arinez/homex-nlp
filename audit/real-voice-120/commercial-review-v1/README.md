# Commercial review: verified development improvements, human review pending

The candidate NLP 0.1.23 recovers ten of the original seventeen missing proposals and improves script-relative supported scalar matches from **487/1000 to 549/1000** on the unchanged original ASR. This is **not commercial precision**: no human acoustic or component-association gold has been approved. Installed consumers and targeted live forms pass; functional-head CI is green (4 NLP, 13 backend, 13 frontend jobs). Technical intervention is complete; integral commercial validation remains pending. Do not merge without human review.

## Evidence map

| Evidence | Location |
|---|---|
| All 120 immutable IDs, audio hashes, raw-output hashes and before/after counts | `case-index.json`, `case-index.csv` |
| All fourteen evaluation cells, categories and fields | `comparison-summary.json` |
| Frozen ASR per-case/category WER and edit counts, six configurations | `frozen-asr-metrics.json` |
| Seventeen case diagnoses and original/script status | `seventeen-case-diagnosis.json` |
| Metric limits, quantity correction and component ownership change | `interpretation.json` |
| Exact reproducible wheel/sdist identities | `release-artifact-hashes.json` |
| Historical 8,293-file inventory summary | `publication-baseline-summary.json` |
| Explicit incomplete closure status | `status.json` |
| Full private texts, fields, provenance and audio review UI | Local corpus `evaluaciones/commercial-review-v1/review-v2/review.html` |
| Full private before/after outputs | Local corpus `evaluaciones/commercial-review-v1/comparison-final-v2/` |
| Full console logs | Local corpus `logs/commercial-review-v1/` |

Published files intentionally omit audio, full commercial dictations, reviewer identities, private paths, screenshots and raw browser traces. Existing historical evidence is preserved, not recertified or deleted.

## Live consumer defects found and corrected

Generic integration initially passed14/14 while targeted original-transcript readback exposed two real defects: component dimensions were flattened into legacy fields, and explicit unit prices were blank in review. Backend now exposes a read-only projection from the same persisted NLP evidence; frontend preserves component data and explicit prices. No historical ItemIA migration, NLP replay, permission change or weakened HITL contradiction guard was used.

The corrected live run passes15/15, including persisted synthetic text→review→HITL proof. Original MP-0007 and MP-0048 now retain the expected explicit prices without manual filling or confirmation. Component measurements remain local; unknown units stay pending. All six authority comparisons pass. See `semantic-integration.json` and `consumer-verification.json`; full private before/after payloads, screenshots and logs are preserved locally.

Backend full suite: **563 passed**; frontend **309 unit tests**, lint/type/build/generated contracts pass; mock E2E **109 passed, 1 existing attachment skip**. All PDF cases ran. Local PostgreSQL16 differs from CI17. These results are not human acoustic or commercial-gold approval.

## Before/after on original ASR

The denominator counts supported scalar/literal script assertions, deduplicated by field/value/unit. It does not score complete names, component ownership or acoustically confirmed truth. Unsupported script assertions (87 of 1087) are excluded only from this supported indicator, not removed from the underlying cases.

| Category | Cases | NLP 0.1.22 | NLP 0.1.23 |
|---|---:|---:|---:|
| Made-to-order furniture | 73 | 368/767 | 430/767 |
| Chairs | 27 | 78/185 | 78/185 |
| Floating floors | 7 | 21/28 | 21/28 |
| Other, including armchairs/poltronas | 13 | 20/20 | 20/20 |
| Total | 120 | 487/1000 | 549/1000 |

Original-ASR no-proposal cases: **17 → 7**. Script control: matches **501 → 549/1000**, no proposals **13 → 7**. All fourteen cells contain 120 outputs, without execution errors. Across 840 paired comparisons, no previously matched tuple or existing proposal was lost. One superficial quantity prediction disappeared because `Sesenta y un` was corrected from 1 to 61; this is not loss of a correct field.

Unchanged original ASR script-relative WER is **1495/6627**; strict-normalized WER is **922/6371**. Original category WER counts are furniture1042/4174, chairs227/1403, floors93/347 and Other133/703; normalization counts are respectively593/3991,174/1374,70/334 and85/672. Neither is human-verified acoustic accuracy. These ASR outputs are frozen: no recognition gain is attributed to NLP changes or metric normalization. Five historical candidate ASR configurations were compared without promoting a production model/configuration.

## Field-level supported script matches

| Field | Before | After |
|---|---:|---:|
| Accessories | 59/211 | 64/211 |
| Brand | 0/1 | 0/1 |
| Colors | 16/116 | 16/116 |
| Commercial unit | 41/41 | 41/41 |
| Dimensions | 101/139 | 115/139 |
| Materials | 75/213 | 90/213 |
| Price | 72/119 | 81/119 |
| Quantity | 51/68 | 60/68 |
| Thickness | 72/92 | 82/92 |

Additional extracted values remain unverified, not confirmed false positives or correct recoveries. Confirmed commercial precision and acoustic/association denominators remain unavailable (zero adjudicated gold). API-reported integer NLP latency from one serial pass is not an end-to-end benchmark.

## Seventeen original abstentions

Recovered: MP-0008, MP-0022, MP-0026, MP-0037, MP-0051, MP-0060, MP-0065, MP-0070, MP-0071, MP-0074. General rules handle literal compound names, explicit integrated sideboards/drawers and repeated component references, not audio IDs.

| Retained case | Evidence-based disposition |
|---|---|
| MP-0003, MP-0061, MP-0066 | Differing members of table sets; single-proposal contract cannot safely flatten independent products. |
| MP-0012 | ASR literal `trill` differs from script `atril`; no guessed acoustic repair. |
| MP-0017 | Quantity-bearing repeated ASR sentences; intended order count needs listening. |
| MP-0057 | Compartment count versus commercial locker units remains ambiguous. |
| MP-0072 | Lateral position alone does not establish an integrated component. |

All seven retain human acoustic review pending. Detailed original/script/candidate executions and source evidence are in the private `relations-adjudication-v1/` and final comparison, accessible through the review UI.

## Demonstrated corrections and regression proof

- Compound product/referential component recognition: 32 new synthetic probes.
- Complete explicit Spanish cardinal quantities, fused explicit `Preciunitario` and independently stated height: 37 new probes. Generic/ambiguous money and missing units remain unresolved.
- Literal integrated `credencia` component ownership: six probes. MP-0007 component 150 cm width, 65 cm height and depth 45 with **no unit** no longer populate the main desktop. Malformed main width remains unresolved. This improvement changes associations without changing scalar totals.
- Human review exports preserve explicit self-reported listening attestation; canonical JSON identity prevents false import conflicts. Playback does not approve a datum.
- Distribution privacy rejects case-insensitive AAC suffixes outside audio directories: five probes. No historical AAC leak was established.

Final source suite: **976 passed**; source/test/tool Ruff scope passes. Repository-wide `ruff check .` reports 338 pre-existing errors in 28 unchanged historical/archive files; a fresh baseline snapshot reproduces the exact same locations, codes and messages. These are not silently treated as passed or rewritten. Scoped independent association/values/relations probes: **75 passed**.

Independent isolated checks and installed distribution byte checks passed for the frozen release candidate. Installed consumer and live-form checks pass as recorded above. Functional-head remote workflows pass as recorded in `ci-verification.json`; prior failed runs and their stale-pin root cause remain recorded, not erased.

## Reproduce locally

From the NLP repository, with its locked development environment:

```bash
uv run --frozen pytest -q
uv run --frozen ruff check src tests tools
uv run --frozen python tools/verify_distribution.py --help
CORPUS="$HOME/Descargas/HOMEX_Guiones_Evaluacion_Voz"
uv run --frozen python tools/evaluate_semantic_voice.py \
  --base-ref 19d16ff0a428d765b7e89d3b695c02e5ce264b50 \
  --references "$CORPUS/evaluaciones/semantic-120-v1/references-v2" \
  --original-asr audit/real-voice-120/evaluaciones/audit-120/baseline-routing-v2/cases \
  --candidate-asr "$CORPUS/evaluaciones/semantic-120-v1/asr-experiments" \
  --values "$CORPUS/evaluaciones/audit-120/catalog-fixture.json" \
  --output "$CORPUS/evaluaciones/commercial-review-reproduction-$(date +%s)"
```

For offline playback and human decision export, follow [`docs/commercial-voice-review.md`](../../../docs/commercial-voice-review.md). Never pass original audio to the deleting ASR CLI. Reproduction uses a new output directory; do not overwrite historical results. No independent acoustic generalization has been established: all 120 recordings are development data.

## Historical publication inventory and privacy limits

The frozen baseline has 8,293 Git paths, 8,139 distinct blobs and 397,010,245 path bytes. Classification is purpose-based, not permission to delete: 229 runtime/maintenance paths, 6,191 historical evidence paths, 37 last-completed-CI paths and 1,836 frozen development-evidence paths. Full per-file hashes and duplicate groups remain in the private `publication-baseline-v1/` inventory.

All 3,892 ZIP/WHL/DOCX members were hashed and checked for audio names/magic; 262/262 authorization headers were redacted and 2,212 cookie arrays empty. Four non-text trace extras are WOFF2 fonts. Initial unknown binaries were the old sdist, script DOCX and an old demonstration SQLite database (not current acoustic gold); they were inspected read-only. No original audio paths, audio data URIs or JWT-shaped strings were found in that scan. These bounded checks are **not** certification of all visual/private content: 3,606 JPEG trace frames did not receive full human visual review. Regex email/contact candidates are not automatically confirmed leaks. Raw private candidate contexts and database rows are not republished.

No tracked file or historical artifact was deleted. `.atl` remains local and untracked. Before merge, maintainers should decide an explicit retention/review plan for the existing large evidence branch; do not silently replace that decision with history rewriting.

## PR recommendations

1. **NLP:** review relation/value regressions, component source offsets and private decision workflow first. Require fresh green CI and consumer proof for the exact wheel. Historical branch volume needs an explicit review/retention plan: four old trace ZIPs alone occupy 182,055,627 bytes. Do not delete or rewrite them without authorization.
2. **Backend:** consume only the hash-pinned 0.1.23 wheel after installed-adapter/contract and application tests. Preserve historical artifacts, permissions, stock and authoritative commercial calculations. No source-path override counts as wheel proof.
3. **Frontend:** retain the four-form mapping and explicit proposal application. Reverify current backend peer, component-local dimensions, unknown units and all categories; a successful HTTP response alone is insufficient.

No PR, merge or deployment is created by these recommendations. Consumer compatibility and functional-head green CI are verified. The final passive NLP closure-document workflow is verified separately before delivery. Integral commercial validation remains blocked on human decisions even after technical completion.

Risk: none (passive evidence report; no production logic or public contract changes).

## Published branches and closure

| Repository | Branch | Verified functional/consumer head | CI |
|---|---|---|---|
| NLP | `feat/real-voice-120-results` | `801a6a4` (runtime source unchanged from `d9f7c54`) | [4/4](https://github.com/gabriel-arinez/homex-nlp/actions/runs/43286032432) |
| Backend | `feat/real-voice-120-semantic` | `9cc380f` (application source `7dae768`) | [13/13](https://github.com/gabriel-arinez/homex-backend/actions/runs/43288199954) |
| Frontend | `fix/real-voice-120-f09` | `a8e1656` (application source `f00bce6`) | [13/13](https://github.com/gabriel-arinez/homex-frontend/actions/runs/43288195256) |

The first backend/frontend publication each passed12/13 jobs. Their sole failures selected stale independent contract-checkout refs; the corrected immutable peer pins retain every job, command, permission, override and comparison. Full failed and successful console output is preserved locally in `ci-publication-v1/` and `ci-publication-v2/`. No failed result is counted as a pass.

PR recommendation: ready for technical review of these controlled branches, not automatic merge. Maintain the historical-artifact retention decision and complete the human acoustic/association queue before claiming integral commercial validation. No PR, main merge, production deployment or historical deletion occurred.
