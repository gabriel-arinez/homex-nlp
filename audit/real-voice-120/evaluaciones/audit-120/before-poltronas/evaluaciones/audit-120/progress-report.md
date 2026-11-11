# Real-voice audit checkpoint — intervention is NOT complete

120/120 baseline cases executed with auditable individual results; five bounded
root-cause improvements implemented locally and independently checked. Original
audio intact. Publication, definitive categories, full semantic annotation and
independent generalization evaluation remain OPEN.

## ASR (same frozen transcripts before/after NLP changes)

| Provisional category | Cases | WER | CER |
|---|---:|---:|---:|
| Custom furniture |76|24.63%|20.32%|
| Chair |27|16.18%|12.86%|
| Floating floor |7|26.80%|16.52%|
| Other |10|19.93%|15.32%|
| Overall |120|22.56%|18.14%|

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
| Custom furniture |41|18→18|23→23|
| Chair |27|27→27|27→27|
| Floor |7|7→7|7→7|
| Other |10|7→10|7→10|
| Total |85|59→62|64→67|

No wrong amount among EXTRACTED explicit-unit amounts in this partial oracle;
missing/no-proposal23 ASR cases and18 script cases remain. These are NOT 100%
financial coverage. Some are blocked by lack of an entire product proposal.
Floor thickness8mm matches: reference3/7→7/7, ASR3/7→6/7. PIS0006 ASR says HDF8
without de; hearing/normalization review remains. Five cabinet cases gained a
proposal, and SIL0001's explicit backrest is no longer suppressed by seat context.
24 semantic output changes across13 IDs are retained in after-nlp-v3.

## Verification

- RED batch1:8 failed/3passed, then55 focused/catalog passed.
- RED batch2:9failed/12passed; detected existing con-casillero regression in full
  suite, corrected via existing component filter; final65 focused/catalog passed.
- Final NLP suite790passed; schemas, Ruff lint and format check passed.
- Backend99passed on final candidate, isolated UTF8 PostgreSQL, no production DB.
- Frontend306passed; contract/typecheck/build passed, repository unchanged.
- Real Chromium + actual Whisper + Django/Postgres + form application:4/4 passed
  on final source hashes: MP0001 quantity2/diameter2m/height75cm/price7300;
  SIL0001 name/price5200; PIS0001 thickness8/price125; MP0005 OTRO price12000,
  literal description and no forced chair-only fields. No inventory/commercial
  writes in these four probes. Furniture type still explicitly needs selection.
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

1. Business category of MP0004/0062/0067 (poltronas fijas) before definitive metrics.
2. Full expected-field annotation and review of doubtful audio; classify all
   remaining warnings/omissions individually. Root matrix contains observed
   candidates, not a claim that unreviewed cases are causally resolved.
3. Remaining product/compartment co-reference, cubos/estaciones vocabulary,
   natural-name boundaries, spoken model decoding, USB/HDMI accessory vocabulary,
   and backend furniture-type mapping. Do not force outcomes or invent data.
4. Independent NEW real dictations grouped by family/source; tests/paraphrases and
   reviewer probes are not a held-out audio study. All120 are development data.
5. Versioned package release/vendor integration, reviewable commit strategy,
   authorized remote credential/destination, commits/push/remote CI. No remote
   operation performed; no CI status invented. Installed backend wheel still0.1.21;
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
  "$CORPUS/evaluaciones/audit-120/replay_and_analyze.py" after-nlp-new
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
- baseline/cases/*.json:120 raw ASR/paired NLP cases
- transcriptions-baseline.jsonl and120-case-results.jsonl: full consolidated data
- after-nlp-v3/cases/*.json:120 final paired NLP, word diffs and partial labels
- after-nlp-v3/{summary,semantic-changes,partial-manual-oracle,source-hashes}.json
- after-nlp-v3/case-matrix.csv, root-cause-matrix.{json,csv}
- duplicate-and-leakage-groups.json, furniture-review-buckets.json
- audio-ledger.json, reclassification.json, before-reclassification/
- live-e2e-final/: browser responses/screenshots/traces, hashes/reproduction
- verification-probes/: independent probes and normalized baseline/CLI outputs
- ../../logs/audit-120-*.log: full executed evaluation/test output. Early chat-only
  reconnaissance output was not fully logged; snapshots/version logs retain its
  material evidence, not a reconstructed verbatim console transcript.

Risk: item3 (shared extraction logic/public consumer behavior); independent
verification performed. Corpus metadata edits also verified for item1 safety.
