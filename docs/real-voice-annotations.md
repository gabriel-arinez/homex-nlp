# Review the 120 commercial reference proposals

`tools/annotate_real_voice.py` creates a local-only annotation workspace from the
original documents, pre-recording scripts and frozen ASR. It never imports the
production extractor. **These are proposals, not complete acoustic gold labels.**

## Generate a new workspace

```sh
.venv/bin/python tools/annotate_real_voice.py \
  --corpus /path/to/HOMEX_Guiones_Evaluacion_Voz \
  --baseline audit/real-voice-120/evaluaciones/audit-120/baseline-routing-v2/cases \
  --output /path/to/NEW/references
```

The output directory must not exist. Do not place it in Git: it contains real
voice clips and source commercial descriptions. Generation reads originals,
verifies all 240 audio hashes against the frozen archive, copies PCM frame ranges
without resampling or normalization, and checks original hashes again afterwards.
Manifest IDs, current commercial categories and exact source strings are retained.
The original source-text hash is retained separately from computed text hashes.

## Read the outputs

| File | Purpose |
| --- | --- |
| `cases.jsonl`, `cases/<id>.json` | Evaluator-ready per-case field proposals |
| `summary.json` | Counts, denominators and explicit limitations |
| `audio-preservation.json` | 240 before/after SHA-256 pairs |
| `audio-review.html` | Local playback of timestamped segments and full WAV links |
| `audio-review-index.json` | Machine-readable playback timestamps and ASR text |
| `clips/` | Local-only unmodified PCM segment copies, padded by 0.4 seconds |
| `holdout-protocol.json` | Connected development groups and independent-audio protocol |

Review every case's `script_fields` and `document_fields` independently. Each array
contains all fourteen field types, including explicit null placeholders when the
bounded parser cannot support a proposal. Several entries per field are expected.
Each field carries:

- `value`, `unit`, `axis`, `currency`, `modality`: proposed normalized scalars or
  literal text; null means unavailable, not zero. Only explicit currency becomes
  `BOB`; undocumented currency remains null. `UNSPECIFIED` price modality never
  means unit price. Accessory/component `count_proposal`, `count_unit`, and
  `count_status` are separate from the accessory's literal identity.
- `evidence`: source identifier, exact Unicode character `start`/`end` (half-open)
  and `raw`. The invariant is `source_text[start:end] == raw`. These are not byte
  offsets and not audio timestamps.
- `document_presence`, `script_presence`, `asr_status`, `asr_evidence`: separate
  evidence channels. No exact match means **not corroborated literally**, not
  contradicted: number words and ASR digits intentionally do not match. Document
  presence is literal only; semantic correspondence still needs review.
- `association`: whether a value belongs to a particular component. Unresolved
  association stays unresolved even when the literal scalar is verified.
- `verification_status`, `verification_scope`, `ambiguity`, and denominator flags:
  the scope of proof, not a confidence score.

Every original script/document clause also appears in `technical_description`.
Concatenating those residual evidence strings reconstructs the original text.
Residuals preserve complex measurements, inherited units, hidden source codes,
technical details and commercial qualifications without silently discarding them.
They remain pending until a reviewer resolves their structured interpretation.

## Denominators are deliberately separate

`eligible_script_denominator` verifies **only literal or scalar textual content**:
explicit quantity, price amount/modality, unit, brand, material/accessory/color
mentions, clear explicit-axis measures and simple thicknesses. It does not prove
component association, completeness of the opening product name, or speech.
Do not score component relations with this denominator. Restrict evaluation to the
field's verified scope; literal accessory presence does not establish its count
or which component carries it. Count evidence can be literal while association
remains pending. Compound measures, unspecified axes and model decoding remain
pending. In particular, a final scalar inside a `por` chain is not verified as a
standalone thickness.

`eligible_acoustic_denominator` is always false. Every case and field has
`PENDING_HUMAN_LISTENING`; automatic ASR corroboration never changes that state.
Document proposals are never included in the spoken/script denominator, including
values whose wording also appears in the script. Use the independently generated
script proposal instead. `NOT_STATED` is reserved for an absent explicit price
statement; other no-match results are `UNSUPPORTED_OR_UNPARSED_NOT_CONFIRMED_ABSENT`.
A parser miss must not count as proof that the speaker omitted a field.

## Human review and holdout

1. Open the local playback index and per-case proposals. Listen to full replay
   when a segment is unclear or ASR omitted speech; segment boundaries/text are
   automatic and are **not** script-to-audio forced alignment.
2. Check each commercial value, component association and residual clause. Record
   corrected values, actual acoustic evidence and reviewer identity in a new,
   separately versioned review artifact; do not modify originals or frozen results.
3. Resolve disagreements using a second listener before creating acoustic gold.

All 120 cases are development data. Family, shared source-record, identical
source-hash and identical normalized source-title links form transitive leakage
groups. These are minimum exclusions, not a claim that different groups are
independent. The protocol requires new speakers/devices/environments and families,
freeze-before-test, dual annotation, complete denominators and no post-holdout
tuning. Until that audio exists, generalization metrics remain null.

## Checks

```sh
.venv/bin/python -m pytest -q tests/evaluation/test_reference_annotations.py
.venv/bin/ruff check tools/annotate_real_voice.py tests/evaluation/test_reference_annotations.py
.venv/bin/ruff format --check tools/annotate_real_voice.py tests/evaluation/test_reference_annotations.py
```

Tests use independent synthetic language, not corpus IDs or production predictions.
The CLI is a new offline tool; no existing production command is changed.

### Coordinated and compound numbers

The independent numeric helper accepts bounded Spanish cardinal grammar, not a
sum of every recognized number word. Multiple coordinated values such as
`setenta y cinco y sesenta` abstain. Partially matched unit chains and `por`
chains also propose null, with their full clauses retained for review; they never
propose the final scalar as though it represented the entire measurement.
A bounded compound with an explicit axis, such as `dos metros diez de alto`,
normalizes to `210 cm`. That verifies only the measure/axis text, not its component
association. `un metro treinta y un metro sesenta` remains pending rather than
fabricating a 41-metre measurement.
