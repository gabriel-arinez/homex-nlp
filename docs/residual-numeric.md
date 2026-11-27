# Reviewable numeric evidence

Implicit dimension units now pass the same contextual scale check, including
same-owner, single-unit neighbors. Product/component profiles and named-axis
bounds are suggestion filters, never restrictions on explicit custom sizes.
Unusual explicit values remain literal and receive a review warning. A 600-wide
furniture measurement can mean 600 mm or 600 cm; absent decisive local evidence,
it stays unitless rather than inheriting metres.

## Gauge boundaries

Material constructions such as `melamina de 18`, `MDF de 15`, `vidrio templado de
6`, and `mesón engrosado a 25` license reviewable millimetre suggestions in the
ordinary gauge range. Models, prices, quantities and named lengths do not.
A plain `espesor de 18` without material/piece context stays unitless. Role and
owner remain review requirements; an edge-band gauge never borrows a board owner.
Standalone technical fragments preserve candidates without creating a commercial
furniture identity or proposal. The existing contract cannot directly attach a
measurement to an accessory; its candidate explicitly identifies the accessory
role while the measurement owner remains unresolved.

## Evidence invariants

Whole-chain candidates retain all operands, independent of each scalar candidate's
unit suggestion. Raw text, offsets, individual references and unestablished axes
are preserved. No contract or schema field was added.

## Superseded assertions

The old `mesón engrosado a 28` unitless assertion in
`test_final_semantic_closure.py` contradicted the requested contextual gauge rule.
It now checks inferred 28 mm and UNRESOLVED evidence while retaining the unrelated
unclassified 16 mm evidence and rejecting fabricated substrate identity.
The component-isolation test now also checks that inferred credenza depth 55 is
550 mm, not 55 metres; isolation alone is not dimensional correctness.
