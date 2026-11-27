# Final Lote02 regression correction

The bounded correction restores the malformed-compound, axis, component, count,
material-scope and catalog-observation guards. The permitted suite currently has
**1361 passes and two oral-thickness failures before the scoped refinement**.
The authorized same-block refinement now passes all **17 scoped checks**; a final
full suite against the frozen sources remains the parent's responsibility.

## What changed

| Area | Root cause and correction |
| --- | --- |
| Magnitudes | Monetary atoms swallowed chain separators and following conjunctions. Dimensional tokens recognize complete tens, compact chains and separate counts; scalar interpretation still reuses the monetary parser. Compound validation rejects leading-zero remainders, metre agreement errors, decimal metre compounds and unsupported-inch suffixes. |
| Axes | Compound measurements bypassed the existing postfix-axis filter. Complete compounds now pass through that same filter, preventing a preceding axis from consuming the next axis's value. |
| Thickness | Missing `tapa`, material/color modifiers and correction continuations lost explicit board gauges. Those cues now preserve the complete literal measurements and correction evidence, without interpreting all millimetres as thickness. Bare unowned oral gauges remain pending evidence. |
| Composition | The `credencia` alias lacked an introduction guard; internal `papeleros` followed by `archivador` was mistaken for an independent order. Existing owner frames now constrain both cases. |
| Inference | Conflicting explicit units no longer fall back to profile inference for an interior omission. Valid proposals retain `UNRESOLVED`, `unit_inferred` metadata and unresolved evidence references. |
| Catalog | Generic `Descripción:` incorrectly populated observations. Only the supported zócalo technical-description flow keeps that fallback. |

## Deliberately superseded expectations

- **S3 fractions:** the former negative `un metro y medio de ancho` case is now
  a positive complete-span 1500 mm test; other negative cases remain unchanged.
- **S4 inferred units:** same-owner omitted units and unambiguous profile-based
  proposals can carry normalized units, but tests now require unresolved candidate
  status, `unit_inferred: true`, the proposed unit and an unresolved evidence link.
  Tests for crossing component owners and contradictory units remain unchanged.
- **S3 millimetres:** `1400 mm x 700 mm` explicitly describes a furniture chain,
  not two thicknesses. Its replacement asserts both axis-pending dimensions,
  original units and zero thicknesses, retaining the non-overlap invariant.
  The parent explicitly confirmed this interpretation.

No malformed-compound, quantity, price, material-owner or independent-product
expectation was weakened to obtain passing results.

## Verification

Evidence directory: `10_reproducibilidad/` in the implementation evidence bundle.
Valid pytest evidence uses the existing original-workspace interpreter,
`python -B -m pytest`, with candidate `PYTHONPATH` and an external in-process source-binding test.
That test checks every loaded `homex_nlp` module resolves inside the selected source
root. No candidate virtual environment, install, model inference or live data was used.

| Evidence | Observed result |
| --- | --- |
| `nlp_suite_run.log` | Prior candidate: 1316 passed, 36 failed. All actual failure traces were inspected. |
| `regression_closure_red_base.log` | New independent tests against an immutable HEAD source copy: 10 failed, 1 binding check passed. |
| `regression_closure_focused.log` | Corrected independent probes: 11 passed, including binding check. |
| `regression_closure_implicated.log` | All implicated modules: 378 passed, including binding check. |
| `regression_closure_suite.log` | Unit, contract (excluding backend consumer), training and operations: 1361 passed, 2 failed. Evaluation excluded. |
| `regression_closure_substrate_red.log` | Two owner-pending substrate probes: 2 failed, binding check passed, before the scoped refinement. |
| `regression_closure_scoped_recheck.log` | Authorized same-block recheck: 17 passed (two residuals, two bare/unowned legacy cases, twelve independent cases, binding check). |
| `regression_closure_lint.log` | Ruff check passed; all 12 changed Python files formatted. |
| `regression_closure_schema.log` | Existing schemas match; source binding verified. |

The first new-test run accidentally omitted required `currency_context`, so its
failures were invalid RED evidence. After correcting the test fixture, genuine
behavioral failures were reproduced against a HEAD source snapshot outside the
worktree. This genuine RED replay occurred after the initial source edits; do not
claim a strictly chronological RED-before-source-edit sequence for those new probes.
The pre-existing 36 failures were observed before the correction.

## Scoped refinement and remaining proof

Two tests in `tests/unit/test_final_unit_scope.py` expect oral thicknesses in
`melamina de dieciocho y treinta y seis milímetros` and `melamina de treinta y seis
milímetros` to remain structured even without a piece owner. The restored pending
rule also removes them, unlike the bare `melamina dieciocho milímetros` legacy case.
The parent authorized one narrow same-block refinement distinguishing explicit
substrate-plus-`de` from a bare oral gauge. Its measurements stay structured with
`component_ref: null`, while their candidates are `UNRESOLVED` with an unresolved
evidence link: no arbitrary parent owner is assigned. Tapacanto/accessory and bare
oral gauges remain pending. The 17 scoped checks pass after normalization; schemas
and lint also pass. No second full sweep was run. The parent must run the final
full suite against these frozen source bytes before claiming closure.

Risk: item 3 (shared dimensional grammar and commercial evidence projection).
