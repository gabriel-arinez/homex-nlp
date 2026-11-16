# Abstain when speech has no commercial meaning

Catalog fallback names no longer turn greetings, testing phrases or numeric chatter into product proposals. A recognized product, descriptive commercial detail, or an explicit name declaration provides evidence; digits alone do not.

Valid brief descriptions such as `silla plegable` remain eligible. Unknown names can be declared explicitly, for example `nombre: Credenza Nórdica`, so extraction is not limited to a fixed product vocabulary. Insufficient text remains in the unrecognized evidence with a comprehensible warning rather than an invented product.

Custom furniture extraction also abstains on a bare `mueble` or `un mueble`. Dimensions, materials or actual component descriptions retain their existing valid interpretations. All evidence refers to original input spans.

The changes ship as local corrective package 0.1.27 for the companion backend feature branch. No public release or publication is implied. Tests cover accepted descriptions, explicit new names, chatter, numeric noise, generic furniture and existing extraction regressions.


## Corrective audit

Bare generic descriptions followed only by attribute markers (for example `un mueble precio`, `mueble color` and `probando marca`) do not count as extracted commercial values. `hola producto` also abstains rather than treating a generic product marker as identity. Positive short catalog descriptions and properly introduced novel names remain covered. The full source and installed-artifact NLP suites each pass 1,137 tests; no missing quantity, price or measurement is invented to complete a proposal. Previous package artifacts remain byte-identical.
