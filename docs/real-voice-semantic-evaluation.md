# Attribute development changes with four-cell evaluation

`tools/evaluate_semantic_voice.py` compares baseline commit `b851b5a` and a frozen
snapshot of current NLP against original ASR and every completed candidate ASR
configuration. It also runs both NLP versions on controlled script input as a
**separate diagnostic, not another ASR configuration and not gold**.

## Run and safely resume

```sh
.venv/bin/python tools/evaluate_semantic_voice.py \
  --references "$CORPUS/evaluaciones/semantic-120-v1/references-v2" \
  --original-asr audit/real-voice-120/evaluaciones/audit-120/baseline-routing-v2/cases \
  --candidate-asr "$CORPUS/evaluaciones/semantic-120-v1/asr-experiments" \
  --values "$CORPUS/evaluaciones/audit-120/catalog-fixture.json" \
  --output "$CORPUS/evaluaciones/semantic-120-v1/comparison-NEW"
```

Use the same command with `--resume` to include newly completed ASR configurations.
A configuration must contain all120 original IDs, no execution errors and nonempty
transcripts. Incomplete/error configurations remain explicitly pending; no partial
configuration is compared against the full baseline denominator.

Resume rejects changed source, reference, helper, evaluator, dependency, fixture
or experiment identities, and changed already-evaluated case hashes. After a code
change, use a **new output suffix**; never overwrite an earlier comparison. CLI
failures retain existing evidence. A partially written/invalid artifact fails
closed rather than being silently accepted or replaced.

The baseline is a read-only `git archive` into a fresh system-temp directory;
current `src/` is copied into another snapshot there. Each version runs in a
separate Python subprocess with that snapshot's import path and the existing
virtualenv dependencies. No checkout, install, Git mutation, network or database
operation occurs. `scratch-paths.json` records exact directories for the parent
to remove after verification. The evaluator deliberately does not delete them.
Source hashes, package versions, Python/dependencies and input hashes are retained.
These are source-snapshot comparisons, **not evidence of installed-wheel usage**.

## Outputs

| Artifact | Evidence |
| --- | --- |
| `identity.json`, `source-versions.json`, `scratch-paths.json` | Exact code/data/config binding and isolation paths |
| `cases/<cell>/<id>.json` | Full raw NLP JSON, transcript, independent field matches, evidence indices, normalization transformations |
| `summary.json` | Cell/category/field numerators and denominators, abstentions, wrong-value mismatches, no-proposal and execution errors |
| `comparison.md` | Four-cell tables for completed candidates plus separate script-control diagnostic |
| `recoveries-regressions.json` | Baseline→current NLP changes with ASR held fixed |
| `asr-recoveries-regressions.json` | Original→candidate ASR changes with NLP held fixed |
| `root-cause-isolation.json` | Per-field script-control evidence and explicitly uncertain hypotheses |

All output is local-only commercial development evidence. Do not publish raw
source descriptions, transcripts or paths without the separate sanitization step.

## What the denominator proves

Only `eligible_script_denominator` literal/scalar proposals from independent
references enter scoring. Repeated identical field/value/unit/axis mentions are
deduplicated **within a case**, so one extracted scalar cannot earn several hits
for repeated wording. Metric units convert deterministically to millimeters and
axis aliases normalize `altura`→`alto`; axes are never inferred.

This is scalar/literal-presence recall, not whole-form correctness. Component
association, acoustic truth and independent-generalization denominators remain
**zero**. Pending names, decoded models, residual clauses and unsupported reference
proposals are not promoted into gold. An unresolved association is never validated
merely because its scalar matches. Accessory counts are retained in predictions
but excluded from headline recall because their relations remain unverified.

Price amount is scored separately from its qualifiers. Per-case
`qualifier_results` retain explicit currency/modality match, mismatch or
`NOT_REPRESENTED_OR_ABSTAINED`; a correct amount does not certify either qualifier.
Catalog contracts that do not represent these qualifiers cannot establish them.
`UNSPECIFIED` reference modality does not imply unit price. Headline recall does
not combine qualifier outcomes with amount correctness.

Prediction adapters read structured proposals or accepted extraction evidence,
not free-form `observaciones` text. Catalog IDs are resolved using the controlled
fixture. No corpus ID has an extraction exception. Unmatched structured predictions
are `UNVERIFIED_EXTRA_CANDIDATE_REFERENCE_INCOMPLETE`, **not confirmed false
positives**. Confirmed false-positive counts and precision therefore remain null.
A missing field is an abstention; a present field with a different scalar is a
mismatch. Both remain visible alongside no-proposal cases and execution failures.

## Strict normalization is a separate diagnostic

Original WER uses the existing punctuation/case tokenization without changing
numbers. Strict-normalized WER permits only independently tested cardinal/numeric
format equivalents with explicit unit/price or opening-quantity context, plus
literal metric-unit and currency words. Every transformation records exact original
start/end/raw text, replacement and reason. Spelled model/code clauses are opaque;
invalid coordinated numerals, uncertain reconstructions and compound-unit guesses
are not repaired. This intentionally leaves difficult equivalences unmatched.

Neither metric is human-verified speech accuracy. A lower normalized WER alone
never justifies an ASR change; inspect field recoveries/regressions, no-proposal
counts, operating costs and unresolved listening evidence together.

## Interpret isolation without overclaiming

- Script succeeds, ASR text fails: a **text-channel discrepancy hypothesis**,
  pending listening/reference/normalization review; not confirmed ASR error.
- Both miss: NLP support or reference ambiguity remains unresolved.
- ASR text succeeds but script misses: surface sensitivity needs review.
- Both match: only the scored scalar is corroborated; association and acoustics
  remain unverified.

All120 recordings are development data. Preserve the connected-family exclusions
and independent-audio protocol from `references-v2`; no holdout/generalization
metric is fabricated.

## Focused checks

```sh
.venv/bin/python -m pytest -q tests/evaluation/test_semantic_voice.py
.venv/bin/ruff check tools/evaluate_semantic_voice.py tests/evaluation/test_semantic_voice.py
.venv/bin/ruff format --check tools/evaluate_semantic_voice.py tests/evaluation/test_semantic_voice.py
```

## Evaluation adapter correction

The first two local comparison runs are historical, not final metrics. Parent review found that furniture color objects were compared as whole dictionaries and floor numeric contract columns were not mapped. Two additional tests reproduced these adapter defects before correction. Final runs read the color value, millimetre thickness/width/length columns and structured chair features. This correction is applied identically to both NLP versions; it is not a production ASR/NLP improvement.

Reports retain two denominators: full verified script-scalar coverage and category-contract-supported field-family coverage. Unsupported OTRO configurator fields stay visible in the exhaustive case rows but are excluded from the latter denominator. Category support does not prove every feature subtype is supported or that a missing catalog fixture record is an NLP bug. Associations and acoustic truth remain unscored. Never interpret unmatched predictions as confirmed false positives when annotations are incomplete.
