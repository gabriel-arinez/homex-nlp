"""Build an honest audit checkpoint; not a declaration of overall completion."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'evaluaciones/audit-120'
base=[json.loads(p.read_text()) for p in sorted((OUT/'baseline/cases').glob('*.json'))]
after={p.stem:json.loads(p.read_text()) for p in (OUT/'after-nlp-v3/cases').glob('*.json')}
assert len(base)==len(after)==120
with (OUT/'transcriptions-baseline.jsonl').open('x') as f:
 for row in base:
  f.write(json.dumps({'id':row['id'],'category':row['category'],'audio':row['audio'],'reference':row['reference'],'asr':row['asr']},ensure_ascii=False)+'\n')
with (OUT/'120-case-results.jsonl').open('x') as f:
 for row in base:f.write(json.dumps({'baseline':row,'after_nlp':after[row['id']]},ensure_ascii=False)+'\n')
# Source/family clusters are leakage warnings, not recordings to delete.
groups=defaultdict(list)
for r in base:groups[r['source']['grupo_familia']].append(r['id'])
exact=defaultdict(list)
for r in base:exact[hashlib.sha256(r['reference'].encode()).hexdigest()].append(r['id'])
ledger=json.loads((OUT/'audio-ledger.json').read_text())
audio=defaultdict(list)
for r in ledger:audio[r['audio']['ruta_audio_esperada']['sha256']].append(r['id'])
(OUT/'duplicate-and-leakage-groups.json').write_text(json.dumps({
 'family_groups':dict(groups),'exact_reference_duplicates':[v for v in exact.values() if len(v)>1],
 'exact_original_audio_duplicates':[v for v in audio.values() if len(v)>1],
 'policy':'All 120 cases are development data. Never split family/source near-duplicates across future tuning and independent evaluation. No recording removed.'},ensure_ascii=False,indent=2)+'\n')
warning_buckets={}
for stage in ['baseline','after']:
 buckets=defaultdict(list)
 for r in base:
  if r['category']!='MUEBLE_MEDIDA':continue
  n=r['nlp_reference'] if stage=='baseline' else after[r['id']]['nlp_reference']
  for w in n.get('warnings',[]):
   if w['code']!='RULES_ONLY_MODE':buckets[w['code']].append(r['id'])
 warning_buckets[stage]=dict(buckets)
(OUT/'furniture-review-buckets.json').write_text(json.dumps(warning_buckets,indent=2)+'\n')
def defect(id,kind,impact,evidence,state,reason):return dict(id=id,classification=kind,commercial_impact=impact,evidence=evidence,state=state,root_cause_or_limitation=reason)
defects=[
 defect('C01','CORPUS_CLASSIFICATION','Wrong extractor and denominator','MP-0005/0063/0068, SIL-0010/0019/0020/0029; reclassification.json','CORRECTED_CONFIRMED','Seven user-confirmed sillones incorrectly assigned to furniture/chair; IDs/audio paths unchanged. Three existing otros labels canonicalized to OTRO.'),
 defect('C02','CORPUS_METADATA','Misleading corpus readiness','before-reclassification/control/RESUMEN.json vs 240 verified files','CORRECTED','Historical summary had zero audio/conversions. Current summary recomputed from actual inventory.'),
 defect('N01','NLP_RULE','Unit price omitted','MP-0005/0063/0068; rules.py price_mentions; unit regressions','CORRECTED','Explicit precio por juego/pieza/barra/metro cuadrado missing in declared-unit grammar; reuse exact monetary grammar/evidence.'),
 defect('N02','NLP_NORMALIZATION_BOUNDARY','Floor thickness omitted','PIS-0001; catalog.py FloorExtractor; conjunction regressions','CORRECTED','Shared numeric token grammar includes y; prefix conjunction consumed into invalid cardinal. Exclude leading y, preserve internal y.'),
 defect('N03','NLP_SEMANTIC_ASSOCIATION','Backrest material omitted','SIL-0001 reference input; catalog.py feature_context','CORRECTED','Previous seat context suppressed an explicit respaldo match. Explicit local component outranks prior component; bare-material association unchanged.'),
 defect('N04','NLP_RULE','HDF board thickness omitted','PIS-0004/0005/0006 reference inputs; after-nlp-v3','CORRECTED_REFERENCE_INPUT','Only labeled thickness syntax recognized. Add bounded HDF board-gauge grammar, not arbitrary unit guessing; negative/alternative/other-axis controls pass.'),
 defect('N05','NLP_LEXICON','Furniture has no proposal','MP-0034/0035/0036/0040/0041; rules.py PRODUCTS','CORRECTED_BOUNDED','Missing armario and accented clóset; storage vocabulary extended including casillero without assigning backend type IDs.'),
 defect('R01','INTRODUCED_REGRESSION','Existing furniture proposal rejected','test_v16_safety.py::test_secondary_out_of_scope_words_do_not_reject_furniture; nlp-suite-v2.log','CORRECTED_BEFORE_ACCEPTANCE','New casillero product detection saw integrated compartments as independent product. Existing con-cajonera exclusion reused for casillero; original regression test now passes.'),
 defect('A01','ASR_OR_NORMALIZATION_OR_REFERENCE','Lost structured thickness','PIS-0006: reference HDF de ocho milímetros, ASR HDF8 milímetros','PENDING_LISTENING','Reference input now gives8; ASR input abstains. Cannot prove whether the speaker omitted de or ASR did; no rewrite/hallucinated gauge applied.'),
 defect('N06','SEMANTIC_ASSOCIATION_OR_LEGITIMATE_MULTIPRODUCT','No furniture proposal',warning_buckets['after'].get('MULTIPLE_MAIN_PRODUCTS',[]),'PENDING_CASE_REVIEW','Repeated descriptions, integrated compartments and actual multi-product sets need separate attribution. Do not collapse all identical nouns or force several products into singular public proposal.'),
 defect('N07','UNSUPPORTED_VOCABULARY_OR_CORPUS_CLASSIFICATION','No furniture proposal',warning_buckets['after'].get('NO_PRODUCT',[]),'PENDING_BUSINESS_REVIEW','Remaining poltronas, cubos móviles and estaciones require classification/domain treatment. Poltronas MP-0004/0062/0067 not automatically moved by synonym.'),
 defect('N08','NLP_NAME_BOUNDARY','Proposal name contains dimensions','OTR-0001 reference; PIS-0001 ASR; original fields preserved','PENDING','Heuristic initial noun phrase can swallow technical clause or trailing preposition. Literal observations preserve original text; no universal name gold annotation yet.'),
 defect('N09','UNSUPPORTED_SPOKEN_MODEL_OR_ASR','Incomplete catalog model','SIL/PIS spelled model phrases; full fields/warnings per-case','PENDING','Spoken letters and digit groupings not fully decoded by literal code recognizer. Do not replace unresolved model by source SKU unless actually spoken.'),
 defect('N10','NLP_UNSUPPORTED_ACCESSORY_VOCABULARY','USB/HDMI not structured','MP-0001 reference contains two USB and two HDMI; accessory list only tomacorrientes','PENDING','Current accessory vocabulary lacks explicit USB/HDMI/caja eléctrica labels. Full dictation remains available in backend technical original description.'),
 defect('B01','LEGITIMATE_PRICE_MODALITY_AMBIGUITY','Unit/total cannot be safely inferred','34 script prices use precio de without explicit unit/total; partial-manual-oracle','REVIEW_REQUIRED_NOT_AUTOMATIC_FAILURE','Do not turn an unqualified amount into authoritative unit/total, apply discounts or stock movements.'),
 defect('I01','CATALOG_DICTIONARY_CONTEXT','Foreign key suggestions unavailable','Controlled fixture has no floor material values; backend static seed leaves floor dictionaries empty','ENVIRONMENT_OR_UNSUPPORTED_CONTEXT','Do not invent active IDs for HDF/brands/colors. This is not a measured ASR or NLP defect by itself.'),
 defect('I02','BACKEND_PROJECTION_UNRESOLVED_TYPE','Manual furniture-type selection','MP-0001 live-e2e-final; TIPO_NO_RESUELTO','PENDING_MAPPING_REVIEW','Correct quantity/dimensions/price reach UI, but mesas is not assigned an active furniture type. Proportional abstention avoids false ID; compare consumer dictionary and supported synonyms before any change.'),
 defect('E01','EVALUATION_LIMITATION','No full semantic accuracy denominator','120 cases PENDING full field annotation/listening; new probes not independent real audio','OPEN','Partial financial/floor oracle only. No generalization demonstrated. All120 used for development; retain family grouping.'),
 defect('P01','UNPUBLISHED_CANDIDATE','Installed consumer remains old package','Backend wheel homex-nlp0.1.21; tests explicitly used candidate PYTHONPATH','OPEN','Need versioned distribution/integration and authorized publication destination+credential before remote use. No remote CI run or commits pushed.'),
]
(OUT/'root-cause-matrix.json').write_text(json.dumps(defects,ensure_ascii=False,indent=2)+'\n')
with (OUT/'root-cause-matrix.csv').open('x',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(defects[0]));w.writeheader();w.writerows(defects)
initial='''# Initial diagnosis reconstructed from frozen baseline evidence

The initial 120-case execution completed before any extraction-rule changes. This
report indexes its immutable outputs; it is not independent audio adjudication.

## Baseline

| Repository | Branch at start | Exact HEAD |
|---|---|---|
| homex-nlp | main | c94e7a89995a7157bd113a03bb8304321d30b0b1 |
| homex-backend | main | ee6c80f13ff76e23c4c572c81042a0b9760db033 |
| homex-frontend | main | ecb7f23b4d7f25317ae1501733cc8c915bed63c1 |

NLP started with untracked `.atl/`, preserved. Other two repositories clean.
Effective NLP0.1.21, faster-whisper1.2.1, CTranslate2 4.8.2, spaCy3.8.13,
Pydantic2.13.4, Python3.11.15. Whisper Small CPU/int8 with Spanish language;
other inference parameters are faster-whisper defaults. Exact model-file hashes
and source hashes are in baseline/identity.json. ASR service/CLI consume input
paths; evaluation uses disposable copies. AAC is not directly supported by its
validator, so previously verified PCM16/mono/16kHz WAVs are used.

Backend Django5.2.17/DRF3.18.2 uses a vendored NLP0.1.21 wheel. Frontend installed
Vue3.5.42, Vite8.3.4, Vitest4.1.12, TypeScript6.0.3, Playwright1.63.0,
Node24.18.1 (see final-parent-spotcheck log). Lockfiles/HEAD define exact source.

## Input audit

120 unique matching manifest/reference/source IDs; 120 AAC and120 WAV.
Seven confirmed sillones reclassified OTRO, with immutable metadata backups.
Current grouping76 furniture/27 chairs/7 floor/10 OTRO remains PROVISIONAL pending
business confirmation of three poltronas. Folders/ID prefixes are not categories.
All240 audio hashes and source/reference scripts preserved. Historical reading
DOCX/group documents are not relabeled; they are historical recording artifacts,
not authoritative routing. Source metadata issues (35 recorded) remain traceable.
Family/exact duplicate groups are recorded separately; nothing was deleted.

## Flow and responsibilities

NLP AsrService -> FasterWhisperAdapter, segment consumption -> verbatim transcript.
Backend apps/capturas/asr.py caches model by process, serializes lazy inference;
pipeline.py stores transcript, deletes its temporary audio, invokes category
extractor, validates and projects proposal. Furniture uses AdaptadorNLP and
PRF04 projection; catalog uses CatalogRequest with active dictionary records and
ProductoSerializer field validation. Backend computes authoritative totals and
stock; NLP is a suggestion only. Frontend CapturaCatalogo applies supported fields
to ProductoForm; CapturaAsistida/configurator mapper handles custom furniture.
A valid JSON alone is not proof of useful form application.

## Baseline findings

See baseline/summary.json for category WER/CER; raw cases retain both reference-input
and ASR-input extraction. Global script-relative WER1495/6627=22.5592%,
CER7758/42777=18.1359%. Digit-vs-word number spellings count as text edits even
where commercial meaning is unchanged (e.g. MP0001), so these rates are NOT
commercial error rates. Reference audio adjudication remains pending.

Observed lexical/grammar gaps and safe bounded fixes are in root-cause-matrix.
NO_PROPOSAL/multiple-product cases must not all be assigned one presumed cause.
No model/dependency/public schema was changed for this checkpoint.
'''
(OUT/'diagnosis-initial.md').write_text(initial)
report='''# Real-voice audit checkpoint — intervention is NOT complete

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
.venv/bin/python -m tools.evaluate_real_voice \\
  --corpus "$CORPUS" --output "$CORPUS/evaluaciones/audit-120/new-current-run" \\
  --model "$HOME/modelos/faster-whisper-small" \\
  --values "$CORPUS/evaluaciones/audit-120/catalog-fixture.json"
# Replay the original ASR strings with current NLP; fresh snapshot name required.
PYTHONPATH=.:src .venv/bin/python \\
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
'''
(OUT/'progress-report.md').write_text(report)
print('Report checkpoint built; baseline and after each contain120 cases.')
print('Reference warning buckets before/after:',{stage:{k:len(v) for k,v in buckets.items()} for stage,buckets in warning_buckets.items()})
print('Exact audio duplicates:',[v for v in audio.values() if len(v)>1])
print('Report does not claim completion, generalization or publication.')
