# Reviewable units in mixed-unit dimensional enumerations

An omitted dimensional unit can use earlier same-owner, same-magnitude context before a furniture profile. The result remains an **inferred proposal requiring review**, never explicit speech or an automatically approved backend value.

## Local evidence

The previous enumeration rule required every nearby explicit dimension to share one unit. This incorrectly rejected a width in centimetres followed by an omitted depth and an explicitly metre-valued height. Thicknesses were already excluded; the conflicting donor was the other furniture axis.

For mixed-unit enumerations, the additional contextual cue requires:

- The existing uninterrupted enumeration and exact component owner boundary.
- Named, distinct axes; no invented axis or same-axis conflicting donor.
- Comparable original numeric scales: the larger raw value is less than ten times the smaller. This pairwise relation is a conservative local cue, not an absolute furniture-size limit or a unit-specific global number threshold.
- One agreeing unit among **all** comparable donors, including at least one explicitly preceding donor. Same-scale unit disagreements and following-only evidence remain pending.

For example, `85 centímetros de ancho, 48 de profundidad y dos metros de alto` supports a reviewable `48 cm` depth: 85 and 48 are comparable raw values, whereas 2 is in another scale. Conversely, `95 cm de ancho y 90 mm de alto y 55 de profundidad` remains pending because comparable donors disagree.

## Preserved boundaries

Explicit units are unchanged, including atypical values. Board thicknesses, accessories and other component owners cannot donate dimensional units. Ambiguous countertop ownership is not resolved by this rule. No source identifiers, reference scripts, product-specific thresholds or new contract fields are used.

The original candidate text/offsets/value remain intact. The proposal carries donor evidence, normalized millimetres, `unit_inferred: true`, `UNRESOLVED`, an unresolved candidate ID and the existing `MISSING_UNIT` review warning. Existing consumers must keep inferred dimensions reviewable rather than populate confirmed commercial fields.

## Verification

`tests/unit/test_final_lote02_verifier.py` adds independent mixed-unit examples, conflicting-unit/owner boundaries and explicit-unit preservation. Existing tests remain unchanged. Frozen ASR and script requests are separate external probes, not committed test fixtures or hidden processing inputs.
