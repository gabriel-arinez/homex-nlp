# Drawer recognition and dimensional ownership

Singular `cajón`, unaccented `cajon`, plural `cajones`, and `gaveta(s)` use the existing component association pipeline. Drawer counts remain internal counts, never commercial furniture quantities. No contract, dependency, model, or dimensional plausibility policy changes are required.

## Ownership example

`un escritorio de melamina de ciento veinte centímetros de largo y sesenta de ancho con un cajón de cuarenta centímetros de ancho y veinte centímetros de alto`

The desk retains one commercial unit, 120 cm length, and 60 cm width. One drawer component owns the 40 cm width and 20 cm height. The drawer does not also appear as an independent accessory.

## Boundaries preserved

- Explicit exclusions and corrections use the existing evidence decisions.
- Repeated identical drawer descriptions share an owner; explicit other drawers remain separate.
- Drawers in a gavetero definition do not steal the furniture envelope dimensions.
- Independent furniture orders still abstain rather than being merged into a component.
- Existing numeric, monetary, thickness, and unit plausibility policies remain unchanged.

## Verification

`tests/unit/test_surgical_drawer_scope.py` exercises the public `RulesEngine`, literal evidence spans, singular/plural and accent variants, commercial/internal counts, exclusions, corrections, repeated descriptions, lateral qualifiers, independent orders, and existing dimensional ownership rules. Baseline and candidate checks must bind imports explicitly to their respective source trees in the same pytest process.

Frozen corpus evaluation, release distribution, consumer CI, and production deployment are separate closure steps; these unit tests do not establish those outcomes.
