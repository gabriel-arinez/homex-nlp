# Real-voice audit checkpoint — intervention is NOT complete

120/120 baseline cases executed with auditable individual results; six bounded
root-cause improvements implemented locally and independently checked. Original
audio intact. Commercial category correction is complete for the10 confirmed records.
Publication, full semantic annotation and independent generalization evaluation
remain OPEN. Current snapshots are baseline-routing-v2 and after-nlp-v5;
latest-evaluation.json is the authoritative artifact index.

## ASR (same frozen transcripts before/after NLP changes)

| Current category | Cases | WER | CER |
|---|---:|---:|---:|
|MUEBLE_MEDIDA|73|24.96%|20.55%|
|OTRO|13|18.92%|14.90%|
|PISO_FLOTANTE|7|26.80%|16.52%|
|SILLA|27|16.18%|12.86%|
|Overall|120|22.56%|18.14%|

Case WER/CER use casefolded NFC tokens with punctuation removed except decimal/code
boundaries. Micro aggregation weights by reference length. Raw source/ASR text is
unchanged. No model change, no claimed ASR improvement. Post-fix NLP replay uses
EXACT baseline ASR strings, not retranscribed/edited audio. Source hashes cover
both snapshots. No hearing verification of all120 recordings was available.

Audio duration4677.406s; baseline summed per-case wall560.356s (about0.120 real-time
factor, including extraction/evaluation), model load1.102s; peak process RSS
1,282,048KiB. This is local CPU warm-process observation, not production SLA.

## Partial NLP oracle — NOT full field accuracy

Manually annotated all119 stated script prices independently of the production
parser; independent arithmetic check found zero annotation mismatches. Only85
explicit unit prices form the exact-match denominator;34 unqualified amounts
remain modality-pending and MP0075 has no price. Full field annotation pending.

| Category | Explicit unit cases | ASR input before→after | Correct script before→after |
|---|---:|---:|---:|
| Custom furniture |38|18→18|23→23|
| Chair |27|27→27|27→27|
| Floor |7|7→7|7→7|
| Other |13|10→13|10→13|
| Total |85|62→65|67→70|

No wrong amount among EXTRACTED explicit-unit amounts in this partial oracle;
missing/no-proposal20 ASR cases and15 script cases remain. These are NOT 100%
financial coverage. Some are blocked by lack of an entire product proposal.
Floor thickness8mm matches: reference3/7→7/7, ASR3/7→6/7. PIS0006 ASR says HDF8
without de; hearing/normalization review remains. Five cabinet cases gained a
proposal, and SIL0001's explicit backrest is no longer suppressed by seat context.
26 semantic output changes across15 IDs are retained in after-nlp-v5.

## Verification

- RED batch1:8 failed/3passed, then55 focused/catalog passed.
- RED batch2:9failed/12passed; detected existing con-casillero regression in full
  suite, corrected via existing component filter; final65 focused/catalog passed.
- Final NLP suite799passed; schemas, Ruff lint and format check passed.
- Backend99passed on final candidate, isolated UTF8 PostgreSQL, no production DB.
- Frontend306passed; contract/typecheck/build passed, repository unchanged.
- Real Chromium + actual Whisper + Django/Postgres + form application:4/4 passed
  on final source hashes: MP0001 quantity2/diameter2m/height75cm/price7300;
  SIL0001 name/price5200; PIS0001 thickness8/price125; MP0005 OTRO price12000,
  literal description and no forced chair-only fields. No inventory/commercial
  writes in these four probes. Furniture type still explicitly needs selection.
- Latest numeric-name batch: RED3failed/27passed; GREEN74 focused/catalog tests;
  final suite799passed. Two additional ASR cases (MP0004/0062) now retain literal
  numeric-leading names and full observations without inventory/quantity inference.
- Latest source backend99passed; three ACTUAL poltrona audio→Chromium→Whisper→
  Django/PostgreSQL→OTRO application checks passed for MP0004/0062/0067 at5500.
  Observations equal raw ASR input; zero commercial writes or inventory changes.
  All24 current source hashes match after-nlp-v5 and all240 audio hashes are intact.
  This is additional latest-candidate proof, not a replacement of older4-form traces.
- Independent scratch probes preserve legacy CLI output (ignoring latency only),
  negation, alternatives, other measurement axes and component association.
- All240 audio hashes intact after real integration. Services stopped.

Environment-only initial failures retained: SQL_ASCII scratch DB caused Unicode
seed errors (recreated UTF8); frontend missing local MSW URL/symlinked PDF worker
(copied dependencies and supplied fixture URL); one custom-form selector failed
BEFORE upload and was corrected in the scratch probe only. The incorrect schema
module command failed; the documented tools/export_schemas.py check passed.
No failures hidden or counted as successful executions.

## Open work / decision required

1. RESOLVED: MP-0004/0062/0067 are OTRO, explicitly confirmed by the user.
   Totals73 custom furniture/27 chairs/7 floors/13 other,120 cases. Original
   raw baseline preserved; corrected baseline uses original rules at c94e7a8.
   The three additional baseline price matches are a CORPUS ROUTING correction,
   not an NLP improvement. Current before/after improvement is still three prices.
2. Full expected-field annotation and review of doubtful audio; classify all
   remaining warnings/omissions individually. Root matrix contains observed
   candidates, not a claim that unreviewed cases are causally resolved.
3. Remaining product/compartment co-reference, cubos/estaciones vocabulary,
   natural-name boundaries, spoken model decoding, USB/HDMI accessory vocabulary,
   and backend furniture-type mapping. Do not force outcomes or invent data.
