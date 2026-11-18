# Commercial recognition 0.1.30: verified scope and limits

The candidate fixes the five requested behavior classes without changing ASR,
observations extraction, or schema. The frozen 120-case corpus is **unchanged**;
measurable gains occur in explicit development probes, not historical scalar
coverage. This is not evidence of independent acoustic generalization.

## Causes and chosen corrections

| Finding | Cause | Correction and tradeoff |
| --- | --- | --- |
| Unlisted commercial names | `_PRODUCT_CUE` was the sole implicit-name identity gate | Keep existing short product identities; admit short phrases using productive descriptor morphology/proper-name complements, not more product nouns. Unusual noun–noun compounds may still require explicit naming. |
| Natural explicit introductions | Extraction and eligibility used different patterns, with eligibility start-anchored | Reuse one introduction grammar, bind it to the accepted name span, retain correction/negation handling. Conversational references do not become declarations. |
| Generic furniture | A narrow detail regex excluded MDF, glass and unfamiliar feature complements | A local positive `de/en/con` complement admits a partial proposal; its text remains unresolved review evidence, not invented structured material/feature values. Existing attribute extractors remain authoritative. |
| Microphone tests | Explicit naming could carry ambiguous audio-test prose without a review | Pure tests still abstain. Explicit ambiguous names retain literal evidence and `AMBIGUOUS_COMMERCIAL_NAME` review. Words are not globally forbidden. |
| Backend postvalidation | Fields and evidence changed after validation, but field reviews retained accepted-price messaging | Reclassify linked reviews to `BACKEND_VALIDATION_REJECTED`; stable identities/spans and historical captures remain intact; stale suggestion warnings are removed only for discarded fields. Rejected fields remain absent; manual correction retains provenance checks. |

Expanding a product whitelist was rejected because the domain is open. Accepting
all two-word strings was also rejected: the full suite exposed repeated nonsense
and new probes exposed ordinary conversation. No NER model or dependency was added.

## Fixed-input results

Source baseline: `5fa4ace20e69bf1ba876b59b61a7edac4118ed15` (0.1.29).
Every Python source member of the Backend's existing 0.1.29 wheel matched this
baseline byte-for-byte; that wheel SHA256 is
`4e8ccb3362152e69ec552917a44c19f839b4f56c737a2e8997f3f23d4ebbff50`.
The old evaluator default `b851b5a` was **not** used as 0.1.29.

| Original ASR development indicator | 0.1.29 | 0.1.30 | Delta |
| --- | ---: | ---: | ---: |
| Identical fixed inputs | 120 | 120 | 0 |
| Script-relative supported scalar matches | 549 / 1000 | 549 / 1000 | 0 |
| Full annotation scalar matches | 549 / 1087 | 549 / 1087 | 0 |
| Script-relative unmatched tuples (not confirmed speech omissions) | 538 | 538 | 0 |
| Cases without proposal | 7 | 7 | 0 |
| Cases with commercial values/evidence/association changes | — | 0 | 0 |
| Verified correct names / incorrect values / unjustified proposals | Not fully annotated | Not fully annotated | Not measurable |
| Correct abstentions / component-association accuracy | Not independently verified | Not independently verified | Not measurable |

The controlled script-input diagnostic also yields 549/1000 and seven abstentions
for both versions. All five **previously saved** ASR variants preserve their
outcomes: 544/541/543/542/543 supported matches respectively. Whisper was not run.
Historical scalar references are incomplete, not a complete acoustic gold set:
**precision, recall and F1 are intentionally not calculated**. An unmatched
prediction is not automatically an incorrect value or false proposal.

Corpus storage groups remain MP=79, SIL=31, PIS=7, OTR=3. Existing semantic routing
is MUEBLE_MEDIDA=73, SILLA=27, PISO_FLOTANTE=7, OTRO=13; it was not rewritten to
inflate results. Machine reports preserve both original ID group and routed
category, every case and field denominator.

### Routed category breakdown (same in both versions)

