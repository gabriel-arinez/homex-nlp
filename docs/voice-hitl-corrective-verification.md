# Final commercial voice validation (2026-11-17)

Final verification is complete on the existing `feat/voice-hitl-review` branches. No PR, push, merge or package publication is authorized. Earlier verification below is historical. The current ledger and `evidence/voice-validation-final.json` bind this final candidate.

## Current contract

**Audio ≥15 seconds → automatic ASR → editable transcript (≥20 words, ≤3,000 characters) → explicit NLP → commercial proposal or abstention → HITL → confirmed application.**

- Microphone maximum: 240 seconds; uploaded files: 300 seconds and 20,000,000 bytes. Rejected decoded audio creates no capture, attempt or outbox job. Browser validation precedes submission; backend decodes before admission. The API runtime now declares the existing PyAV decoder directly because validation precedes the worker.
- Only commercial voice-assistant endpoints enforce the text thresholds. General NLP, manual products and historical inputs retain their existing contracts. Whitespace-separated tokens containing Unicode letters or numbers count as words; isolated punctuation does not. Character counting uses Unicode code points on both sides.
- ASR output is retained intact, including over-limit text. Oversized typing/paste is rejected with a message; existing content is preserved. Over-limit ASR text can be reduced before explicit interpretation.
- Catalog extraction uses positive commercial evidence and category compatibility, not greeting/testing/microphone/name blacklists. Commercial insufficiency still produces abstention or evidence-backed partial fields.
- Thickness assignment compares exact normalized measurements. A different value requires a distinct verified correction event retaining original and final values; edits/reversions reopen review. Existing ownership, immutable provenance and idempotency checks remain.
- Observations no longer receive an entire-input/description fallback. Explicit complementary observations retain evidence; applying proposals preserves manual notes and ignores legacy notes equal to the full transcript.

## Calibration and artifact identity

| Evidence                                            | Words          | Characters | Threshold result |
| --------------------------------------------------- | -------------- | ---------- | ---------------- |
| 120 written scripts                                 | 30–96          | 192–645    | 120/120 pass     |
| 120 stored real ASR transcripts                     | 27–90          | 150–554    | 120/120 pass     |
| Backend historical synthetic 240-second experiment  | Not remeasured | 2,807      | Pass             |
| Frontend historical synthetic 240-second experiment | 99             | 638        | Pass             |

The written snapshot available here peaks at 645 characters, not the approximate 671 in the request. The two long experiments are different synthetic recordings, not genuine four-minute seller dictations. Stored real-ASR duration metadata is null. No evidence available requires raising 3,000 characters; this does not claim universal coverage of real long dictation.

NLP **0.1.29**, wheel SHA-256 `4e8ccb3362152e69ec552917a44c19f839b4f56c737a2e8997f3f23d4ebbff50`. Installed metadata and all 32 package files match the wheel/source; the only changed Python modules relative to 0.1.28 are package identity and catalog extraction. Previous wheels/checksums remain unchanged. Source and installed-wheel NLP suites: **1,209 passed each**.

## Verification ledger

- Observed RED before implementation for thresholds, forbidden-name regressions, observation preservation and thickness integrity; focused GREEN completed.
- Final independent backend suite: **752 passed**; frontend Vitest: **412 passed**. Source and installed NLP suites: **1,209 passed each**.
- Browser verification covers **115 cases**: initial full run **108 passed / 7 failed**, followed by the single scoped test-fixture correction and **7/7 passing rechecks**. The failures used short/undecodable fixtures invalidated by the new thresholds; no production correction was needed. The staged seller-flow/accessibility E2E passed.
- Frontend typecheck/lint/format and production build, backend lint/format/system checks/migration drift, offline locks, NLP/backend builds, generated OpenAPI/types and contract check passed. OpenAPI retains one non-fatal `CategoryEnum` choice-set naming warning and no schema errors.
- Parent reran the reported 23-test voice subset and backend Ruff successfully. The backend feature worktree has a durable ignored `.venv` installed offline with 0.1.29; all 32 package files match the new wheel.
- Implementation commits: NLP `bf67a50`; backend `f311c8d`, `2ccab9a`; frontend `23d3343`, `980720c`, `169c138`. Documentation-only closure is the final branch HEAD. The evidence JSON lists modified files and commands/outcomes. Historical artifacts and prior commits remain intact.
- NLP's configured Makefile lint/format scope (`src tests tools training`), schema export check and offline lock passed. An additional noncanonical whole-tree scan found **338 lint errors / 30 unformatted files** in preserved audit scripts; the exact same counts reproduce on baseline `50216e5`. Those frozen artifacts were not changed. Python repositories do not configure a standalone static typechecker; frontend `vue-tsc` passed.
- RDD remains globally disabled by existing user preference; no native review consent or lifecycle started. Independent functional verification passed for audit/contract/package risk.
- No remote CI or physical microphone/device verification is claimed. Browser tests use synthetic audio and local route stubs; backend tests decode real PCM and exercise the installed NLP package.

## Prior intervention (historical)

# Definitive commercial-validation correction

The existing rule engine is preserved. The correction is local to `feat/voice-hitl-review`; no package was published and no PR or merge was created.

## Behavior

- Explicit `producto:`, `nombre:` and `nombre comercial:` prefixes do not bypass commercial-content validation.
- Greetings, counting, microphone-test phrases and attribute markers without values abstain; legitimate introduced names remain open vocabulary.
- Category contradictions use the primary product identity, not a related noun: chair descriptions remain valid when mentioning desks, and flooring remains valid when mentioning a room with chairs.
- Typed `field_reviews` link actual extracted fields and candidate IDs to commercial warnings, including an accepted price requiring human review. Existing warning strings remain compatible.
- Furniture prefix negatives, quantities, dimensions, materials, prices and rectifications retain their regressions.

## Verified final candidate

| Check                                     | Result                        |
| ----------------------------------------- | ----------------------------- |
| Full source suite                         | 1,185 passed                  |
| Full suite against the installed wheel    | 1,185 passed                  |
| Independent commercial regression subset  | 197 passed                    |
| Ruff and formatting                       | Passed                        |
| Extraction schema drift                   | Passed                        |
| Canonical wheel and sdist reproducibility | Passed, `SOURCE_DATE_EPOCH=0` |

Specific RED evidence: 22 explicit-name/category failures, two primary-versus-related-noun failures, and three bare microphone-test-phrase failures before their fixes. Existing furniture-prefix negatives already abstained. Positive category fixtures were moved to their intended category rather than weakening the new contradiction rule.

## Artifact identity

New local version: **0.1.28**. The backend vendors and installs `homex_nlp-0.1.28-py3-none-any.whl`.

SHA256: `abf68e16979c9cdf64eff534051798cec3a12b9d27672fd0f9fcd4805e825fea`.

Installed module bytes, metadata, runtime guard, backend lock and operational checksum pins agree. Historical 0.1.25, 0.1.26 and 0.1.27 artifacts remain unchanged. The cross-component report is maintained in the frontend repository at the same documentation path.

Risk: items 3 and 5 — additive consumed review contract and coordinated local package integration. Full producer/consumer tests and independent checks cover these changes. Browser speech tests use synthetic fixtures, not a claim of field speech accuracy.