4. Independent NEW real dictations grouped by family/source; tests/paraphrases and
   reviewer probes are not a held-out audio study. All120 are development data.
5. Versioned package release/vendor integration, reviewable commit strategy,
   authorized remote credential/destination, commits/push/remote CI. Local chain ff4df92→c02c6df→f139bd2→40e4665 now committed; remote
   authorization/push/PR/CI remain pending. Installed backend wheel still0.1.21;
   integration ran candidate source explicitly via PYTHONPATH. No deployment.

## Reproduce locally

From the NLP branch audit/real-voice-120, with existing dependencies/model:

```bash
CORPUS="$HOME/Descargas/HOMEX_Guiones_Evaluacion_Voz"
.venv/bin/python -m pytest -q -p no:cacheprovider
.venv/bin/python tools/export_schemas.py --check
.venv/bin/ruff check src tests tools training
.venv/bin/ruff format --check src tests tools training
# Use a NEW output directory. For the original baseline use the exact base commit,
# not modified rules. The original frozen execution already lives in baseline/.
.venv/bin/python -m tools.evaluate_real_voice \
  --corpus "$CORPUS" --output "$CORPUS/evaluaciones/audit-120/new-current-run" \
  --model "$HOME/modelos/faster-whisper-small" \
  --values "$CORPUS/evaluaciones/audit-120/catalog-fixture.json"
# Replay the original ASR strings with current NLP; fresh snapshot name required.
PYTHONPATH=.:src .venv/bin/python \
  "$CORPUS/evaluaciones/audit-120/replay_and_analyze.py" after-nlp-new baseline-routing-v2
# Actual integration setup/scripts used are preserved here:
cd "$CORPUS/evaluaciones/audit-120/live-e2e-final/reproduce"
bash bootstrap.sh
```

The packaged E2E bootstrap wrapper was structurally checked but not separately
rerun; constituent setup/test commands executed and passed. It requires locally
installed PostgreSQL16, browser/dependencies and the three repos at recorded
commits plus candidate NLP source. It starts ONLY isolated scratch services and
synthetic accounts. See reproduce/README.md and retained command logs. No remote
session or production credentials are needed.

## Evidence index

- diagnosis-initial.md, baseline/{identity,environment,summary}.json
- baseline/cases/*.json:120 historical original execution cases
- baseline-routing-v2/cases/*.json:120 current-category baseline cases, immutable ASR
- latest-evaluation.json: current snapshot pointers and provenance
- transcriptions-baseline.jsonl and120-case-results.jsonl: full consolidated data
- after-nlp-v5/cases/*.json:120 final paired NLP, word diffs and partial labels
- after-nlp-v5/{summary,semantic-changes,partial-manual-oracle,source-hashes}.json
- after-nlp-v5/case-matrix.csv, root-cause-matrix.{json,csv}
- duplicate-and-leakage-groups.json, furniture-review-buckets.json
- audio-ledger.json, reclassification.json, before-reclassification/, before-poltronas/
- live-e2e-final/: previous four-form browser evidence;
- live-e2e-poltronas/: latest-candidate real poltrona responses/screenshots/traces, hashes/reproduction
- candidate-source-v2/: exact latest local candidate; latest-evaluation.json indexes active snapshots
- verification-probes/: independent probes and normalized baseline/CLI outputs
- ../../logs/audit-120-*.log: full executed evaluation/test output. Early chat-only
  reconnaissance output was not fully logged; snapshots/version logs retain its
  material evidence, not a reconstructed verbatim console transcript.

Risk: item3 (shared extraction logic/public consumer behavior); independent
verification performed. Corpus metadata edits also verified for item1 safety.

## Local feature-chain checkpoint

User approved Feature Branch Chain. Local tracker`feat/real-voice-120` is based on
c94e7a8; evaluation child targets tracker; extraction child targets evaluation.
Actual child review budgets397/339/205 authored lines. Commits:ff4df92 specification,
c02c6df evaluator,f139bd2 fixes,40e4665 verification evidence. No merge, push or
remote lookup performed. See local-chain.json and pr-drafts/ for exact refs/bodies.

Each code slice was verified in a clean detached worktree: evaluator769 tests,
extraction799 tests; schemas/lint/format/curated corpus/inventory passed. Fully
offline wheel and sdist installation/privacy/required-files/rebuild checks passed.
Temporary same-version0.1.21 test artifacts are in packaging-smoke-only/; they are
NOT a versioned release and were never installed into the backend or published.
Original workspace published distributions remain unchanged.

Next publication prerequisite: explicit authorization for remote repository and
credential/session, followed by repository policy/issue lookup. No approval or
issue identity has been inferred. The full audit remains incomplete.

## Single-branch publication override

The user superseded the earlier chain plan and requested one published branch,
all implemented modifications and all evaluation results. Current destination:
`gabriel-arinez/homex-nlp`, branch `feat/real-voice-120-results`. No PR or merge.
The prior chain documents remain historical artifacts, not active instructions.
The full audit is still incomplete for the explicitly listed semantic/audio,
independent-evaluation and versioned-release limitations; publication does not
turn those pending criteria into completed results.

The public copy includes all evaluation/history/results/log snapshots and current
manifest/reference/control metadata. Independent privacy/fidelity verification
passed:120-case outputs/24 source hashes/category routing preserved;240 original
audio hashes retained; no original audio, session credentials, database/model or
cache published. Credential-bearing values in four Playwright traces/two configs
are redacted in COPIES; all trace events/screenshots remain. No source audio body
was present in those trace archives. Raw local evidence remains untouched.
See PUBLICATION-MANIFEST.json for source/export hashes and redaction details.