| Category | Cases | Supported script matches | No proposal |
| --- | ---: | ---: | ---: |
| MUEBLE_MEDIDA | 73 | 430/767 | 7 |
| OTRO | 13 | 20/20 | 0 |
| PISO_FLOTANTE | 7 | 21/28 | 0 |
| SILLA | 27 | 78/185 | 0 |

Field-specific matches/misses and predictions are retained for all categories
in `semantic/summary.json` and every case in `report/report.json`; these include
unsupported category fields, so their full denominators differ from supported
scalar coverage. Components, units, associations, offsets and decisions were
also compared as complete commercial payloads, with zero deltas—not certified
correct by the scalar matcher.

### Directed text diagnostics (development, not a held-out set)

The 25 deterministic probes have explicit expectations only for product names,
proposal presence, and the two named ambiguity reviews. No claim is made that
this oracle completely annotates every commercial attribute.

| Indicator | 0.1.29 | 0.1.30 | Delta |
| --- | ---: | ---: | ---: |
| Correct positive names | 4 / 17 | 17 / 17 | +13 |
| Correct negative abstentions | 8 / 8 | 8 / 8 | 0 |
| Unjustified proposals among these eight negative cases | 0 | 0 | 0 |
| Required ambiguity reviews | 0 / 2 | 2 / 2 | +2 |
| Cases matching all scoped expectations | 10 / 25 | 25 / 25 | +15 |

| IDs | Cases | Outcome |
| --- | --- | --- |
| DEV-01–04 | Espejo decorativo; Armario metálico; Librero modular; Ventana corrediza | Four recovered names |
| DEV-05–08 | The four requested natural introductions | Four corrected names |
| DEV-09–13 | MDF, glass, wheels, LED and lacquered-finish generic furniture | Five partial proposals recovered, absent price/dimensions not invented |
| DEV-14–15 | Greeting/microphone and counting/audio test | Correct abstention unchanged |
| DEV-16–17 | Producto: prueba de voz; Nombre: prueba | Literal names unchanged; human review added |
| DEV-18–19 | Silla Probando; Nombre comercial: Micrófono Aurora | Correct names unchanged |
| DEV-20–25 | Ordinary conversation and repeated nonsense | Correct abstention unchanged |

Every original corpus ID is unchanged; there is no improved/worsened original-ASR
ID to list. Full by-ID evidence is in the generated report, not silently omitted.
New linguistic probes were used during development and are not independent validation.

## Reproduce locally

Set `CORPUS` to the supplied corpus root; use Python 3.11 with the locked project
dependencies. Both NLP snapshots run under the same interpreter and dependencies.
Choose new external output directories; no historical reference file is modified.

```bash
PYTHONPATH=src .venv/bin/python tools/evaluate_semantic_voice.py \
  --base-ref 5fa4ace20e69bf1ba876b59b61a7edac4118ed15 \
  --references "$CORPUS/evaluaciones/semantic-120-v1/references-v2" \
  --original-asr audit/real-voice-120/evaluaciones/audit-120/baseline-routing-v2/cases \
  --candidate-asr "$CORPUS/evaluaciones/semantic-120-v1/asr-experiments" \
  --values "$CORPUS/evaluaciones/audit-120/catalog-fixture.json" \
  --output "$NEW/semantic"
PYTHONPATH=src:. .venv/bin/python tools/report_commercial_differential.py \
  --evaluation "$NEW/semantic" \
  --probes data/evaluation/commercial-0130-probes.jsonl \
  --output "$NEW/report"
```

Current local evidence: `evaluaciones/commercial-0130-v2/` under the corpus.
`semantic/identity.json` pins sources, dependencies, input and reference hashes;
`report/report.json` contains every original ID, category and field breakdown,
all 25 probes and scoped outcomes. Raw transcripts/audio are not added to the package.

## Verification status

- RED: naming 15 failures initially; generic furniture eight failures; Backend
  rejected-review coherence four failures; new sentence-fragment probes six failures.
- Final NLP suite: **1275 passed**, including reporting predicates and five
  independent-verifier regression probes. Independent verification found a
  negative-MDF false proposal and three natural-name boundary/correction errors;
  all five were reproduced RED, corrected in one batch, and the focused
  257-test catalog check passed. Final frozen comparison was regenerated afterward.
