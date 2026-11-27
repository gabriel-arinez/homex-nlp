# Source-preserving magnitudes and reviewable units

The scalar grammar reuses the monetary cardinal parser. Complete compound lengths, chain operands and monetary amounts retain the original source spans; raw transcripts are never normalized in place.

## Behavior

| Input | Proposal |
| --- | --- |
| `dos metros con treinta centímetros de largo` | 230 cm, explicit long axis, full source span |
| `un metro veinte`, `un metro y medio`, `medio metro`, `dos metros y cuarto` | 120, 150, 50 and 225 cm respectively |
| `mesa de dos por tres` | 2 m and 3 m; inferred units, axes pending |
| `mesa de cincuenta y cinco por cincuenta y cinco` | 55 cm and 55 cm; inferred units, axes pending |
| `90 centímetros de ancho, 43 de profundidad y 70 de alto` | Local cm proposals for the omitted units; explicit axes preserved |
| `precio de 13 mil 200` | Complete 13200 amount; commercial mode pending |
| `por dos mil bolivianos en total` | Explicit total of 2000 |
| `rieles de 450 mm` | Not a board thickness |
| `espesor de 1,8 cm` | 18 mm thickness; owner may still need review |

## Evidence and inference

Precedence is explicit units, declared shared enumeration, local same-owner dimensional enumeration, configurable contextual profile, then abstention. The profiles in `src/homex_nlp/resources/dimensional_profiles.json` enumerate plausible m/cm/mm interpretations for furniture and technical contexts. They only propose units when exactly one interpretation fits; they never reject explicit atypical values. For example, `300 por 300` remains ambiguous.

Inferred unit candidates remain `UNRESOLVED`, carry a reason and normalized value including `unit_inferred: true`, and appear in the proposal's unresolved list. Missing-axis and inferred-unit review warnings remain visible. Inference does not assign axes or replace an explicit unit. Source values, original text and evidence IDs are retained. No model or new dependency is used.

An explicit commercial quantity of one makes total and unit prices arithmetically equivalent, but does not establish which mode was spoken. The existing strict price origins cannot represent this inference honestly: the amount remains an unresolved monetary candidate with an inference reason instead of manufacturing an `EXPLICIT_UNIT` price. Quantities above one retain the full amount and require mode confirmation.

Thickness requires an explicit thickness marker or nearby board/structural substrate, not merely millimeters. Unitless explicit thickness stays pending. Word and digit thicknesses both remain structured even when their owner is unknown; the existing missing-owner warning requests confirmation.

## Verification

- New public-engine tests: `tests/unit/test_final_magnitudes.py`, `tests/unit/test_final_money.py`.
- Initial meaningful RED: 18 failed, 5 passed before implementation; initial missing-currency test setup was corrected before recording that result.
- Final focused and related regression check: 305 passed.
- Scoped Ruff check: passed after source normalization.
- Eight shared-parser baseline/candidate probes: explicit axes, board thickness, explicit unit price and invalid oral compound unchanged. Only requested rail/thickness disambiguation, full compound length, complete ambiguous amount and postposed total changed.
- Baseline probe source: `a73c462`; scratch evidence remains outside the worktree under `Descargas/HOMEX_NLP_Implementacion_Final_Lote02/scratch/numeric-*`.

Broader suites, frozen transcription comparison, backend/frontend review propagation and wheel-resource verification are parent integration work. No ASR or historical corpus evaluation was run.