- Ruff/check-format, schema export, four curated corpus validations, PRF04 audit,
  and all four DocBin conversions passed.
- Backend full suite with installed 0.1.29 plus adapter fix: 758 passed.
- Existing Frontend voice-review component tests: 8 passed; no Frontend source change.
- Final corrected Backend suite with ordinary installed 0.1.30 wheel: **758 passed**,
  zero errors, skips or warnings; all 32 installed package files match the vendor
  wheel byte-for-byte. Exact version/hash checks remain enforced.
- Independent verifier cleared both negative-MDF cases and all three natural-name
  boundaries/corrections. An additional scratch-only Frontend test consumed the
  actual final Backend rejection payload: **1 passed**, no price autofill, exact
  rejection message, preserved audit IDs and null original discarded value.
  Its first harness attempts omitted capture_id; only the corrected harness
  outcome is product evidence. No Frontend source was changed.
- Final wheel/sdist reproducibility, privacy and isolated-install check is recorded
  in external `package-verification.log` after documentation normalization.
- PR chains are published with explicit authorization. See the linked PR checks
  below for current remote CI; no merge or release was requested or performed.
- RDD: explicitly globally off, respected; independent functional verification is separate.

The initial installed-wheel integration exposed stale 0.1.29
consumer guards (204 failures / 13 errors); exact version/hash guards, vendored
artifact, lock and operational identity checks were advanced together, not
removed. Final corrected-consumer verification passed as recorded above.

## Remaining limitations

Rules are not a complete Spanish grammar or commercial-intent oracle. A novel
phrase can remain ambiguous; explicit naming plus human review is the fallback.
Generic description evidence is intentionally not mapped to unsupported material
fields. No complete verified human transcript/association oracle was established
for the 120 cases; historical acoustic-review statuses remain pending. This
candidate demonstrates targeted text improvement and corpus non-regression, not
a measured generalization improvement or certified commercial precision.

## Published feature-branch chains

No merge, deployment or release is authorized. Trackers remain draft until all
children and coordinated integration have been reviewed. Current CI status is
available on each linked PR; a pending or skipped external review is not a pass.

| Repository | PR | Head → base | Role |
| --- | --- | --- | --- |
| homex-nlp | [#48](https://github.com/gabriel-arinez/homex-nlp/pull/48) | `feat/commercial-recognition-0130` → `main` | Draft tracker, no merge |
| homex-nlp | [#49](https://github.com/gabriel-arinez/homex-nlp/pull/49) | `feat/commercial-recognition-0130-identity` → `feat/commercial-recognition-0130` | Review slice |
| homex-nlp | [#50](https://github.com/gabriel-arinez/homex-nlp/pull/50) | `feat/commercial-recognition-0130-names-ci` → `feat/commercial-recognition-0130-identity` | Review slice |
| homex-nlp | [#51](https://github.com/gabriel-arinez/homex-nlp/pull/51) | `feat/commercial-recognition-0130-furniture-ci` → `feat/commercial-recognition-0130-names-ci` | Review slice |
| homex-nlp | [#52](https://github.com/gabriel-arinez/homex-nlp/pull/52) | `feat/commercial-recognition-0130-evaluation-ci` → `feat/commercial-recognition-0130-furniture-ci` | Review slice |
| homex-nlp | [#53](https://github.com/gabriel-arinez/homex-nlp/pull/53) | `feat/commercial-recognition-0130-report-ci` → `feat/commercial-recognition-0130-evaluation-ci` | Review slice |
| homex-backend | [#63](https://github.com/gabriel-arinez/homex-backend/pull/63) | `feat/commercial-recognition-0130` → `main` | Draft tracker, no merge |
| homex-backend | [#64](https://github.com/gabriel-arinez/homex-backend/pull/64) | `feat/commercial-recognition-0130-reviews` → `feat/commercial-recognition-0130` | Review slice |
| homex-backend | [#65](https://github.com/gabriel-arinez/homex-backend/pull/65) | `feat/commercial-recognition-0130-package` → `feat/commercial-recognition-0130-reviews` | Review slice |
